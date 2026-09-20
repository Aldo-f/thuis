"""Orchestrator for the Thuis CLI.

The heavy logic originally lived in ``thuis.main.main``; it has been moved here
to keep ``thuis.main`` as a thin delegator.  All imports that would cause a
circular dependency on ``thuis.main`` are performed lazily inside the relevant
functions.
"""

from __future__ import annotations

import signal
import sys
from typing import List

# Non‑circular imports – these modules do not import ``thuis.main``.
from thuis.classifier import classify, ContentType
from thuis.metadata_fetcher import fetch_metadata
from thuis.scene_namer import build_tv_filename
from typing import Any


def _process_url(url: str, args: Any) -> int:
    """Process a single VRT URL.

    Returns the subprocess exit code (0 on success).  All side‑effects – logging,
    file creation, database updates – remain exactly as in the original
    implementation.
    """
    # Lazy imports to avoid circular dependency on ``thuis.main``.
    from thuis.main import (
        url_parser,
        build_yt_dlp_args,
        _run_ytdlp_with_drm_detection,
    )
    # Import the watchlist helpers directly to avoid circular import
    from thuis.cli.watchlist_helpers import (
        is_season_url,
        expand_season,
        process_watchlist_file,
    )

    # 1. Parse the URL (may raise ValueError which the caller handles).
    vrt_info = url_parser.parse_vrt_url(url)

    # 2. Expand season URLs if needed.
    if is_season_url(vrt_info.url):
        expanded = expand_season(vrt_info.url, args.max_episodes)
        for ep_url in expanded:
            _process_url(ep_url, args)
        return 0

    # 3. Fetch metadata.
    metadata = fetch_metadata(vrt_info.url)

    # 4. Classify the content.
    content_type = classify(vrt_info, metadata)

    # 5. Build the output template.
    if content_type is ContentType.UNKNOWN:
        output_template = "%(title)s.%(ext)s"
    else:
        output_template = build_tv_filename(vrt_info, metadata, content_type)

    # 6. Assemble yt‑dlp arguments.
    ytdlp_args = build_yt_dlp_args(
        url=vrt_info.url,
        output_template=output_template,
        args=args,
        content_type=content_type,
    )

    # 7. Run yt‑dlp (may include DRM detection wrapper).
    exit_code, _ = _run_ytdlp_with_drm_detection(ytdlp_args, args)
    return exit_code


def run_cli(args: Any) -> None:
    """Entry point used by ``thuis.main.main`` after argument parsing.

    Mirrors the original ``main`` flow but isolates the logic in this module.
    """
    # Install SIGINT handler – matches original behaviour.
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit("\nInterrupted by user"))

    # Resolve yt‑dlp binary location once.
    from thuis.main import get_yt_dlp_location
    yt_dlp_path = get_yt_dlp_location(args.yt_dlp_path)
    if not yt_dlp_path:
        print("yt‑dlp binary not found – aborting", file=sys.stderr)
        sys.exit(1)

    # Watchlist handling.
    from thuis.cli.watchlist_helpers import process_watchlist_file
    if args.watchlist:
        process_watchlist_file(args.watchlist, args)
        return

    # Process URLs.
    for url in args.urls:
        try:
            _process_url(url, args)
        except Exception as exc:  # pragma: no cover – defensive
            print(f"Error processing {url}: {exc}", file=sys.stderr)
            continue

    return