# Implementation Plan: Torrent Category Support for Watchlists and CLI

## Technical Context
- **Language/Framework**: Python 3.10+ (uv, pytest)
- **Key Modules**:
  - `src/thuis/watchlist.py`: Parses watchlist files (`[dir]`, `[schedule]`, now adding `[cat]`).
  - `src/thuis/main.py`: CLI arguments and main execution loop, passing parameters to plugins.
  - `src/thuis/plugins/torrent_uploader.py`: Plugin handling torrent creation and qBittorrent / ext.to upload.
  - `src/thuis/plugins/qbittorrent_client.py`: API wrapper for qBittorrent `add_torrent()`.
- **Testing**: pytest (`pytest`)

## Constitution Check
- Verification-first: Yes, tested via dry-run and direct API calls.
- Concise English logs: Yes.
- No hardcoded paths: Yes.

## Phase 0: Research & Design
- **Watchlist syntax**: `[cat] Media/Tv` parses into `WatchlistFile.default_category` and can be overridden per entry.
- **CLI argument**: `--category` added to `argparse` group, passed via plugin config override.

## Phase 1: Artifacts
- Spec: `specs/004-torrent-category-support/spec.md`
- Plan: `specs/004-torrent-category-support/plan.md`
