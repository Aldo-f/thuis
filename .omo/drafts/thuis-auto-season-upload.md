---
slug: thuis-auto-season-upload
status: draft
intent: clear
review_required: true
plan_path: .omo/plans/thuis-auto-season-upload.md
plan_sha256: null
review_round_id: null
pending-action: write .omo/plans/thuis-auto-season-upload.md after explicit user okay
review:
  momus:
    status: null
    workspace_root: null
    runtime_home: null
    target: .omo/plans/thuis-auto-season-upload.md
    round_id: null
    plan_sha256: null
    launch_id: null
    session: null
    result: null
  independent:
    status: null
    workspace_root: null
    runtime_home: null
    target: .omo/plans/thuis-auto-season-upload.md
    round_id: null
    plan_sha256: null
    launch_id: null
    session: null
    result: null
approach: TMDB-based season completion detection + multi-file season torrent creation + Tribler REST API upload for anonymous seeding. Triggered after each download, checks TMDB for expected episode count, compares against local files, creates multi-file season torrent when complete, submits to Tribler REST API with anonymity hops > 0.
---
# Draft: thuis-auto-season-upload

## Components (topology ledger)

| id | outcome (one line) | status: active|deferred | evidence path |
|----|---------------------|----------------------|---------------|
| tmdb-season-detection | TMDBClient.get_season_details() + get_all_seasons_episode_counts() for Thuis (ID 14506) | active | src/thuis/plugins/metadata_enricher.py |
| season-completion | Check downloaded episodes vs TMDB expected count per season | active | src/thuis/plugins/season_detector.py (new) |
| season-torrent | Multi-file torrent from all episode files in season | active | src/thuis/plugins/season_torrent.py (new) |
| tribler-client | REST API client for Tribler PUT /downloads with anonymity hops | active | src/thuis/plugins/tribler_client.py (new) |
| auto-trigger | Post-download hook checks season completion, triggers torrent + upload | active | src/thuis/main.py (modify) |
| cli-commands | thuis season-status, thuis season-upload, thuis season-upload-all | active | src/thuis/cli/args.py, src/thuis/main.py |

## Open assumptions (announced defaults)

| assumption | adopted default | rationale | reversible? |
|------------|-----------------|-----------|-------------|
| TMDB Show ID | 14506 (Thuis) hardcoded | Thuis is fixed show; user won't change | Yes |
| Episode file pattern | Thuis.S{XX}E{YYYY}.*.mp4/mkv | Matches existing download structure | Yes |
| Season complete threshold | 100% episodes present | Strict: all TMDB episodes must exist | Yes |
| Tribler API port | 8085 (env CORE_API_PORT) | Standard Tribler core port | Yes |
| Tribler anonymity hops | 3 (max) | Maximum anonymity for upload | Yes |
| Tribler safe_seeding | true | Prevent IP leaks | Yes |
| Season directory | Flat structure (current) | Matches existing download dir | Yes |
| Missing episodes | Logged but don't block | Season 1 has 13 missing eps | Yes |

## Findings (cited - path:lines)

| ID | Finding | Evidence path | Relevance |
|----|---------|---------------|-----------|
| F1 | Thuis TMDB ID = 14506 | TMDB website | Show identification |
| F2 | Season 1 = 90 episodes | TMDB /tv/14506/season/1 | Episode count source |
| F3 | Season 32 in progress | TMDB /tv/14506/season/32 | Current season tracking |
| F4 | Episode naming: Thuis.S{XX}E{YYYY} | /mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Thuis | File pattern matching |
| F5 | Flat directory structure | Real data scan | No season subdirs |
| F6 | Season 1 has 13 missing episodes | Real data scan | Not 100% complete |
| F7 | Tribler PUT /downloads endpoint | tribler-bash add_torrent function | Anonymous upload API |
| F8 | Tribler REST API port 8085 | tribler-bash, docs | API connection |
| F9 | Tribler anonymity hops 0-3 | tribler-bash hops command | Anonymity control |

## Decisions (with rationale)

| ID | Decision | Rationale | Evidence |
|----|----------|-----------|----------|
| D1 | TMDB as source of truth for episode counts | Authoritative, includes specials, accurate | F1, F2, F3 |
| D2 | Check completion after each download | Near-real-time, no separate scheduler | Existing --auto-upload hook |
| D3 | Season torrent = multi-file libtorrent | Single .torrent for whole season | libtorrent supports multi-file |
| D4 | Tribler for anonymous upload | Tor-like onion routing, hidden seeding | F7, F8, F9 |
| D5 | Anonymity hops = 3 (max) | Maximum IP protection | F9 |
| D6 | Safe_seeding = true | Prevents IP leaks in swarm | Tribler best practice |
| D7 | Flat file structure for torrent | Matches current download dir | F4, F5 |
| D8 | Missing episodes don't block | Season 1 missing 13 eps | F6 |
| D9 | Per-season poster upload | Reuses existing ImgBB integration | Existing code |

## Scope IN

- TMDBClient.get_season_details(show_id, season) -> episode_count, episodes[]
- TMDBClient.get_all_seasons_episode_counts(show_id) -> {season: count}
- SeasonDetector.is_season_complete(download_dir, show_id, season) -> (bool, missing[], expected)
- SeasonTorrent.create_season_torrent(episode_files, trackers, piece_size) -> Path
- TriblerClient.upload_torrent(torrent_path, anon_hops, safe_seeding) -> success
- Post-download hook: after each download, check if season complete -> create torrent -> upload
- CLI: thuis season-status [--season N], thuis season-upload [--season N], thuis season-upload-all
- Config: tribler section with api_port, api_key, anon_hops, safe_seeding
- Per-season poster upload to ImgBB, embed in torrent description

## Scope OUT (Must NOT have)

- No hardcoded TMDB show ID beyond Thuis (14506)
- No hardcoded Tribler API key (read from config/env)
- No hardcoded Tribler port (default 8085, configurable)
- No automatic upload without explicit config enable
- No GUI/web interface
- No modification of existing download logic (only add hook)
- No support for shows other than Thuis (architecture allows but not required)
- No season pack download (only upload existing files)
- No external Tribler installation (assume pre-installed)

## Open questions

None - all forks resolved via adopted defaults or user clarification.

## Approval gate

status: awaiting-approval
approach: TMDB season detection + multi-file season torrent + Tribler anonymous upload. Triggered post-download.
next: Write .omo/plans/thuis-auto-season-upload.md after explicit user okay.