#!/usr/bin/env python3
"""
Proof-of-concept script to download VRT MAX videos using yt-dlp directly.
This is a simple wrapper that:
- Reads credentials from environment or .env (optional)
- Falls back to default credentials if none are provided
- Accepts one or more URLs as command-line arguments
- Optionally reads URLs from a file (--file)
- Supports a dry-run flag (--dry-run)
- Supports season URL expansion with optional --max-episodes limit
- Works on both Linux and Windows
"""

import sys
import os
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import signal
import time

# GraphQL query for paginated tile list (cursor-based pagination)
_LIST_QUERY = """
query PaginatedTileListPage($listId: ID!, $after: ID) {
  list(listId: $listId) {
    ... on PaginatedTileList {
      paginatedItems(first: 50, after: $after) {
        edges {
          node {
            __typename
            ... on EpisodeTile {
              title
              action {
                ... on LinkAction { link }
              }
            }
            ... on PodcastEpisodeTile {
              title
              action {
                ... on LinkAction { link }
              }
            }
          }
        }
        pageInfo { endCursor hasNextPage }
      }
    }
    ... on StaticTileList {
      items {
        __typename
        ... on EpisodeTile {
          title
          action {
            ... on LinkAction { link }
          }
        }
      }
    }
  }
}
"""

def _execute_graphql_query(query: str, variables: dict | None = None) -> dict | None:
    """Execute a GraphQL query against the VRT MAX API and return the JSON response.
    Returns None on failure."""
    data = {"query": query}
    if variables:
        data["variables"] = variables
    data_bytes = json.dumps(data).encode('utf-8')
    url = "https://www.vrt.be/vrtnu-api/graphql/v1"
    req = urllib.request.Request(url, data=data_bytes, headers={
        'Content-Type': 'application/json',
        'x-vrt-client-name': 'WEB',
    })

    var_hint = ""
    if variables and "pageId" in variables:
        var_hint = f" pageId={variables['pageId']}"
    elif variables and "listId" in variables:
        after = variables.get("after")
        var_hint = f" listId={variables['listId']}" + (f" after={after}" if after else "")

    try:
        logger.debug(f"GraphQL POST{var_hint} ...")
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                logger.debug(f"GraphQL returned status {response.status}")
                return None
            body = json.loads(response.read().decode())
            logger.debug(f"GraphQL response OK{var_hint}")
            return body
    except Exception as e:
        logger.debug(f"GraphQL error{var_hint}: {type(e).__name__}: {e}")
        return None
# Ensure project root, src, and src/thuis are on sys.path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'thuis'))
import shutil
import subprocess
import tempfile
import platform
import logging
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present
except Exception:
    pass  # dotenv optional

# Import scene naming pipeline modules
try:
    # When used as part of a package
    from . import url_parser, classifier, metadata_fetcher, scene_namer, transcoder
except ImportError:
    # When run directly
    import url_parser
    import classifier
    import metadata_fetcher
    import scene_namer
    import transcoder

# Import DRM decrypt worker
try:
    from . import drm_decrypt
except ImportError:
    import drm_decrypt

# Import watchlist database for download tracking
try:
    from . import watchlist
except ImportError:
    import watchlist

# Default credentials (for demonstration / testing only)
DEFAULT_EMAIL = "kuxelu@ipdeer.com"
DEFAULT_PASSWORD = "Els123456"

# Module-level logger for debug messages (GraphQL, etc.)
# This is configured by setup_logging() when the app starts
logger = logging.getLogger('thuis')

# Default output directory (can be overridden via OUTPUT_DIR env var / .env)
DEFAULT_OUTPUT_DIR = os.getenv("OUTPUT_DIR", "media")

# Valid video resolutions for --profile validation
VALIDATIONS = [720, 1080, 1440, 2160]


def normalize_resolution(res: int | str) -> str:
    """Normalize a resolution value to a string ending with 'p'.

    Accepts int (1080), str int ("1080"), or str with 'p' ("1080p")
    and returns the canonical form (e.g. ``"1080p"``).

    Args:
        res: Resolution value as int or str.

    Returns:
        Canonical resolution string ending with 'p'.
    """
    res_str = str(res).lower().rstrip("p")
    return f"{res_str}p"


def canonical_slug(title: str) -> str:
    """Convert a show title to the VRT MAX canonical slug.
    Rules:
    - Lower‑case all characters.
    - Replace '&' with '-and-'.
    - Replace any other character that is not alphanumeric with a hyphen.
    - Collapse leading/trailing hyphens.
    """
    s = title.lower()
    s = s.replace("&", "-and-")
    s = re.sub(r"[^a-z0-9]", "-", s)
    s = s.strip("-")
    return s


def _is_not_found(status: int, body_preview: str) -> bool:
    """Return True if the response indicates the episode is not found (HTTP >=400 or soft-stop string)."""
    if status >= 400:
        return True
    if "Deze pagina lijkt verloren" in body_preview:
        return True
    if "The specified key does not exist" in body_preview:
        return True
    return False


def _guess_episode_urls(show_slug: str, season: int, max_episodes: int | None = None) -> list[str]:
    """Try to discover episode URLs by HEAD-requesting candidate patterns.
    Stops at the first 404/soft-stop per episode (avoids duplicates).
    Returns list of valid episode URLs."""
    import urllib.error
    
    episodes = []
    episode = 1
    max_episodes_hard = max_episodes if max_episodes is not None else 500  # Hard safety limit

    logger.debug("HEAD probing: %s season %s, max %s episodes", show_slug, season, max_episodes_hard)

    while True:
        if len(episodes) >= max_episodes_hard:
            logger.debug("Hit max episode limit (%s), stopping HEAD probing", max_episodes_hard)
            break

        found_any = False
        # Try VRT MAX's actual URL patterns:
        # Pattern 1: /a-z/<show>/<season>/<show>-s<season>a<episode>/
        # Pattern 2: /a-z/<show>/<season>/<show>/e<episode>/
        patterns = [
            f"https://www.vrt.be/vrtmax/a-z/{show_slug}/{season}/{show_slug}-s{season}a{episode}/",
            f"https://www.vrt.be/vrtmax/a-z/{show_slug}/{season}/{show_slug}/e{episode}/"
        ]

        for url in patterns:
            try:
                req = urllib.request.Request(url, method="HEAD")
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if not _is_not_found(response.status, ""):
                            logger.debug("HEAD found episode %s: %s (status %s)", episode, url, response.status)
                            episodes.append(url)
                            found_any = True
                            break  # One URL per episode — avoid duplicates
                except urllib.error.HTTPError as e:
                    try:
                        body_preview = e.read(500).decode("utf-8", errors="ignore")
                    except:
                        body_preview = ""
                    if not _is_not_found(e.code, body_preview):
                        logger.debug("HEAD found episode %s via HTTPError %s: %s", episode, e.code, url)
                        episodes.append(url)
                        found_any = True
                        break  # One URL per episode — avoid duplicates
            except Exception as ex:
                if episode <= 3:  # Only log early failures
                    logger.debug("HEAD exception for %s: %s: %s", url, type(ex).__name__, ex)
                continue

        if not found_any:
            logger.debug("No more episodes found after #%s (total: %s)", episode - 1, len(episodes))
            break

        episode += 1

    return episodes


def _get_list_id(show_slug: str, season: int) -> str | None:
    """Query the VRT MAX GraphQL page to find a listId tile whose title
    contains the target season number.  Returns the first matching listId,
    or the first listId found as fallback."""
    query = """
    query($pageId: ID!) {
      page(id: $pageId) {
        ... on IPage {
          components {
            __typename
            ... on PaginatedTileList { listId title }
            ... on StaticTileList { listId title }
            ... on LazyTileList { listId title }
            ... on ContainerNavigation {
              items {
                title
                components {
                  __typename
                  ... on PaginatedTileList { listId title }
                  ... on StaticTileList { listId title }
                  ... on LazyTileList { listId title }
                  ... on ContainerNavigation {
                    items {
                      title
                      components {
                        __typename
                        ... on PaginatedTileList { listId title }
                        ... on StaticTileList { listId title }
                        ... on LazyTileList { listId title }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    variables = {"pageId": f"/vrtmax/a-z/{show_slug}"}
    logger.debug("Fetching list_id for slug=%r season=%s", show_slug, season)
    response_data = _execute_graphql_query(query, variables)
    if not response_data:
        logger.debug("No graphql response for _get_list_id")
        return None

    def _collect_list_ids(node, parent_title=''):
        results = []
        if isinstance(node, list):
            for item in node:
                results.extend(_collect_list_ids(item, parent_title))
        elif isinstance(node, dict):
            typename = node.get('__typename')
            title = node.get('title') or parent_title

            if typename in ('PaginatedTileList', 'StaticTileList', 'LazyTileList') and node.get('listId'):
                results.append((title, node['listId']))

            for k in ['components', 'items']:
                if k in node:
                    results.extend(_collect_list_ids(node[k], title))
        return results

    components = response_data.get("data", {}).get("page", {}).get("components", [])
    candidates = _collect_list_ids(components)

    logger.debug("Found %s list_id candidate(s): %s", len(candidates), [(t[:30], lid[:20]) for t, lid in candidates])

# Filter out non-episode lists (social media, podcasts, bloopers, etc.)
    # Keep only lists that contain "seizoen" or have a numeric title (likely seasons)
    def _is_season_list(title: str) -> bool:
        if not title:
            return False
        title_lower = title.lower()
        if "meest recente" in title_lower or "meest recent" in title_lower:
            return False
        if "podcast" in title_lower:
            return False
        if "social" in title_lower or "volg ons" in title_lower:
            return False
        if "throwback" in title_lower:
            return False
        if "bloopers" in title_lower:
            return False
        if "achter de schermen" in title_lower:
            return False
        if "extra-s" in title_lower or "extra's" in title_lower:
            return False
        # Include lists with season keyword or numeric titles
        if "seizoen" in title_lower or "season" in title_lower:
            return True
        # Assume numeric title means season
        try:
            int(title.strip())
            return True
        except ValueError:
            pass
        return True

    filtered = [(t, lid) for t, lid in candidates if _is_season_list(t)]

    logger.debug("After filtering: %s of %s candidates remain", len(filtered), len(candidates))

    # Match by title containing season number
    season_str = str(season)
    for title, lid in filtered:
        title_norm = title.lower().replace('(', ' ').replace(')', ' ')
        words = title_norm.split()
        if season_str in words or f"seizoen-{season_str}" in title_norm:
            logger.debug("Matched list_id %r by season title %r", lid, title)
            return lid

    # Fallback: return first listId found
    # Use filtered list if non-empty, otherwise fall back to original candidates
    # (handles shows where all lists have empty titles, e.g. FC De Kampioenen)
    fallback = filtered if filtered else candidates
    if fallback:
        logger.debug("No season match, using first list_id: %r", fallback[0][1])
        return fallback[0][1]
    logger.debug("No list_id found at all")
    return None


def get_credentials():
    """Return (email, password) from environment, falling back to defaults."""
    email = os.getenv("VRT_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("VRT_PASSWORD", DEFAULT_PASSWORD)
    return email, password


def get_decrypt_policy() -> str:
    """Return DRM decryption policy from environment.

    Normalizes DECRYPT_DRM env var:
    - yes|1|true (case-insensitive) -> "yes"
    - anything else -> "no"
    Default: "yes" (decrypt DRM by default)
    """
    val = os.getenv("DECRYPT_DRM", "yes").strip().lower()
    if val in ("yes", "1", "true"):
        return "yes"
    return "no"


def _is_drm_content(metadata: dict) -> bool:
    """Check if content is DRM-protected based on yt-dlp metadata.

    Currently checks for common DRM indicators in metadata.
    Can be extended as more DRM detection logic is added.
    """
    # Check for VRT MAX DRM metadata fields (emitted by fork)
    if metadata.get("_vrt_drm_vudrm_token") and metadata.get("_vrt_drm_mpd_url"):
        return True

    # Check for common DRM scheme indicators in vcodec/acodec
    vcodec = (metadata.get("vcodec_raw") or "").lower()
    acodec = (metadata.get("acodec_raw") or "").lower()

    # Common DRM codec indicators
    drm_indicators = [
        "widevine", "playready", "fairplay", "clearkey",
        "cenc", "cbcs", "cbc1", "cens",
    ]

    for indicator in drm_indicators:
        if indicator in vcodec or indicator in acodec:
            return True

    # Check for encrypted extensions (yt-dlp returns ext without dot)
    ext = (metadata.get("ext") or "").lower()
    if ext in ("ism", "ismv", "isma"):  # Smooth Streaming often DRM
        return True

    return False


def get_yt_dlp_cmd():
    """Return the command to invoke yt-dlp, preferring the packaged binary in the project's bin directory.
    If a virtual environment is active, it will always use the venv's python -m yt_dlp.
    """
    # Try to find a bundled binary first
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    binary_name = 'yt-dlp.exe' if platform.system().lower().startswith('win') else 'yt-dlp'
    bundled_path = os.path.join(project_root, 'bin', binary_name)
    if os.path.isfile(bundled_path):
        return [bundled_path]
    # If running inside a virtualenv, prefer python -m yt_dlp
    # (sys.prefix != sys.base_prefix works even when the venv was never activated)
    if hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix:
        return [sys.executable, '-m', 'yt_dlp']
    # Fallback to system yt-dlp if available
    path_ytdlp = shutil.which('yt-dlp')
    if path_ytdlp:
        return [path_ytdlp]
    # Final fallback to module execution
    return [sys.executable, '-m', 'yt_dlp']


def get_yt_dlp_location():
    """Return the directory where yt-dlp is installed."""
    result = subprocess.run(
        [sys.executable, "-c", "import yt_dlp, os, sys; print(os.path.dirname(yt_dlp.__file__))"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def patch_ytdlp_if_needed():
    """No-op: patch is already included in the yt-dlp fork tag v2026.06.09-patch1.
    Kept for backward compatibility; does nothing."""
    pass


def build_yt_dlp_args(urls, dry_run=False, output_dir=Path(DEFAULT_OUTPUT_DIR), output_template=None, email=None, password=None, resolution=None):
    """Build yt-dlp argument list.

    Args:
        urls: List of URLs to download.
        dry_run: If True, add --simulate flag.
        output_dir: Directory to save files.
        output_template: Output filename template.
        email: VRT MAX email.
        password: VRT MAX password.
        resolution: Optional video height (e.g. ``"1080p"``). When set,
            format string becomes ``bestvideo[height<=N]+bestaudio``,
            otherwise defaults to ``bestvideo+bestaudio``.
    """
    args = []
    args.extend(get_yt_dlp_cmd())
    # Common options: best video+audio, merge to mp4, no warnings, no color
    if resolution:
        height_match = re.search(r"\d+", str(resolution))
        height = int(height_match.group()) if height_match else None
        if height:
            fmt = f"bestvideo[height<={height}]+bestaudio"
        else:
            fmt = "bestvideo+bestaudio"
    else:
        fmt = "bestvideo+bestaudio"
    args += [
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--no-color",
    ]
    if dry_run:
        args.append("--simulate")
    # Add output template
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_template is None:
        output_template = "%(title)s.%(ext)s"
    args.extend(["-o", str(output_dir / output_template)])
    # Add credentials
    if email is None or password is None:
        email, password = get_credentials()
    if email and password:
        args.extend(["--username", email, "--password", password])
    # Append URLs
    args.extend(urls)
    return args


def _find_downloaded_file(output_dir: Path, template: str, url: str) -> str | None:
    """Find the actual file created by yt-dlp given a template and URL.

    When template contains %%-placeholders (e.g. %(title)s.%(ext)s),
    scan the output directory for recently modified files and try to
    match them against the template pattern or URL association.

    Returns the discovered filename, or None if no match is found.
    """
    import fnmatch
    if "%" not in template:
        # Concrete filename — just check if it exists
        candidate = output_dir / template
        if candidate.exists():
            return candidate.name
        return None

    # Template with placeholders — find recently created mp4 files
    # and try to match by pattern
    now = time.time()
    candidates: list[tuple[str, float]] = []  # (filename, mtime)
    for f in output_dir.glob("*.mp4"):
        if f.stat().st_mtime > (now - 600):  # Last 10 minutes
            candidates.append((f.name, f.stat().st_mtime))

    if not candidates:
        return None

    # Sort by most recent first
    candidates.sort(key=lambda x: x[1], reverse=True)
    filename, _mtime = candidates[0]

    # Try to match template pattern against filename
    # Convert yt-dlp template to glob pattern
    glob_pattern = template.replace("%(", "{").replace("s)", "*").replace("ext)", "*")
    if fnmatch.fnmatch(filename, glob_pattern):
        return filename

    # Fallback: return most recent file
    logger.debug("Could not match template %r against files in %s; using most recent", template, output_dir)
    return filename


def _run_ytdlp_with_drm_detection(url_args_list: list[str]) -> tuple[int, str]:
    """Run yt-dlp via a PTY so it detects a real terminal and shows an
    in-place progress bar.  Lines read from the PTY have trailing ``\\r``
    stripped and are printed via ``print(..., end="")`` so the terminal
    renders the carriage-return updates as a single updating bar.

    Args:
        url_args_list: Command line arguments for yt-dlp.

    Returns:
        Tuple of (returncode, stderr_text).
    """
    import pty
    import select
    master_fd, slave_fd = pty.openpty()

    proc = subprocess.Popen(
        url_args_list,
        stdout=slave_fd,
        stderr=slave_fd,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )
    os.close(slave_fd)  # Close slave in parent after fork

    stderr_buffer = []
    while True:
        # Use select to avoid blocking forever when process exits
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if ready:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            # Pass raw bytes straight to stdout so the terminal handles
            # carriage returns and ANSI escape sequences for the progress bar
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            # Also decode for DRM detection buffer
            stderr_buffer.append(chunk.decode("utf-8", errors="replace"))
        elif proc.poll() is not None:
            # Process has exited — drain any remaining PTY output
            time.sleep(0.2)
            while True:
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                stderr_buffer.append(chunk.decode("utf-8", errors="replace"))
            break

    proc.wait()
    returncode = proc.returncode
    stderr_text = "".join(stderr_buffer)
    os.close(master_fd)
    return returncode, stderr_text

def is_season_url(url: str) -> bool:
    """Detect if *url* points to a season page rather than a single episode.
    Covers two patterns used by VRT MAX:
    1. Query parameter ``?seizoen=seizoen-<num>``
    2. Path ending with the season number (e.g. ``/.../2``) under /a-z/
    """
    if "seizoen=" in url:
        return True
    # Path ending with a slash‑separated integer (e.g. …/2/ or …/2)
    path = urlparse(url).path.rstrip("/")
    # Check if path ends with a digit and contains /a-z/
    if path.endswith(tuple("0123456789")) and "/a-z/" in path:
        # Extract the last segment (the number)
        last_segment = path.split("/")[-1]
        if last_segment.isdigit():
            return int(last_segment) > 0
    return False

def is_valid_vrt_url(url: str) -> bool:
    """Check if URL has no # fragment (fragments cause processing errors)."""
    return '#' not in url

def is_audio_only_stream(url: str) -> bool:
    """Detect whether a given HLS stream URL points to audio‑only content.

    Fetches the m3u8 manifest and inspects the ``CODECS`` attribute of any
    ``#EXT-X-STREAM-INF`` lines. If a known video codec (e.g. ``avc1``, ``hvc1``,
    ``hev1``, ``av01``, ``vp9``, ``vp8``) appears, the function returns ``False``.
    If only audio codecs like ``mp4a`` or ``aac`` are present, returns ``True``.
    Network errors or missing ``CODECS`` are treated as not audio‑only (conservative).
    """
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as resp:
            text = resp.read().decode(errors="ignore")
    except Exception:
        return False

    for line in text.splitlines():
        if line.startswith("#EXT-X-STREAM-INF"):
            m = re.search(r'CODECS="([^\"]+)"', line)
            if m:
                codecs = m.group(1).lower()
                video_markers = ["avc1", "hvc1", "hev1", "av01", "vp9", "vp8"]
                if any(v in codecs for v in video_markers):
                    return False
                return True
    return False


def is_show_url(url: str) -> bool:
    """Detect if *url* points to a show-level page (not a specific season or episode).

    A show URL under VRT MAX has exactly the path ``/vrtmax/a-z/{show_slug}``
    with no additional path segments and no ``?seizoen=`` query parameter.
    Examples:
        ``https://www.vrt.be/vrtmax/a-z/thuis`` → show URL
        ``https://www.vrt.be/vrtmax/a-z/thuis/1/`` → season URL (not a show URL)
    """
    if not is_valid_vrt_url(url):
        return False
    if is_season_url(url):
        return False
    path = urlparse(url).path.rstrip("/")
    segments = [seg for seg in path.split("/") if seg]
    return len(segments) == 3 and segments[0] == "vrtmax" and segments[1] == "a-z"


def _fetch_episodes_by_list_id(list_id: str, max_episodes: int | None = None) -> list[str]:
    """Fetch episode URLs from a GraphQL ``listId`` using cursor-based pagination.

    Returns a flat list of full VRT MAX episode URLs.
    """
    episodes: list[str] = []
    after: str | None = None
    max_pages = 100
    page_count = 0

    while page_count < max_pages:
        page_count += 1
        variables: dict = {"listId": list_id}
        if after:
            variables["after"] = after

        logger.debug(f"GraphQL page {page_count} (episodes so far: {len(episodes)})")
        response = _execute_graphql_query(_LIST_QUERY, variables)
        if not response or 'data' not in response:
            logger.debug("GraphQL returned no data, stopping pagination")
            break

        list_data = response['data'].get('list', {})
        if not list_data:
            logger.debug("GraphQL list_data is empty, stopping pagination")
            break

        # Handle both StaticTileList and PaginatedTileList
        items: list[dict] = []
        page_info: dict | None = None

        if 'paginatedItems' in list_data:
            paginated = list_data['paginatedItems']
            edges = paginated.get('edges', [])
            for e in edges:
                node = e.get('node', {})
                items.append(node)
            page_info = paginated.get('pageInfo', {})
        elif 'items' in list_data:
            items = list_data['items']

        logger.debug(f"Page {page_count} has {len(items)} items")

        for node in items:
            action = node.get('action', {})
            link = action.get('link') if action else None
            if link:
                full_url = f"https://www.vrt.be{link}"
                if not is_valid_vrt_url(full_url):
                    continue
                episodes.append(full_url)
                if max_episodes is not None and len(episodes) >= max_episodes:
                    break

        if max_episodes is not None and len(episodes) >= max_episodes:
            break

        # Check pagination
        if page_info:
            has_next = page_info.get('hasNextPage', False)
            end_cursor = page_info.get('endCursor')
            if has_next:
                if end_cursor:
                    after = end_cursor
                    logger.debug(f"Paginating: after={after!r}")
                else:
                    logger.debug("hasNextPage=True but endCursor is missing/empty — stopping to avoid infinite loop")
                    break
            else:
                logger.debug("No more pages (hasNextPage=False)")
                break
        else:
            # StaticTileList — no more pages
            logger.debug("StaticTileList (no page_info), stopping")
            break

    if page_count >= max_pages:
        logger.debug("Reached max pages (%s), stopping pagination", max_pages)

    return episodes


def fetch_season_episodes(url: str, max_episodes: int | None = None) -> list[str]:
    """Extract show slug and season number from URL, then query the VRT MAX
    GraphQL API to collect episode URLs for that season.
    Falls back to HEAD-guessing when the API yields no results."""
    from urllib.parse import urlparse, parse_qs

    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        query = parsed.query

        slug = None
        season = None

        if 'seizoen=' in query:
            query_params = parse_qs(query)
            season_vals = query_params.get('seizoen')
            if season_vals:
                season_val = season_vals[0]
                if season_val.startswith('seizoen-'):
                    try:
                        season = int(season_val.split('-')[1])
                    except ValueError:
                        pass
            path_segments = [seg for seg in path.split('/') if seg]
            if path_segments:
                slug = path_segments[-1]
        else:
            path_segments = [seg for seg in path.split('/') if seg]
            if len(path_segments) >= 4 and path_segments[0] == 'vrtmax' and path_segments[1] == 'a-z':
                slug = path_segments[2]
                try:
                    season = int(path_segments[3])
                except ValueError:
                    pass

        if not slug or season is None:
            logger.debug("Could not extract slug/season from URL")
            return []

        logger.debug(f"Extracted slug={slug!r} season={season}")

        list_id = _get_list_id(slug, season)
        if not list_id:
            logger.debug("No list_id found, falling back to HEAD probing...")
            return _guess_episode_urls(slug, season, max_episodes)

        logger.debug(f"Found list_id={list_id!r}, fetching episodes via GraphQL...")

        episodes = _fetch_episodes_by_list_id(list_id, max_episodes)

        if not episodes:
            logger.debug("GraphQL returned 0 episodes, falling back to HEAD probing...")
            return _guess_episode_urls(slug, season, max_episodes)

        logger.debug(f"GraphQL returned {len(episodes)} episodes total")
        return episodes
    except Exception as e:
        logger.debug(f"fetch_season_episodes exception: {type(e).__name__}: {e}")
        return []


def _collect_list_ids(node, parent_title=''):
    """Collect (title, listId) pairs from GraphQL page components (recursive)."""
    results = []
    if isinstance(node, list):
        for item in node:
            results.extend(_collect_list_ids(item, parent_title))
    elif isinstance(node, dict):
        typename = node.get('__typename')
        title = node.get('title') or parent_title
        if typename in ('PaginatedTileList', 'StaticTileList', 'LazyTileList') and node.get('listId'):
            results.append((title, node['listId']))
        for k in ['components', 'items']:
            if k in node:
                results.extend(_collect_list_ids(node[k], title))
    return results


def _resolve_podcast_stream_url(episode_url: str) -> tuple[str, str] | None:
    """Resolve a VRT MAX podcast episode page URL to (HLS audio URL, title).

    Uses the GraphQL player data to get the streamId, then the VRT media
    aggregator (same as yt-dlp's VRT extractor) to get the HLS manifest.
    Returns None on failure.
    """
    try:
        import yt_dlp.extractor.vrt as vrt_ext
        import yt_dlp

        page_id = urlparse(episode_url).path.rstrip("/")

        q = ("query($pageId: ID!) { page(id: $pageId) { ... on PodcastEpisodePage "
             "{ title player { modes { streamId } } } } }")
        data = _execute_graphql_query(q, {"pageId": page_id})
        if not data:
            return None
        page = (data.get("data") or {}).get("page") or {}
        title = page.get("title") or "podcast-aflevering"
        modes = (page.get("player") or {}).get("modes") or []
        stream_id = next((m["streamId"] for m in modes if m.get("streamId")), None)
        if not stream_id:
            logger.warning("No streamId found for %s", episode_url)
            return None

        ydl = yt_dlp.YoutubeDL({"quiet": True})
        ie = vrt_ext.VrtNUIE()
        ie.set_downloader(ydl)
        media = ie._call_api(stream_id)
        for target in media.get("targetUrls", []):
            if target.get("type", "").lower() == "hls":
                return target["url"], title
        logger.warning("No HLS targetUrl in media response for %s", episode_url)
        return None
    except Exception as e:
        logger.error("Failed to resolve stream for %s: %s", episode_url, e)
        return None


def _fetch_podcast_episodes(url: str, slug: str, max_episodes: int | None = None) -> list[str]:
    """Expand a podcast show URL into individual episode URLs.

    Uses the same GraphQL page API with pageId ``/vrtmax/podcasts/…`` and
    collects every tile-list entry, then rewrites each tile URL to the
    canonical /vrtmax/podcasts/.../{season}/{episode-slug}/ form.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    prefix = '/'.join(path.split('/')[:5])  # /vrtmax/podcasts/<station>/<letter>

    _PAGE_QUERY = """
    query($pageId: ID!) {
      page(id: $pageId) {
        ... on IPage {
          components {
            __typename
            ... on ContainerNavigation {
              items {
                title
                components {
                  __typename
                  ... on PaginatedTileList { listId title }
                  ... on StaticTileList { listId title }
                  ... on LazyTileList { listId title }
                }
              }
            }
            ... on PaginatedTileList { listId title }
            ... on StaticTileList { listId title }
            ... on LazyTileList { listId title }
          }
        }
      }
    }
    """
    variables = {"pageId": path}
    logger.debug(f"Fetching podcast lists for {path!r}")
    response_data = _execute_graphql_query(_PAGE_QUERY, variables)
    if not response_data:
        logger.debug("No GraphQL response; cannot expand podcast URL")
        return []

    page_data = (response_data.get("data") or {}).get("page")
    if not page_data:
        logger.debug(f"No page data for podcast {slug!r}")
        return []

    candidates = _collect_list_ids(page_data.get("components", []))
    logger.debug(f"Podcast: found {len(candidates)} list candidate(s)")

    all_episodes: list[str] = []
    for title, list_id in candidates:
        episodes = _fetch_episodes_by_list_id(list_id, max_episodes)
        for ep_url in episodes:
            # yt-dlp handles full VRT MAX episode URLs directly
            all_episodes.append(ep_url)

    return all_episodes


def fetch_all_seasons(url: str, max_episodes: int | None = None) -> list[str]:
    """Given a show-level URL, discover all seasons and expand each into episode URLs.

    Example::

        fetch_all_seasons("https://www.vrt.be/vrtmax/a-z/thuis")
        → ["https://www.vrt.be/vrtmax/a-z/thuis/1/…",
           "https://www.vrt.be/vrtmax/a-z/thuis/2/…",
           …]
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    segments = [seg for seg in path.split('/') if seg]

    # Podcast show URL: /vrtmax/podcasts/{station}/{letter}/{slug}
    if len(segments) >= 3 and segments[0] == 'vrtmax' and segments[1] == 'podcasts':
        return _fetch_podcast_episodes(url, segments[2], max_episodes)

    if len(segments) < 3 or segments[0] != 'vrtmax' or segments[1] != 'a-z':
        return []

    slug = segments[2]

    _PAGE_QUERY = """
    query($pageId: ID!) {
      page(id: $pageId) {
        ... on IPage {
          components {
            __typename
            ... on PaginatedTileList { listId title }
            ... on StaticTileList { listId title }
            ... on LazyTileList { listId title }
            ... on ContainerNavigation {
              items {
                title
                components {
                  __typename
                  ... on PaginatedTileList { listId title }
                  ... on StaticTileList { listId title }
                  ... on LazyTileList { listId title }
                  ... on ContainerNavigation {
                    items {
                      title
                      components {
                        __typename
                        ... on PaginatedTileList { listId title }
                        ... on StaticTileList { listId title }
                        ... on LazyTileList { listId title }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    variables = {"pageId": f"/vrtmax/a-z/{slug}"}
    logger.debug("Fetching all season listIds for slug=%r", slug)
    response_data = _execute_graphql_query(_PAGE_QUERY, variables)
    if not response_data:
        logger.debug("No GraphQL response; cannot expand show URL")
        return []

    def _collect_list_ids(node, parent_title=''):
        results = []
        if isinstance(node, list):
            for item in node:
                results.extend(_collect_list_ids(item, parent_title))
        elif isinstance(node, dict):
            typename = node.get('__typename')
            title = node.get('title') or parent_title
            if typename in ('PaginatedTileList', 'StaticTileList', 'LazyTileList') and node.get('listId'):
                results.append((title, node['listId']))
            for k in ['components', 'items']:
                if k in node:
                    results.extend(_collect_list_ids(node[k], title))
        return results

    page_data = (response_data.get("data") or {}).get("page")
    if not page_data:
        logger.debug("No page data for slug=%r; cannot expand show URL", slug)
        return []
    components = page_data.get("components", [])
    candidates = _collect_list_ids(components)

    logger.debug("Found %s list_id candidate(s): %s", len(candidates), [(t[:30], lid[:20]) for t, lid in candidates])

    def _is_season_list(title: str) -> bool:
        if not title:
            return False
        title_lower = title.lower()
        if "meest recente" in title_lower or "meest recent" in title_lower:
            return False
        if "podcast" in title_lower:
            return False
        if "social" in title_lower or "volg ons" in title_lower:
            return False
        if "throwback" in title_lower:
            return False
        if "bloopers" in title_lower:
            return False
        if "achter de schermen" in title_lower:
            return False
        if "extra-s" in title_lower or "extra's" in title_lower:
            return False
        if "seizoen" in title_lower or "season" in title_lower:
            return True
        try:
            int(title.strip())
            return True
        except ValueError:
            pass
        return True

    season_lists = [(t, lid) for t, lid in candidates if _is_season_list(t)]

    if not season_lists:
        print(f"No season lists detected; using all {len(candidates)} candidate(s) as fallback", flush=True)
        season_lists = candidates

    print(f"Found {len(season_lists)} season(s)", flush=True)

    all_episodes: list[str] = []
    for title, list_id in season_lists:
        season_label = title or f"list-{list_id[:12]}"
        print(f"Expanding season: {season_label}", flush=True)

        episodes = _fetch_episodes_by_list_id(list_id, max_episodes)

        if not episodes:
            print(f"No episodes found for season {season_label}, skipping", flush=True)
            continue

        print(f"Found {len(episodes)} episode(s) for season {season_label}", flush=True)
        all_episodes.extend(episodes)

    return all_episodes


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure logging: always write to file, optionally to console.
    
    Args:
        level: If set, enables console logging at the given level.
               Values: "DEBUG", "INFO", "WARNING", "ERROR"
    """
    logger = logging.getLogger('thuis')
    logger.setLevel(logging.DEBUG)  # Allow all levels through; handlers filter
    
    # File handler — always on, date-based filename (e.g. logs/2026-07-07.log)
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    fh = logging.FileHandler(log_dir / f"{today}.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(fh)
    
    # Console handler — optional, controlled by --log-level
    if level:
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, level.upper()))
        ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logger.addHandler(ch)
    
    return logger


_NORMALIZE_HELP = """\
usage: thuis normalize [-h] [--dry-run] [--cleanup] directory

Normalize video files to scene format.

positional arguments:
  directory   Directory with video files

options:
  -h, --help  Show this help and exit
  --dry-run   Show what would be done without making changes
  --cleanup   Remove duplicates (_1) and stale .part files
"""


def _run_normalize_from_argv(argv: list[str]) -> None:
    """Parse normalize arguments from *argv* and execute."""
    if not argv or argv[0] in ("-h", "--help"):
        print(_NORMALIZE_HELP)
        return
    from thuis.normalizer import run_normalize
    from pathlib import Path
    directory = Path(argv[0])
    if not directory.is_dir():
        print(f"Fout: directory bestaat niet: {directory}")
        sys.exit(1)
    dry_run = "--dry-run" in argv
    cleanup = "--cleanup" in argv
    run_normalize(directory, dry_run=dry_run, cleanup=cleanup)


def _run_watchlist(args) -> None:
    """Run watchlist mode: check schedules and download due entries."""
    from pathlib import Path as _Path
    from thuis.watchlist import (
        parse_watchlist_file,
        resolve_output_dir,
        WatchlistDB,
        should_trigger,
    )
    from datetime import datetime

    now = datetime.now()
    db = WatchlistDB()
    due: list[tuple[str, str, str]] = []  # (url, schedule, output_dir)

    for wl_path in args.watchlist:
        if not _Path(wl_path).is_file():
            sys.exit(f"Error: watchlist file not found: {wl_path}")
        wl = parse_watchlist_file(wl_path)
        out_dir = resolve_output_dir(wl.output_dir)
        print(f"Watchlist {wl_path} → output: {out_dir}")
        for entry in wl.entries:
            # Determine schedule label for logging
            schedule = entry.schedule or "manual"
            # If --now flag is set, treat all entries (scheduled or not) as due.
            if args.now:
                print(f"  [due now] [{schedule}] {entry.url}")
                due.append((entry.url, schedule, out_dir))
                continue
            # Otherwise, only process manual entries when --now is present and scheduled entries per their schedule.
            if entry.schedule is None:
                # Manual-only entries require --now flag; skip otherwise
                continue
            if not should_trigger(entry.schedule, now, db.get_last_run(entry.url)):
                print(f"  [skip] not scheduled: [{schedule}] {entry.url}")
                continue
            # Skip DRM entries on scheduled runs (unless --now is used)
            last_status = db.get_last_status(entry.url)
            if last_status == "drm":
                print(f"  [skip] DRM protected: [{schedule}] {entry.url}")
                continue
            print(f"  [due ] [{schedule}] {entry.url}")
            due.append((entry.url, schedule, out_dir))

    if not due:
        print("Nothing to do — all entries already handled.")
        return

    # Record that these entries were triggered (per-URL last_run).
    # In dry-run mode we do NOT persist, so a real run can still pick them up.
    if not args.dry_run:
        for url, _sched, _out in due:
            db.set_last_run(url, status="triggered")
    db.close()

    # Re-invoke the normal download pipeline with the due URLs.
    # Each watchlist file has one output dir; group by dir.
    by_dir: dict[str, list[str]] = {}
    for url, _sched, out_dir in due:
        by_dir.setdefault(out_dir, []).append(url)

    rc = 0
    for out_dir, urls in by_dir.items():
        cmd = [
            os.path.dirname(os.path.abspath(__file__)) and sys.executable,
            "-m", "thuis.main",
            "--output-dir", out_dir,
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.profile is not None:
            cmd += ["--profile", str(args.profile)]
        cmd += ["--retry"]
        cmd += urls
        completed = subprocess.run(cmd)
        if completed.returncode != 0:
            rc = completed.returncode
    sys.exit(rc)


def main():
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit("\nInterrupted by user"))
    import argparse
    from pathlib import Path
    import re
    parser = argparse.ArgumentParser(
        description="Download VRT MAX videos using yt-dlp (POC)",
        epilog="""examples:
  ./thuis.sh https://www.vrt.be/vrtmax/...            # single URL
  ./thuis.sh --transcode 720p --input-dir media       # batch transcode
  ./thuis.sh --watchlist watchlists/podcast.txt --now # run watchlist now

 Watchlist mode requires --watchlist; --now only applies there.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Download options
    g_dl = parser.add_argument_group("download options")
    g_dl.add_argument("urls", nargs="*", help="VRT MAX URL(s) to download")
    g_dl.add_argument("--file", type=Path, help="Path to a file containing URLs (one per line)")
    g_dl.add_argument("--dry-run", action="store_true", help="Simulate download without downloading")
    g_dl.add_argument("--profile", "-p", type=int, help="Specify desired video resolution (e.g., 1080).")
    g_dl.add_argument("--retry", action="store_true", help="If set, skip download when output file already exists.")
    g_dl.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR), help="Directory to save downloaded files (default: media or OUTPUT_DIR env)")
    g_dl.add_argument("--max-episodes", type=int, default=None, help="Maximum number of episodes to process per season URL")
    g_dl.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None, help="Enable console logging at specified level (default: file only)")

    # Transcode options
    g_tr = parser.add_argument_group("transcode options")
    g_tr.add_argument("--transcode", type=str, default=None, help="Target resolution for transcoding (e.g., '720p', '1080p'). If set, transcode downloaded files to this resolution.")
    g_tr.add_argument("--allow-upscale", action="store_true", help="Allow upscaling lower resolutions to target (e.g., 540p -> 720p)")
    g_tr.add_argument("--keep-original", action="store_true", help="Keep original file when transcoding (default: replace)")
    g_tr.add_argument("--transcode-preset", type=str, default="fast", choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], help="FFmpeg preset for transcoding (default: fast)")
    g_tr.add_argument("--transcode-crf", type=int, default=23, help="FFmpeg CRF quality (0-51, lower=better, default: 23)")

    # Batch transcoding options (share transcode group)
    g_tr.add_argument("--input-dir", type=Path, help="Directory of existing files to transcode (batch mode)")
    g_tr.add_argument("--filter", action="append", default=[], help="Filter files by name (substring, case-insensitive). Can be used multiple times.")
    g_tr.add_argument("--recursive", action="store_true", help="Scan subdirectories recursively")
    g_tr.add_argument("--parallel", type=int, default=4, help="Concurrent transcoding jobs (default: 4)")
    g_tr.add_argument("--max", type=int, default=None, help="Maximum number of files to transcode (for testing)")

    # Watchlist options (require --watchlist)
    g_wl = parser.add_argument_group("watchlist options (require --watchlist)")
    g_wl.add_argument("--watchlist", action="append", default=[], metavar="FILE",
                        help="Process a watchlist file (first line = output dir, then [schedule] URL lines). Can be used multiple times.")
    g_wl.add_argument("--now", action="store_true",
                        help="With --watchlist: also run entries without a schedule (manual-only entries)")

    # Handle normalize subcommand — argparse nargs="*" on urls conflicts
    # with subparsers, so we intercept argv manually.
    if len(sys.argv) > 1 and sys.argv[1] == "normalize":
        _run_normalize_from_argv(sys.argv[2:])
        return

    # Handle doctor subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "doctor":
        try:
            from .doctor import run_doctor
        except ImportError:
            import doctor
            run_doctor = doctor.run_doctor
        import argparse as _ap
        _doc_parser = _ap.ArgumentParser()
        _doc_parser.add_argument("--fix", action="store_true", help="Attempt to auto-fix issues")
        _doc_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
        _doc_args = _doc_parser.parse_args(sys.argv[2:])
        sys.exit(run_doctor(fix_mode=_doc_args.fix, verbose=_doc_args.verbose))
        return

    args = parser.parse_args()

    # Handle watchlist mode (--watchlist provided)
    if args.watchlist:
        _run_watchlist(args)
        return

    # Handle batch transcoding mode (--input-dir provided)
    if args.input_dir:
        if not args.transcode:
            sys.exit("Error: --transcode is required when using --input-dir")
        from pathlib import Path
        import transcoder
        
        target_height = transcoder.parse_target_height(args.transcode)
        
        logger = setup_logging(args.log_level)
        
        stats = transcoder.batch_transcode_directory(
            directory=args.input_dir,
            target_height=target_height,
            filters=args.filter if args.filter else None,
            recursive=args.recursive,
            parallel=args.parallel,
            allow_upscale=args.allow_upscale,
            keep_original=args.keep_original,
            preset=args.transcode_preset,
            crf=args.transcode_crf,
            dry_run=args.dry_run,
            max_jobs=args.max,
        )
        
        print(f"\n=== Batch Transcode Summary ===")
        print(f"Total:     {stats['total']}")
        print(f"Transcoded: {stats['transcoded']}")
        print(f"Skipped:    {stats['skipped']}")
        print(f"Failed:     {stats['failed']}")
        sys.exit(0 if stats['failed'] == 0 else 1)

    logger = setup_logging(args.log_level)

    # Validate and normalise resolution profile
    if args.profile is not None:
        if args.profile not in VALIDATIONS:
            logger.warning(
                "Resolution %d not in standard resolutions %s; proceeding anyway",
                args.profile, VALIDATIONS,
            )
        args.profile_str = normalize_resolution(args.profile)
    else:
        args.profile_str = None

    # Verify output directory permission before proceeding
    if not args.output_dir.exists():
        try:
            # parents=True: create missing intermediate dirs (e.g. Media/podcasts/_seed)
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            sys.exit(
                f"Error: cannot create output directory {args.output_dir}: {e}\n"
                f"Hint: the parent dir is likely owned by another user (www-data). "
                f"Create it manually with correct ownership or run as a user with write access."
            )
    else:
        if not os.access(args.output_dir, os.W_OK):
            sys.exit(f"Error: no write permission for output directory {args.output_dir}")

    # Collect URLs
    urls = list(args.urls)
    if args.file:
        if not args.file.is_file():
            sys.exit(f"Error: file not found: {args.file}")
        with args.file.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    if not unique_urls:
        parser.print_help()
        sys.exit(1)

    # Expand season / show URLs to individual episode URLs
    expanded_urls = []
    for u in unique_urls:
        if is_season_url(u):
            print(f"Expanding season URL: {u}", flush=True)
            playlist = fetch_season_episodes(u, max_episodes=args.max_episodes)
            if playlist:
                print(f"Found {len(playlist)} episode(s)", flush=True)
                expanded_urls.extend(playlist)
            else:
                # If we can't expand, keep the original URL (fallback will handle it)
                expanded_urls.append(u)
        elif is_show_url(u):
            print(f"Expanding show URL to all seasons: {u}", flush=True)
            playlist = fetch_all_seasons(u, max_episodes=args.max_episodes)
            if playlist:
                print(f"Found {len(playlist)} episode(s) across all seasons", flush=True)
                expanded_urls.extend(playlist)
            else:
                print(f"No episodes found for any season, using URL as-is", flush=True)
                expanded_urls.append(u)
        elif "/vrtmax/podcasts/" in u and u.rstrip("/").count("/") >= 5:
            # Podcast show-level URL (…/podcasts/<station>/<letter>/<slug>)
            print(f"Expanding podcast URL to all episodes: {u}", flush=True)
            from thuis.url_parser import parse_vrt_url
            slug = parse_vrt_url(u).show_slug
            playlist = _fetch_podcast_episodes(u, slug, max_episodes=args.max_episodes)
            if playlist:
                print(f"Found {len(playlist)} podcast episode(s)", flush=True)
                expanded_urls.extend(playlist)
            else:
                print(f"No podcast episodes found, using URL as-is", flush=True)
                expanded_urls.append(u)
        else:
            expanded_urls.append(u)
    # Use the expanded list for further processing
    unique_urls = expanded_urls

    # Filter invalid URLs before processing
    unique_urls = [u for u in unique_urls if is_valid_vrt_url(u)]
    if not unique_urls:
        logger.error("No valid URLs to process")
        sys.exit(1)

    # Get credentials once
    email, password = get_credentials()

    # Optionally apply patch before running
    try:
        patch_ytdlp_if_needed()
    except Exception as e:
        logger.warning("Could not apply patch: %s", e)

# Process each URL individually with scene naming pipeline
    results = []
    db = watchlist.WatchlistDB()
    try:
        total = len(unique_urls)
        for idx, url in enumerate(unique_urls):
            print(f"[{idx+1}/{total}] Processing: {url}", flush=True)
            scene_template = None
            fallback_used = False
            
            try:
                # Step 1: Parse URL
                vrt_info = url_parser.parse_vrt_url(url)
                
                # Step 2: Fetch metadata for classification
                credentials = (email, password) if email and password else None
                metadata = metadata_fetcher.fetch_metadata(url, credentials)
                
                # Step 3: Classify content
                content_type = classifier.classify(vrt_info, metadata)
                
                # Step 3b: DRM policy gate
                # Check if content is DRM-protected and decryption is disabled
                if _is_drm_content(metadata):
                    policy = get_decrypt_policy()
                    if policy != "yes":
                        logger.info("DRM decryption disabled; set DECRYPT_DRM=yes in .env to enable")
                        # Skip this URL but continue with others
                        continue
                    # Policy is "yes" -> try DRM decryption using fork metadata
                    vudrm_token = metadata.get("_vrt_drm_vudrm_token")
                    mpd_url = metadata.get("_vrt_drm_mpd_url")
                    init_url = metadata.get("_vrt_drm_init_url")
                    
                    if vudrm_token and mpd_url and init_url:
                        logger.info("Attempting DRM decryption for %s", url)
                        # Build output name — scene_template not yet set at this point
                        title = metadata.get("title") or vrt_info.show_slug or "unknown"
                        if content_type == classifier.ContentType.TV:
                            show_norm = scene_namer.normalize_show_name(vrt_info.show_slug)
                            output_name = f"{show_norm}.S{vrt_info.season:02d}E{vrt_info.episode:02d}"
                        else:
                            output_name = title.replace(" ", ".")
                        
                        decrypted_file = drm_decrypt.decrypt_drm_content(
                            vudrm_token=vudrm_token,
                            mpd_url=mpd_url,
                            init_url=init_url,
                            output_dir=args.output_dir,
                            output_name=output_name,
                        )
                        
                        if decrypted_file and decrypted_file.exists():
                            logger.info("DRM decryption successful: %s", decrypted_file)
                            results.append(0)
                            # Skip normal download/post-processing
                            continue
                        else:
                            logger.warning("DRM decryption failed for %s, marking as drm", url)
                            results.append("drm")
                            # Persist DRM status
                            try:
                                from thuis.watchlist import WatchlistDB
                                db = WatchlistDB()
                                db.set_last_run(url, status="drm")
                                db.close()
                            except Exception as e:
                                logger.warning("Failed to persist DRM status: %s", e)
                            continue
                    else:
                        logger.warning("DRM detected but missing _vrt_drm_* metadata for %s", url)
                        results.append("drm")
                        try:
                            from thuis.watchlist import WatchlistDB
                            db = WatchlistDB()
                            db.set_last_run(url, status="drm")
                            db.close()
                        except Exception as e:
                            logger.warning("Failed to persist DRM status: %s", e)
                        continue
                
                # Step 4: Build scene filename based on content type
                resolution = audio_codec = video_codec = None
                if content_type == classifier.ContentType.TV:
                    # Get metadata for TV show
                    show_name = metadata.get('series') or vrt_info.show_slug.replace('-', ' ').title()
                    season_num = int(metadata.get('season')) if metadata.get('season') is not None and str(metadata.get('season')).isdigit() else int(vrt_info.season)
                    episode_num = int(metadata.get('episode')) if metadata.get('episode') is not None and str(metadata.get('episode')).isdigit() else int(vrt_info.episode)
                    resolution = metadata.get('height')
                    if resolution and resolution.endswith('p'):
                        resolution = resolution[:-1]  # Remove 'p' if present
                    audio_codec = metadata.get('acodec_raw')
                    video_codec = metadata.get('vcodec_raw')

                    # Detect date-based episode slugs (e.g. het-weer-d20260706)
                    date_match = re.search(r'-d(\d{8})/?$', str(vrt_info.path)) if isinstance(vrt_info.path, str) else None
                    if date_match:
                        scene_template = scene_namer.build_dated_tv_filename(
                            show_name=show_name or "Unknown Show",
                            date_str=date_match.group(1),
                            resolution=resolution,
                            audio_codec=audio_codec,
                            video_codec=video_codec,
                        )
                    else:
                        scene_template = scene_namer.build_tv_filename(
                            show_name=show_name or "Unknown Show",
                            season=season_num or 0,
                            episode=episode_num or 0,
                            resolution=resolution,
                            audio_codec=audio_codec,
                            video_codec=video_codec
                        )
                elif content_type == classifier.ContentType.MOVIE:
                    # Get metadata for movie
                    title = metadata.get('title') or vrt_info.show_slug.replace('-', ' ').title()
                    year = None
                    if metadata.get('season') and metadata.get('season').isdigit():
                        year = int(metadata.get('season'))
                    resolution = metadata.get('height')
                    if resolution and resolution.endswith('p'):
                        resolution = resolution[:-1]
                    audio_codec = metadata.get('acodec_raw')
                    video_codec = metadata.get('vcodec_raw')
                    
                    scene_template = scene_namer.build_movie_filename(
                        title=title or "Unknown Movie",
                        year=year,
                        resolution=resolution,
                        audio_codec=audio_codec,
                        video_codec=video_codec
                    )
                elif content_type == classifier.ContentType.SPECIAL:
                    # Get metadata for special
                    show_name = metadata.get('series') or vrt_info.show_slug.replace('-', ' ').title()
                    resolution = metadata.get('height')
                    if resolution and resolution.endswith('p'):
                        resolution = resolution[:-1]
                    audio_codec = metadata.get('acodec_raw')
                    video_codec = metadata.get('vcodec_raw')
                    
                    scene_template = scene_namer.build_special_filename(
                        show_name=show_name or "Unknown Show",
                        resolution=resolution,
                        audio_codec=audio_codec,
                        video_codec=video_codec
                    )
                else:  # UNKNOWN
                    # Try date-based slug before falling back to bare template
                    date_match = re.search(r'-d(\d{8})/?$', str(vrt_info.path)) if isinstance(vrt_info.path, str) else None
                    if date_match:
                        show_name = vrt_info.show_slug.replace('-', ' ').title()
                        # Set codecs/resolution so second fallback block doesn't overwrite dated template
                        resolution = metadata.get('height')
                        if resolution and resolution.endswith('p'):
                            resolution = resolution[:-1]
                        audio_codec = metadata.get('acodec_raw')
                        video_codec = metadata.get('vcodec_raw')
                        scene_template = scene_namer.build_dated_tv_filename(
                            show_name=show_name, date_str=date_match.group(1),
                            resolution=resolution, audio_codec=audio_codec, video_codec=video_codec)
                    else:
                        # Use metadata title (sanitized) instead of raw yt-dlp %(title)s
                        # to avoid ugly internal IDs like "vrtmax video #pbs-...$vid-..."
                        raw_title = metadata.get('title') or vrt_info.show_slug.replace('-', ' ').title()
                        resolution = metadata.get('height')
                        if resolution and resolution.endswith('p'):
                            resolution = resolution[:-1]
                        audio_codec = metadata.get('acodec_raw')
                        video_codec = metadata.get('vcodec_raw')

                        # If we have an episode slug from the URL path, include it
                        # (e.g. /fc-de-favorieten-bella-africa/ → Bella Africa)
                        episode_slug = None
                        path_segments = [s for s in vrt_info.path.split('/') if s]
                        if len(path_segments) >= 4:
                            episode_slug = path_segments[-1]
                        if episode_slug and episode_slug != vrt_info.show_slug:
                            # Build a descriptive filename: ShowName.S20.Bella.Africa.1080p.WEB-DL.AAC.x264.mp4
                            show_name = scene_namer.normalize_show_name(raw_title)
                            ep_name = episode_slug.replace('-', '.').title()
                            res = f".{resolution}p" if resolution else ""
                            codecs = scene_namer._codec_tags(audio_codec, video_codec)
                            season_int = int(vrt_info.season) if vrt_info.season else 0
                            scene_template = f"{show_name}.S{season_int:02d}.{ep_name}{res}.WEB-DL{codecs}.mp4"
                        else:
                            scene_template = scene_namer.build_special_filename(
                                show_name=raw_title,
                                resolution=resolution,
                                audio_codec=audio_codec,
                                video_codec=video_codec,
                            )
                    fallback_used = True

                if not any([resolution, audio_codec, video_codec]) and "%" in scene_template:
                    # Metadata failed — use scene template WITHOUT codecs
                    # only when we haven't already built a concrete filename
                    # (e.g. UNKNOWN branch with episode slug already set one).
                    # This gives scene-compatible naming for dedup matching.
                    if content_type == classifier.ContentType.TV:
                        scene_template = scene_namer.build_tv_filename(
                            show_name, season_num, episode_num,
                            None, None, None)
                    elif content_type == classifier.ContentType.MOVIE:
                        scene_template = scene_namer.build_movie_filename(
                            title, None, None, None, None)
                    elif content_type == classifier.ContentType.SPECIAL:
                        scene_template = scene_namer.build_special_filename(
                            show_name, None, None, None)
                    else:
                        scene_template = "%(title)s.%(ext)s"
                    fallback_used = True

            except Exception as e:
                # If any step fails, log and skip — don't run yt-dlp on a known-bad URL
                logger.warning("Failed to process %s: %s (%s)", url, e, type(e).__name__)
                continue
            
            # Pre-download dedup: check database FIRST (O(1)), fall back to filesystem glob
            try:
                if db.file_was_downloaded(url, scene_template, str(args.output_dir)):
                    logger.info("Skipped %s: already in database as %s", url, scene_template)
                    continue
            except Exception as e:
                logger.warning("DB dedup failed for %s: %s", url, e)

            # Fallback: filesystem glob check (existing logic)
            if content_type == classifier.ContentType.TV:
                show_norm = scene_namer.normalize_show_name(show_name)
                res_part = f".{resolution}p" if resolution else ""
                search = f"{show_norm}.S{season_num:02d}E{episode_num:02d}{res_part}*.mp4"
                logger.debug("Glob fallback: %s", search)
                matches = list(args.output_dir.glob(search))
                if matches:
                    names = ", ".join(m.name for m in matches)
                    logger.info("Skipped %s: already exists as %s", url, names)
                    continue
            elif scene_template and "%" not in scene_template:
                output_file = args.output_dir / scene_template
                if output_file.exists():
                    logger.info("Skipped %s: %s already exists", url, scene_template)
                    continue

            # Podcast URLs are not supported by yt-dlp's VRT extractor:
            # resolve the page to a direct HLS audio URL first.
            download_url = url
            if "/vrtmax/podcasts/" in url:
                resolved_pair = _resolve_podcast_stream_url(url)
                if not resolved_pair:
                    logger.error("Kon podcast stream niet resolven: %s", url)
                    continue
                download_url, podcast_title = resolved_pair
                # Use the episode title as the output filename (sanitised)
                safe_title = re.sub(r'[\\/:*?"<>|]+', "", podcast_title).strip().replace(" ", ".")
                scene_template = f"{safe_title}.%(ext)s"
                fallback_used = False

            # Build yt-dlp arguments for this URL
            url_args_list = build_yt_dlp_args(
                [download_url], dry_run=args.dry_run, output_dir=args.output_dir,
                output_template=scene_template, email=email, password=password,
                resolution=args.profile_str,
            )
            if is_audio_only_stream(download_url):
                # Audio-only: pick best audio format instead of video
                try:
                    idx = url_args_list.index("bestvideo+bestaudio")
                    url_args_list[idx] = "bestaudio"
                except ValueError:
                    pass
                # Remove video merge flag to keep a pure audio container (e.g., .m4a)
                try:
                    mi = url_args_list.index("--merge-output-format")
                    del url_args_list[mi:mi + 2]
                except ValueError:
                    pass
            
            # Print status message
            if args.dry_run:
                if fallback_used:
                    print(f"[DRY-RUN] (fallback) {scene_template} ← {url}")
                else:
                    print(f"[DRY-RUN] {scene_template} ← {url}")
            else:
                print(f"Download started: {url}", flush=True)
# Always run yt-dlp (in dry-run mode, this will be with --simulate)
            def _mask_secrets(args_list):
                """Mask sensitive arguments like --password and --username in the args list."""
                masked = []
                skip_next = False
                for arg in args_list:
                    if skip_next:
                        masked.append("****")
                        skip_next = False
                    elif arg in ("--password", "--username"):
                        masked.append(arg)
                        skip_next = True
                    else:
                        masked.append(arg)
                return masked

            print("Running:", " ".join(_mask_secrets(url_args_list)))
            try:
                # Run yt-dlp with stderr tee for DRM detection
                returncode, stderr_text = _run_ytdlp_with_drm_detection(url_args_list)

                # DRM classification: check for exact marker from yt-dlp's report_drm
                drm_marker = "This video is DRM protected"
                if drm_marker in stderr_text:
                    logger.info("DRM detected for %s", url)
                    results.append("drm")
                    # Persist DRM status in WatchlistDB
                    try:
                        from thuis.watchlist import WatchlistDB
                        db = WatchlistDB()
                        db.set_last_run(url, status="drm")
                        db.close()
                    except Exception as e:
                        logger.warning("Failed to persist DRM status: %s", e)
                    continue  # Skip post-download processing for DRM

                results.append(returncode)

                # Record successful download in database
                if returncode == 0 and not args.dry_run:
                    try:
                        # Find the actual filename that yt-dlp created
                        actual_filename = _find_downloaded_file(
                            args.output_dir, scene_template, url)
                        record_name = actual_filename or scene_template
                        db.record_download(url, record_name, str(args.output_dir))
                        if actual_filename:
                            logger.info("Recorded download as: %s", actual_filename)
                    except Exception as e:
                        logger.warning("Failed to record download in DB: %s", e)

                # Post-download transcoding if requested and download succeeded
                if args.transcode and returncode == 0 and not args.dry_run:
                    import transcoder
                    
                    # Parse target height from --transcode argument
                    target_height = transcoder.parse_target_height(args.transcode)
                    
                    # Find the downloaded file
                    output_files = list(args.output_dir.glob("*.mp4"))
                    for f in output_files:
                        if f.stat().st_mtime > (time.time() - 300):  # Modified in last 5 minutes
                            # Check if there are related files with different resolutions
                            # (e.g., both 1080p and 540p versions of the same episode)
                            base_name = re.sub(r'\.(S\d+E\d+|d\d{8}).*', '', f.stem)
                            related_files = transcoder.find_related_files(args.output_dir, base_name)
                            
                            # Find the best source for transcoding (prefer higher resolution)
                            best_source = transcoder.find_best_source_for_transcoding(
                                related_files if related_files else [f],
                                target_height,
                            )
                            
                            if best_source and best_source != f:
                                logger.info(f"Using best source for transcoding: {best_source.name}")
                            
                            success, out_path, error = transcoder.transcode_file_if_needed(
                                best_source or f,
                                keep_original=args.keep_original,
                                target_height=target_height,
                                allow_upscale=args.allow_upscale,
                            )
                            if success:
                                logger.info(f"Transcoded {f.name} to {target_height}p")
                            elif error:
                                logger.warning(f"Transcoding failed for {f.name}: {error}")
                            break  # Only process the most recent file
            except Exception:
                # On any unexpected error, record failure
                results.append(1)
            except KeyboardInterrupt:
                print("\nInterrupted")
                sys.exit(1)
        
        def _exit_with_code(results):
            drm_results = [r for r in results if r == "drm"]
            non_drm_results = [r for r in results if r != "drm"]
            
            if drm_results and not non_drm_results:
                print(f"\n=== DRM Summary ===")
                print(f"Total DRM protected: {len(drm_results)}")
                print(f"No downloadable content found.")
                sys.exit(0)
            if drm_results and non_drm_results:
                print(f"\n=== DRM Summary ===")
                print(f"DRM protected: {len(drm_results)}")
                print(f"Other results: {len(non_drm_results)}")
                if any(r != 0 for r in non_drm_results):
                    sys.exit(1)
                sys.exit(0)
            if any(r != 0 for r in results):
                sys.exit(1)
            sys.exit(0)

        _exit_with_code(results)

    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()