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
    from . import url_parser, classifier, metadata_fetcher, scene_namer
except ImportError:
    # When run directly
    import url_parser
    import classifier
    import metadata_fetcher
    import scene_namer

# Default credentials (for demonstration / testing only)
DEFAULT_EMAIL = "kuxelu@ipdeer.com"
DEFAULT_PASSWORD = "Els123456"


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
        patterns = [
            f"https://www.vrt.be/vrtmax/a/video/{show_slug}-e{episode}/",
            f"https://www.vrt.be/vrtmax/a/video/{show_slug}/{episode}/"
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
            ... on ContainerNavigation {
              items {
                components {
                  __typename
                  ... on PaginatedTileList { listId title }
                  ... on StaticTileList { listId title }
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

    def _collect_list_ids(components: list) -> list[tuple[str, str]]:
        results = []
        for comp in components or []:
            t = comp.get("__typename")
            if t in ("PaginatedTileList", "StaticTileList") and comp.get("listId"):
                results.append((comp.get("title") or "", comp["listId"]))
            elif t == "ContainerNavigation":
                for item in comp.get("items") or []:
                    for sub in item.get("components") or []:
                        st = sub.get("__typename")
                        if st in ("PaginatedTileList", "StaticTileList") and sub.get("listId"):
                            results.append((sub.get("title") or "", sub["listId"]))
        return results

    components = response_data.get("data", {}).get("page", {}).get("components", [])
    candidates = _collect_list_ids(components)

    print(f"[DEBUG] Found {len(candidates)} list_id candidate(s): {[(t[:30], lid[:20]) for t, lid in candidates]}", flush=True)

    # Match by title containing season number
    season_str = str(season)
    for title, lid in candidates:
        if season_str in title:
            print(f"[DEBUG] Matched list_id {lid!r} by season title {title!r}", flush=True)
            return lid

    # Fallback: return first listId found
    if candidates:
        print(f"[DEBUG] No season match, using first list_id: {candidates[0][1]!r}", flush=True)
        return candidates[0][1]
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


def build_yt_dlp_args(urls, dry_run=False, output_dir=Path("media"), output_template=None, email=None, password=None):
    """Build yt-dlp argument list."""
    args = []
    args.extend(get_yt_dlp_cmd())
    # Common options: best video+audio, merge to mp4, no warnings, no color
    args += [
        "-f", "bestvideo+bestaudio",
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

        # Cursor-based pagination through episodes
        episodes = []
        after: str | None = None
        max_pages = 100
        page_count = 0

        while page_count < max_pages:
            page_count += 1
            variables = {"listId": list_id}
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
            items = []
            page_info = None

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

        if not episodes:
            print(f"[DEBUG] GraphQL returned 0 episodes, falling back to HEAD probing...", flush=True)
            return _guess_episode_urls(slug, season, max_episodes)

        print(f"[DEBUG] GraphQL returned {len(episodes)} episodes total", flush=True)
        return episodes
    except Exception as e:
        print(f"[DEBUG] fetch_season_episodes exception: {type(e).__name__}: {e}", flush=True)
        return []


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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download VRT MAX videos using yt-dlp (POC)")
    parser.add_argument("urls", nargs="*", help="VRT MAX URL(s) to download")
    parser.add_argument("--file", type=Path, help="Path to a file containing URLs (one per line)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate download without downloading")
    parser.add_argument("-S", "--output-dir", type=Path, default=Path("media"), help="Directory to save downloaded files (default: media)")
    parser.add_argument("--max-episodes", type=int, default=None, help="Maximum number of episodes to process per season URL")
    parser.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None, help="Enable console logging at specified level (default: file only)")
    args = parser.parse_args()

    logger = setup_logging(args.log_level)

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

    # Expand season URLs to individual episode URLs
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
        for idx, url in enumerate(unique_urls):
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
                    
            except Exception as e:
                # If any step fails, log and skip — don't run yt-dlp on a known-bad URL
                logger.warning("Failed to process %s: %s (%s)", url, e, type(e).__name__)
                continue
            
            # Build yt-dlp arguments for this URL
            url_args_list = build_yt_dlp_args([url], dry_run=args.dry_run, output_dir=args.output_dir, output_template=scene_template, email=email, password=password)
            
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