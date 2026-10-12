# Core Downloader Specification

## Module
`src/thuis/main.py` — Main entry point and core download logic

## Responsibilities
1. Parse CLI arguments (via `argparse`)
2. Load configuration (`config.py`)
3. Set up logging (`setup_logging`)
4. Handle subcommands (`normalize`, `doctor`, `watchlist`)
5. Resolve and expand URLs (season → episodes, show → seasons)
6. Coordinate the download pipeline:
   - Metadata fetch (`metadata_fetcher.py`)
   - Classification (`classifier.py`)
   - DRM detection & decryption (`drm_decrypt.py`)
   - Scene naming (`scene_namer.py`)
   - Download via yt-dlp (`_run_ytdlp_with_drm_detection`)
   - Record in state DB (`watchlist.py`)
   - Transcoding (`transcoder.py`)

## Key Functions

### `main()`
- Intercepts `normalize`, `doctor`, `watchlist` subcommands.
- Configures logging.
- Validates `--output-dir`.
- Collects and expands URLs.
- Iterates over URLs and calls the processing loop.

### `_run_ytdlp_with_drm_detection(args)`
- Wraps yt-dlp execution in a PTY (Pseudo-Terminal).
- Captures output for DRM detection (searches for "This video is DRM protected").
- Returns `(exit_code, output_text)`.

### `fetch_season_episodes(url)` / `fetch_all_seasons(url)`
- Uses GraphQL API to find episodes/seasons.
- Falls back to `_guess_episode_urls` (HEAD probing) if GraphQL fails.
- Caches results for 24h in `state.db`.

### `build_yt_dlp_args(urls, ...)`
- Constructs the command line for yt-dlp.
- Handles credentials, output templates, and format selection.
- Supports audio-only mode for podcasts.

## Dependencies
- `yt-dlp` (custom fork recommended for better metadata)
- `ffmpeg` / `ffprobe` (for probing and transcoding)
- `sqlite3` (for state tracking)

## Tests
- `tests/test_integration.py` — verifies the full pipeline with mocked yt-dlp.
- `tests/test_main.py` — unit tests for helper functions.
- `tests/test_graphql.py` — tests VRT API interaction.