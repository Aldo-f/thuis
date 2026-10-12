# Thuis v4 — Architecture Specification

## Overview
Python CLI tool (`thuis.sh`) for downloading VRT MAX content via yt-dlp with optional Widevine DRM decryption via N_m3u8DL-RE + pywidevine.

## Module Layout
```
src/thuis/
├── __init__.py           # package marker
├── main.py               # CLI entry point, arg parsing, GraphQL queries
├── cli/
│   ├── args.py           # argparse builder (all CLI flags)
│   ├── orchestrator.py   # run_cli(): dispatches to watchlist or URL processing
│   ├── runner.py         # low-level subprocess execution of yt-dlp
│   └── watchlist_helpers.py  # watchlist entry processing, season URL expansion
├── classifier.py         # ContentType enum + classify() function
├── config.py             # YAML/env config loader, get_config()
├── url_parser.py         # parse_vrt_url() → VRTInfo dataclass
├── metadata_fetcher.py   # fetch_metadata(url) → metadata dict
├── scene_namer.py        # build_tv_filename() → output template string
├── show_resolver.py      # resolve_show_id_from_url() — reverse-geo via GraphQL
├── filename_parser.py    # parse SceneFilename → ShowName, Season, Episode
├── normalizer.py         # filename normalization (special chars, unicode)
├── codec_detector.py     # detect_highest_profile() from yt-dlp JSON
├── codec_map.py          # CODEC_PRIORITIES + resolution preference
├── probe.py              # ffprobe wrapper → video/audio stream info
├── transcoder.py         # post-download: merge, normalize audio, extract
├── watchlist.py          # parser, scheduler, state DB (SQLite)
├── doctor.py             # doctor/doctor --fix CLI subcommand
├── cdm.py                # CDM auto-fetch + validation (.wvd)
├── drm_decrypt.py        # core decryption pipeline (PSSH → keys → N_m3u8DL-RE)
└── extract_cdm.py        # manual CDM extraction helper (Frida)
```

## Import Flow (anti-circular pattern)
1. `thuis.sh` → `python -m thuis.main`
2. `main.py` parses args via `cli.args` → calls `cli.orchestrator.run_cli(args)`
3. `orchestrator.py` lazy-imports from `main.py` inside functions to avoid circular deps:
   - `url_parser`, `build_yt_dlp_args`, `_run_ytdlp_with_drm_detection`
4. `watchlist_helpers.py` lazy-imports `watchlist.py` and `thuis.main` functions
5. `drm_decrypt.py` lazy-imports `thuis.cdm` and `thuis.config`

## Data Flow
```
URL ──→ url_parser.parse_vrt_url() ──→ VRTInfo(show_slug, season, episode)
  ──→ metadata_fetcher.fetch_metadata() ──→ metadata dict (title, year, etc.)
  ──→ classifier.classify() ──→ ContentType (TV_SHOW, MOVIE, PODCAST, etc.)
  ──→ scene_namer.build_tv_filename() ──→ output template (e.g. /path/Thuis.S32E6120.1080p.WEB-DL.AAC.x264.mp4)
  ──→ main.build_yt_dlp_args() ──→ yt-dlp CLI args list
  ──→ orchestrator._run_ytdlp_with_drm_detection() ──→ subprocess.run()
  │    ↳ Detect DRM: if yt-dlp fails with "DRM" → drm_decrypt.decrypt_drm_content()
  │       ↳ drm_decrypt: PSSH → pywidevine license → N_m3u8DL-RE --decryption-engine mp4decrypt
  ├──→ watchlist.py (if --watchlist flag) ──→ parse → schedule check → state DB → same flow per URL
  └──→ cli.runner.run_ytdlp() ──→ final subprocess call
```

## State / Config
- **SQLite DB**: `~/.thuis/state.db` — watchlist entries, downloaded files, episode progress, episode cache
- **CDM cache**: `~/.thuis/cdm/widevine_l3_android.wvd` (or `WVD_CDM_PATH`)
- **Config**: `~/.thuis.config.yaml` (loaded first if exists) → env vars → `.env` → defaults
- **Logs**: `./logs/YYYY-MM-DD.log` (per-day file), stdout for interactive
- **Media output**: Default `./media/`, override via `--output-dir` or watchlist first-line

## CLI Entry Points
```
thuis.sh [URLS...] [--watchlist FILE] [--dry-run] [--output-dir DIR] [--file F]
thuis.sh --watchlist FILE [--now] -- watchlist mode
thuis.sh doctor [--fix]           -- diagnose DRM pipeline readiness
```

## Cron / Watchlist Runner
- `scripts/watchlist-runner.sh` — wrapper that ensures cron entry exists, runs thuis.sh with all watchlist files
- Cron line format: `0 * * * * run-serial.sh thuis-watchlist --max-wait=7200 -- REPO_DIR/scripts/watchlist-runner.sh`

## Testing Strategy
- `pytest` with `conftest.py` fixtures for temp dirs, mocked yt-dlp
- Unit tests per module (`tests/` + `tests/thuis/`)
- Integration tests with mocked subprocess (`tests/test_integration.py`)
- All existing tests must pass: `pytest tests/ -v`