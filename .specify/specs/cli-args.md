# CLI Arguments Specification

## Module
`src/thuis/cli/args.py` — argparse builder, used by `main.py`

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `urls` (positional) | str[] | `[]` | One or more VRT MAX URLs |
| `--file FILE` | path | `None` | File with URLs (one per line, `#` comments ignored) |
| `--watchlist FILE [FILE ...]` | path[] | `None` | Watchlist files to process |
| `--now` | flag | `False` | Bypass schedule, process all watchlist entries |
| `--dry-run` | flag | `False` | Print what would be downloaded, do not download |
| `--output-dir DIR` | str | `None` | Output directory (not allowed with `--watchlist`) |
| `--max-episodes N` | int | `None` | Max episodes for season URL expansion |
| `--max-wait SECONDS` | int | `300` | Max wait for subprocess completion |
| `--profile N` | int | `None` | Preferred video profile index (passed to yt-dlp) |
| `--yt-dlp PATH` | path | auto-detect | Path to yt-dlp binary |
| `--yt-dlp-json TEXT` | str | `None` | JSON overrides for yt-dlp args (merged into dict) |
| `--verbose` / `-v` | count | `0` | Log verbosity level |

## Validation Rules
- `--output-dir` **must fail** when used with `--watchlist` (FR-014)
- `--watchlist` **must fail** if no watchlist files given
- `--max-episodes` only meaningful with season URLs
- `--yt-dlp-json` must be valid JSON, merged into default yt-dlp args

## Output
Returns an `argparse.Namespace` with all parsed args.

## Error Handling
- Validation errors printed to stderr, exit code 2
- Missing required files (watchlist, file) printed to stderr, exit code 2
- Invalid JSON for `--yt-dlp-json` → stderr, exit 2