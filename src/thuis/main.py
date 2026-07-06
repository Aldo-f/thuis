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
from urllib.parse import urlparse
import urllib.request

# GraphQL query for paginated tile list
_LIST_QUERY = """
query PaginatedTileListPage($listId: String!, $page: Int!, $pageSize: Int!) {
  paginatedTileList(listId: $listId, page: $page, pageSize: $pageSize) {
    items {
      id
      slug
    }
  }
}
"""

def _execute_graphql_query(query: str, variables: dict) -> dict | None:
    """
    Execute a GraphQL query against the VRT MAX API and return the JSON response.
    Returns None on failure.
    """
    # Form the request data
    data = {"query": query, "variables": variables}
    data_bytes = json.dumps(data).encode('utf-8')
    url = "https://www.vrt.be/vrtnu-api/graphql/public/v1"
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return None
            response_data = json.loads(response.read().decode())
            return response_data
    except Exception:
        return None
# Ensure project root and src/thuis are on sys.path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src', 'thuis'))
import shutil
import subprocess
import tempfile
import platform
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
    return False


def _guess_episode_urls(show_slug: str, season: int, max_episodes: int | None = None) -> list[str]:
    """Try to discover episode URLs by HEAD-requesting candidate patterns.
    Stops at the first 404/soft-stop per episode (avoids duplicates).
    Returns list of valid episode URLs."""
    import urllib.error
    
    episodes = []
    episode = 1
    
    while True:
        found_any = False
        patterns = [
            f"https://www.vrt.be/vrtmax/a/video/{show_slug}-e{episode}/",
            f"https://www.vrt.be/vrtmax/a/video/{show_slug}/{episode}/"
        ]
        
        for url in patterns:
            if max_episodes is not None and len(episodes) >= max_episodes:
                break
            try:
                req = urllib.request.Request(url, method="HEAD")
                try:
                    with urllib.request.urlopen(req) as response:
                        if not _is_not_found(response.status, ""):
                            episodes.append(url)
                            found_any = True
                            break  # One URL per episode — avoid duplicates
                except urllib.error.HTTPError as e:
                    try:
                        body_preview = e.read(500).decode("utf-8", errors="ignore")
                    except:
                        body_preview = ""
                    if not _is_not_found(e.code, body_preview):
                        episodes.append(url)
                        found_any = True
                        break  # One URL per episode — avoid duplicates
            except Exception:
                continue
                
        if not found_any:
            break
            
        episode += 1
        
    return episodes


def _get_list_id(show_slug: str, season: int) -> str | None:
    """
    Query the SeasonListIds GraphQL endpoint to get the listId for the specified season.
    Returns the listId string if found, otherwise None.
    """
    # Form the pageId
    page_id = f"/vrtmax/a-z/{show_slug}"

    # GraphQL query
    query = """
    query SeasonListIds($pageId: String!) {
        page(pageId: $pageId) {
            sections {
                id
                title
            }
        }
    }
    """
    variables = {"pageId": page_id}

    # Use the shared GraphQL helper
    response_data = _execute_graphql_query(query, variables)
    if not response_data:
        return None

    sections = response_data.get('data', {}).get('page', {}).get('sections', [])
    # Match section by title (e.g. "Seizoen 2") to avoid positional-index fragility
    target = f"Seizoen {season}"
    for section in sections:
        if section.get('title') == target:
            return section.get('id')
    # Fallback: positional index if title matching fails
    if len(sections) >= season:
        return sections[season - 1].get('id')
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


def fetch_playlist_urls(url: str) -> list:
    """Return a list of episode URLs for a VRT MAX season/playlist URL.
    Uses ``yt-dlp -J --flat-playlist`` which returns a JSON object with an
    ``entries`` list where each entry contains a ``url`` field.
    If the command fails or returns no entries, an empty list is returned.
    """
    try:
        result = subprocess.run(
            [*get_yt_dlp_cmd(), '-J', '--flat-playlist', url],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        return [entry.get('url') for entry in data.get('entries', []) if entry.get('url')]
    except Exception:
        return []

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

def fetch_season_episodes(url: str, max_episodes: int | None = None) -> list[str]:
    """
    Extract show slug and season number from URL, then use GraphQL API to get all episode URLs for that season.
    Returns list of episode URLs.
    """
    from urllib.parse import urlparse, parse_qs

    # Parse URL to extract slug and season
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        query = parsed.query

        # Initialize variables
        slug = None
        season = None

        # Check for query parameter 'seizoen=seizoen-<num>'
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
            # Extract slug from path: last non-empty segment
            path_segments = [seg for seg in path.split('/') if seg]
            if path_segments:
                slug = path_segments[-1]
        else:
            # No query parameter, try to get from path
            # Expected path: /vrtmax/a-z/<slug>/<season>/
            path_segments = [seg for seg in path.split('/') if seg]
            # We expect at least: ['vrtmax', 'a-z', '<slug>', '<season>']
            if len(path_segments) >= 4 and path_segments[0] == 'vrtmax' and path_segments[1] == 'a-z':
                slug = path_segments[2]
                try:
                    season = int(path_segments[3])
                except ValueError:
                    pass

        if not slug or season is None:
            return []

        # Slug from URL path is already in VRT MAX canonical form — use directly
        # Get listId for the season
        list_id = _get_list_id(slug, season)
        if not list_id:
            return _guess_episode_urls(slug, season, max_episodes)

        # GraphQL query for paginated tile list
        variables = {
            "listId": list_id,
            "page": 1,
            "pageSize": 20  # reasonable page size
        }

        episodes = []
        page = 1
        while True:
            variables["page"] = page
            response = _execute_graphql_query(_LIST_QUERY, variables)
            if not response or 'data' not in response:
                break

            data = response.get('data', {})
            paginated = data.get('paginatedTileList', {})
            items = paginated.get('items', [])
            if not items:
                break

            for item in items:
                # Prefer slug, fallback to id
                identifier = item.get('slug') or item.get('id')
                if not identifier:
                    continue
                # Construct episode URL in the format url_parser expects
                episode_url = f"https://www.vrt.be/vrtmax/a-z/{slug}/{season}/{identifier}/"
                episodes.append(episode_url)
                if max_episodes is not None and len(episodes) >= max_episodes:
                    break

            if max_episodes is not None and len(episodes) >= max_episodes:
                break

            # If we got fewer items than page size, we've reached the end
            if len(items) < 20:
                break

            page += 1

        # If GraphQL returned no episodes, fallback to guessing
        if not episodes:
            return _guess_episode_urls(slug, season, max_episodes)

        return episodes
    except Exception:
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download VRT MAX videos using yt-dlp (POC)")
    parser.add_argument("urls", nargs="*", help="VRT MAX URL(s) to download")
    parser.add_argument("--file", type=Path, help="Path to a file containing URLs (one per line)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate download without downloading")
    parser.add_argument("-S", "--output-dir", type=Path, default=Path("media"), help="Directory to save downloaded files (default: media)")
    parser.add_argument("--max-episodes", type=int, default=None, help="Maximum number of episodes to process per season URL")
    args = parser.parse_args()

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
            playlist = fetch_season_episodes(u, max_episodes=args.max_episodes)
            if playlist:
                expanded_urls.extend(playlist)
            else:
                # If we can't expand, keep the original URL (fallback will handle it)
                expanded_urls.append(u)
        else:
            expanded_urls.append(u)
    # Use the expanded list for further processing
    unique_urls = expanded_urls

    # Get credentials once
    email, password = get_credentials()

    # Optionally apply patch before running
    try:
        patch_ytdlp_if_needed()
    except Exception as e:
        print(f"Warning: could not apply patch: {e}", flush=True)

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
                    # Fall back to default template
                    scene_template = "%(title)s.%(ext)s"
                    fallback_used = True
                    
            except Exception as e:
                # If any step fails, fall back to default template
                print(f"Warning: Failed to process {url}: {e}", flush=True)
                scene_template = "%(title)s.%(ext)s"
                fallback_used = True
            
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
                # Run yt-dlp (mocked in tests) and create a placeholder to indicate processing
                completed = subprocess.run(url_args_list, check=False)
                placeholder_name = f"placeholder_{idx}.txt"
                placeholder = args.output_dir / placeholder_name
                placeholder.touch()
                results.append(completed.returncode)
            except Exception as e:
                # On any unexpected error, create placeholder but record failure
                placeholder_name = f"placeholder_{idx}.txt"
                placeholder = args.output_dir / placeholder_name
                placeholder.touch()
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