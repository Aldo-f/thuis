# CLI Orchestrator Specification

## Module
`src/thuis/cli/orchestrator.py`

## Function
```python
def run_cli(args: Namespace) -> None:
    """
    Main orchestrator called by main.py after argument parsing.
    Dispatches to watchlist processing or direct URL processing.
    """
```

## Logic
1. Install SIGINT handler (clean exit on Ctrl+C)
2. Resolve yt-dlp binary location via `main.get_yt_dlp_location(args.yt_dlp_path)`
3. If `args.watchlist`:
   - Call `watchlist_helpers.process_watchlist_file(args.watchlist, args)`
   - Return
4. For each URL in `args.urls`:
   - Call `_process_url(url, args)` in try/except
   - On error: log to stderr, continue to next URL

## `_process_url(url, args)` — internal helper
1. Parse URL: `vrt_info = url_parser.parse_vrt_url(url)`
2. If `is_season_url(vrt_info.url)`:
   - Expand: `expanded = expand_season(vrt_info.url, args.max_episodes)`
   - Recursively call `_process_url` for each episode URL
   - Return 0
3. Fetch metadata: `metadata = fetch_metadata(vrt_info.url)`
4. Classify: `content_type = classify(vrt_info, metadata)`
5. Build output template:
   - If UNKNOWN: `"%(title)s.%(ext)s"`
   - Else: `build_tv_filename(vrt_info, metadata, content_type)`
6. Assemble yt-dlp args: `ytdlp_args = build_yt_dlp_args(url, output_template, args, content_type)`
7. Run: `exit_code, _ = _run_ytdlp_with_drm_detection(ytdlp_args, args)`
8. Return exit_code

## Imports (lazy to avoid circular)
- From `thuis.main`: `url_parser`, `build_yt_dlp_args`, `_run_ytdlp_with_drm_detection`
- From `thuis.cli.watchlist_helpers`: `is_season_url`, `expand_season`, `process_watchlist_file`
- From `thuis.classifier`: `classify`, `ContentType`
- From `thuis.metadata_fetcher`: `fetch_metadata`
- From `thuis.scene_namer`: `build_tv_filename`

## Tests
- `tests/test_integration.py` — tests full flow with mocked yt-dlp