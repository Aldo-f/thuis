"""Command‑line argument parser for the thuis CLI.

All options are defined in the original ``thuis.main`` script; this module simply
extracts the construction of the ``argparse.ArgumentParser`` so that the CLI
logic can be tested and reused independently.
"""

import argparse
import os
import sys
from pathlib import Path

# The default output directory mirrors the historic behaviour: ``media`` or the
# ``OUTPUT_DIR`` environment variable if set.
DEFAULT_OUTPUT_DIR = os.getenv("OUTPUT_DIR", "media")


def build_parser() -> argparse.ArgumentParser:
    """Create and return the ``argparse`` parser used by ``thuis.main``.

    The parser is identical to the one historically built inside ``main()`` –
    groups for download options, transcoding, batch processing and watch‑list
    handling are preserved verbatim.
    """
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
    g_dl.add_argument("--force", action="store_true", help="Ignore DB records; download even if DB says file exists, but only if file is missing.")
    g_dl.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR), help="Directory to save downloaded files (default: media or OUTPUT_DIR env)")
    g_dl.add_argument("--max-episodes", type=int, default=None, help="Maximum number of episodes to process per season URL")
    g_dl.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None, help="Enable console logging at specified level (default: file only)")
    g_dl.add_argument("--key-file", type=Path, default=None, help="JSON file with KID:KEY pairs for DRM decryption (alternative to CDM)")
    g_dl.add_argument("--key", action="append", default=[], metavar="KID:KEY", help="Direct KID:KEY pair for DRM decryption (repeatable, overrides CDM)")
    g_dl.add_argument("--key-provider", type=str, choices=["cdm", "file", "cli"], default="cdm", help="Key source: cdm (pywidevine), file (--key-file), cli (--key)")

    # Transcode options
    g_tr = parser.add_argument_group("transcode options")
    g_tr.add_argument("--transcode", type=str, default=None, help="Target resolution for transcoding (e.g., '720p', '1080p'). If set, transcode downloaded files to this resolution.")
    g_tr.add_argument("--allow-upscale", action="store_true", help="Allow upscaling lower resolutions to target (e.g., 540p -\u003e 720p)")
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

    return parser
