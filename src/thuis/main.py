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
        print(f"[DEBUG] GraphQL POST{var_hint} ...", flush=True)
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                print(f"[DEBUG] GraphQL returned status {response.status}", flush=True)
                return None
            body = json.loads(response.read().decode())
            print(f"[DEBUG] GraphQL response OK{var_hint}", flush=True)
            return body
    except Exception as e:
        print(f"[DEBUG] GraphQL error{var_hint}: {type(e).__name__}: {e}", flush=True)
        return None
# Ensure project root and src/thuis are on sys.path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src', 'thuis'))
import shutil
import subprocess
import tempfile
import platform
import logging
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

# Default credentials (for demonstration / testing only)
DEFAULT_EMAIL = "kuxelu@ipdeer.com"
DEFAULT_PASSWORD = "Els123456"

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
    
    print(f"[DEBUG] HEAD probing: {show_slug} season {season}, max {max_episodes_hard} episodes", flush=True)
    
    while True:
        if len(episodes) >= max_episodes_hard:
            print(f"[DEBUG] Hit max episode limit ({max_episodes_hard}), stopping HEAD probing", flush=True)
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
                            print(f"[DEBUG] HEAD found episode {episode}: {url} (status {response.status})", flush=True)
                            episodes.append(url)
                            found_any = True
                            break  # One URL per episode — avoid duplicates
                except urllib.error.HTTPError as e:
                    try:
                        body_preview = e.read(500).decode("utf-8", errors="ignore")
                    except:
                        body_preview = ""
                    if not _is_not_found(e.code, body_preview):
                        print(f"[DEBUG] HEAD found episode {episode} via HTTPError {e.code}: {url}", flush=True)
                        episodes.append(url)
                        found_any = True
                        break  # One URL per episode — avoid duplicates
            except Exception as ex:
                if episode <= 3:  # Only log early failures
                    print(f"[DEBUG] HEAD exception for {url}: {type(ex).__name__}: {ex}", flush=True)
                continue
                
        if not found_any:
            print(f"[DEBUG] No more episodes found after #{episode - 1} (total: {len(episodes)})", flush=True)
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
    print(f"[DEBUG] Fetching list_id for slug={show_slug!r} season={season}", flush=True)
    response_data = _execute_graphql_query(query, variables)
    if not response_data:
        print(f"[DEBUG] No graphql response for _get_list_id", flush=True)
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

    print(f"[DEBUG] Found {len(candidates)} list_id candidate(s): {[(t[:30], lid[:20]) for t, lid in candidates]}", flush=True)

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

    print(f"[DEBUG] After filtering: {len(filtered)} of {len(candidates)} candidates remain", flush=True)

    # Match by title containing season number
    season_str = str(season)
    for title, lid in filtered:
        title_norm = title.lower().replace('(', ' ').replace(')', ' ')
        words = title_norm.split()
        if season_str in words or f"seizoen-{season_str}" in title_norm:
            print(f"[DEBUG] Matched list_id {lid!r} by season title {title!r}", flush=True)
            return lid

    # Fallback: return first listId found
    # Use filtered list if non-empty, otherwise fall back to original candidates
    # (handles shows where all lists have empty titles, e.g. FC De Kampioenen)
    fallback = filtered if filtered else candidates
    if fallback:
        print(f"[DEBUG] No season match, using first list_id: {fallback[0][1]!r}", flush=True)
        return fallback[0][1]
    print(f"[DEBUG] No list_id found at all", flush=True)
    return None


def get_credentials():
    """Return (email, password) from environment, falling back to defaults."""
    email = os.getenv("VRT_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("VRT_PASSWORD", DEFAULT_PASSWORD)
    return email, password


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


def build_yt_dlp_args(urls, dry_run=False, output_dir=Path("media"), output_template=None, email=None, password=None, resolution=None):
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

        print(f"[DEBUG] GraphQL page {page_count} (episodes so far: {len(episodes)})", flush=True)
        response = _execute_graphql_query(_LIST_QUERY, variables)
        if not response or 'data' not in response:
            print(f"[DEBUG] GraphQL returned no data, stopping pagination", flush=True)
            break

        list_data = response['data'].get('list', {})
        if not list_data:
            print(f"[DEBUG] GraphQL list_data is empty, stopping pagination", flush=True)
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

        print(f"[DEBUG] Page {page_count} has {len(items)} items", flush=True)

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
                    print(f"[DEBUG] Paginating: after={after!r}", flush=True)
                else:
                    print(f"[DEBUG] hasNextPage=True but endCursor is missing/empty — stopping to avoid infinite loop", flush=True)
                    break
            else:
                print(f"[DEBUG] No more pages (hasNextPage=False)", flush=True)
                break
        else:
            # StaticTileList — no more pages
            print(f"[DEBUG] StaticTileList (no page_info), stopping", flush=True)
            break

    if page_count >= max_pages:
        print(f"[DEBUG] Reached max pages ({max_pages}), stopping pagination", flush=True)

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
            print(f"[DEBUG] Could not extract slug/season from URL", flush=True)
            return []

        print(f"[DEBUG] Extracted slug={slug!r} season={season}", flush=True)

        list_id = _get_list_id(slug, season)
        if not list_id:
            print(f"[DEBUG] No list_id found, falling back to HEAD probing...", flush=True)
            return _guess_episode_urls(slug, season, max_episodes)

        print(f"[DEBUG] Found list_id={list_id!r}, fetching episodes via GraphQL...", flush=True)

        episodes = _fetch_episodes_by_list_id(list_id, max_episodes)

        if not episodes:
            print(f"[DEBUG] GraphQL returned 0 episodes, falling back to HEAD probing...", flush=True)
            return _guess_episode_urls(slug, season, max_episodes)

        print(f"[DEBUG] GraphQL returned {len(episodes)} episodes total", flush=True)
        return episodes
    except Exception as e:
        print(f"[DEBUG] fetch_season_episodes exception: {type(e).__name__}: {e}", flush=True)
        return []


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
    print(f"[DEBUG] Fetching all season listIds for slug={slug!r}", flush=True)
    response_data = _execute_graphql_query(_PAGE_QUERY, variables)
    if not response_data:
        print(f"No GraphQL response; cannot expand show URL", flush=True)
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
        print(f"No page data for slug={slug!r}; cannot expand show URL", flush=True)
        return []
    components = page_data.get("components", [])
    candidates = _collect_list_ids(components)

    print(f"[DEBUG] Found {len(candidates)} list_id candidate(s): {[(t[:30], lid[:20]) for t, lid in candidates]}", flush=True)

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

Normaliseer videobestanden naar scene-formaat.

positional arguments:
  directory   Directory met videobestanden

options:
  -h, --help  Toon deze hulp en sluit af
  --dry-run   Toon wat er zou gebeuren zonder wijzigingen
  --cleanup   Verwijder duplicates (_1) en stale .part files
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


def main():
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit("\nInterrupted by user"))
    import argparse
    from pathlib import Path
    import re
    parser = argparse.ArgumentParser(description="Download VRT MAX videos using yt-dlp (POC)")
    parser.add_argument("urls", nargs="*", help="VRT MAX URL(s) to download")
    parser.add_argument("--file", type=Path, help="Path to a file containing URLs (one per line)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate download without downloading")

    parser.add_argument("--profile", "-p", type=int, help="Specify desired video resolution (e.g., 1080).")
    parser.add_argument("--retry", action="store_true", help="If set, skip download when output file already exists.")
    parser.add_argument("--output-dir", type=Path, default=Path("media"), help="Directory to save downloaded files (default: media)")
    parser.add_argument("--max-episodes", type=int, default=None, help="Maximum number of episodes to process per season URL")
    parser.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None, help="Enable console logging at specified level (default: file only)")

    # Transcoding options
    parser.add_argument("--transcode", type=str, default=None, help="Target resolution for transcoding (e.g., '720p', '1080p'). If set, transcode downloaded files to this resolution.")
    parser.add_argument("--allow-upscale", action="store_true", help="Allow upscaling lower resolutions to target (e.g., 540p -> 720p)")
    parser.add_argument("--keep-original", action="store_true", help="Keep original file when transcoding (default: replace)")
    parser.add_argument("--transcode-preset", type=str, default="fast", choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], help="FFmpeg preset for transcoding (default: fast)")
    parser.add_argument("--transcode-crf", type=int, default=23, help="FFmpeg CRF quality (0-51, lower=better, default: 23)")

    # Batch transcoding options
    parser.add_argument("--input-dir", type=Path, help="Directory of existing files to transcode (batch mode)")
    parser.add_argument("--filter", action="append", default=[], help="Filter files by name (substring, case-insensitive). Can be used multiple times.")
    parser.add_argument("--recursive", action="store_true", help="Scan subdirectories recursively")
    parser.add_argument("--parallel", type=int, default=2, help="Concurrent transcoding jobs (default: 2)")

    # Handle normalize subcommand — argparse nargs="*" on urls conflicts
    # with subparsers, so we intercept argv manually.
    if len(sys.argv) > 1 and sys.argv[1] == "normalize":
        _run_normalize_from_argv(sys.argv[2:])
        return

    args = parser.parse_args()

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
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            sys.exit(f"Error: cannot create output directory {args.output_dir}: {e}")
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
    try:
        total = len(unique_urls)
        for idx, url in enumerate(unique_urls):
            print(f"[{idx+1}/{total}] Verwerken: {url}", flush=True)
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
                        scene_template = scene_namer.build_dated_tv_filename(
                            show_name=show_name, date_str=date_match.group(1))
                    else:
                        scene_template = "%(title)s.%(ext)s"
                    fallback_used = True

                if not any([resolution, audio_codec, video_codec]):
                    # Metadata failed — use scene template WITHOUT codecs
                    # instead of falling back to %(title)s.%(ext)s.
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
            
            # Pre-download dedup: skip if the episode already exists
            # in the output directory in scene-normalized form.
            # Uses glob matching on show/season/episode so it works
            # even when the scene template is "%(title)s.%(ext)s".
            if content_type == classifier.ContentType.TV:
                show_norm = scene_namer.normalize_show_name(show_name)
                res_part = f".{resolution}p" if resolution else ""
                search = f"{show_norm}.S{season_num:02d}E{episode_num:02d}{res_part}*.mp4"
                print(f"[DEBUG] Glob: {search}", flush=True)
                matches = list(args.output_dir.glob(search))
                if matches:
                    names = ", ".join(m.name for m in matches)
                    logger.info("Overgeslagen %s: bestaat al als %s", url, names)
                    continue
            elif scene_template and "%" not in scene_template:
                output_file = args.output_dir / scene_template
                if output_file.exists():
                    logger.info("Overgeslagen %s: %s bestaat al", url, scene_template)
                    continue

            # Build yt-dlp arguments for this URL
            url_args_list = build_yt_dlp_args(
                [url], dry_run=args.dry_run, output_dir=args.output_dir,
                output_template=scene_template, email=email, password=password,
                resolution=args.profile_str,
            )
            
            # Print status message
            if args.dry_run:
                if fallback_used:
                    print(f"[DRY-RUN] (fallback) {scene_template} ← {url}")
                else:
                    print(f"[DRY-RUN] {scene_template} ← {url}")
# Always run yt-dlp (in dry-run mode, this will be with --simulate)
            print("Running:", " ".join(url_args_list))
            try:
                # Run yt-dlp
                completed = subprocess.run(url_args_list, check=False)
                results.append(completed.returncode)
                
                # Post-download transcoding if requested and download succeeded
                if args.transcode and completed.returncode == 0 and not args.dry_run:
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
        
        # Exit with appropriate code
        if results:
            # If any subprocess failed, exit with error code
            if any(r != 0 for r in results):
                sys.exit(1)
            else:
                sys.exit(0)
        else:
            # No URLs processed
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()