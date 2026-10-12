---
slug: thuis-plugin-system
status: approved
intent: clear
review_required: true
plan_path: .omo/plans/thuis-plugin-system.md
plan_sha256: null
review_round_id: null
pending-action: execute .omo/plans/thuis-plugin-system.md
review:
  momus:
    status: null
    workspace_root: null
    runtime_home: null
    target: .omo/plans/thuis-plugin-system.md
    round_id: null
    plan_sha256: null
    launch_id: null
    session: null
    result: null
  independent:
    status: null
    workspace_root: null
    runtime_home: null
    target: .omo/plans/thuis-plugin-system.md
    round_id: null
    plan_sha256: null
    launch_id: null
    session: null
    result: null
approach: Entry-point + config-driven hybrid plugin architecture with a PostprocessContext dataclass passed to plugins. Torrent upload plugin as the first concrete example, with metadata enrichment (TMDB API for IMDb, images via TMDB, encoding from existing metadata). Manual subcommand + optional post-download hook.
---

# Draft: thuis-plugin-system

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->

| plugin-host | Entry-point + config-driven plugin registry with PostprocessContext | active | src/thuis/plugin_host.py (new) |
| torrent-plugin | Torrent upload plugin with metadata enrichment (TMDB, images, encoding) | active | src/thuis/plugins/torrent_uploader.py (new) |
| metadata-enricher | TMDB lookup + image fetch for torrent descriptions | active | src/thuis/plugins/metadata_enricher.py (new) |
| cli-integration | --upload subcommand + optional post-download hook flag | active | src/thuis/cli/args.py, main.py |
| config-schema | plugins: section in config.yaml with enable/disable/options | active | config.yaml, src/thuis/config.py |
| tests | Unit + integration tests for plugin system and torrent uploader | active | tests/test_plugin_host.py, tests/test_torrent_uploader.py |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->

| Plugin discovery mechanism | importlib.metadata entry_points(group="thuis.postprocess") + config.yaml enable/disable | Standard Python plugin pattern (pytest, click-plugins); allows pip-installable plugins + in-tree examples; reversible via config | Yes |
| Torrent upload trigger | Manual subcommand `thuis torrent-upload <dir>` + optional `--auto-upload` flag for post-download hook | User explicitly said "bestaande files uploaden" (upload existing files) -> batch operation on existing files | Yes |
| Torrent library | python-libtorrent (libtorrent4) for .torrent creation | Most robust, supports multi-file torrents, tracker announce; already used by similar tools | Yes |
| Metadata source | TMDB API v3 (themoviedb.org) with user-provided API key | Free tier (10k req/day), comprehensive metadata, images; OMDb requires paid for commercial use | Yes |
| Image source | TMDB poster API (highest resolution available) | Consistent with metadata source; fallback to placeholder | Yes |
| Plugin interface | Single `postprocess(ctx: PostprocessContext) -> bool` function per plugin | Simple, matches existing drm_decrypt pattern; plugins return True on success | Yes |
| Plugin config location | `plugins:` section in config.yaml + config.local.yaml | Follows existing config pattern; per-plugin options under `plugins.<name>.options` | Yes |
| Torrent tracker list | Configurable via `plugins.torrent_uploader.trackers` in config.yaml | Allows user to specify their preferred trackers; default to public trackers | Yes |
| Error handling | Plugins wrapped in try/except; failures logged but never crash the host | Matches existing drm_decrypt pattern; graceful degradation | Yes |

## Findings (cited - path:lines)
<!-- ID | Finding | Evidence path | Relevance -->

| F1 | Existing optional plugin pattern: drm_decrypt imported via try/except ImportError in main.py:128-132 | src/thuis/main.py:128-132 | Pattern to follow for new plugins |
| F2 | Config system: config.yaml + config.local.yaml + env overrides in src/thuis/config.py | src/thuis/config.py | Extend with plugins: section |
| F3 | Metadata available: series, season, episode, height, vcodec, acodec, ext, title from metadata_fetcher.py | src/thuis/metadata_fetcher.py:48-127 | All needed for torrent description |
| F4 | Scene naming pipeline: scene_namer.py builds filenames with show, season, episode, resolution, codecs | src/thuis/scene_namer.py | Can reuse for torrent naming |
| F5 | WatchlistDB tracks downloaded files with URL, filename, output_dir | src/thuis/watchlist.py:333-517 | Can query for files to upload |
| F6 | CLI structure: argparse in main.py with subcommands (doctor, normalize) | src/thuis/main.py:1301-1440 | Add torrent-upload subcommand |
| F7 | Entry-point plugin pattern recommended by Python packaging guide + used by pytest, click-plugins | librarian research | Best practice for discoverable plugins |
| F8 | python-libtorrent supports creating .torrent files with multi-file, trackers, web seeds | librarian research | Library for torrent creation |
| F9 | TMDB API v3 provides comprehensive movie/TV metadata + images with free tier | librarian research | Metadata enrichment source |

## Decisions (with rationale)
<!-- ID | Decision | Rationale | Evidence -->

| D1 | Entry-point + config-driven hybrid plugin architecture | Standard Python pattern (importlib.metadata) + user control via config.yaml; allows both pip-installable and in-tree plugins | F7, existing config pattern |
| D2 | PostprocessContext dataclass with filepath, metadata, db reference | Single clean interface for all plugins; matches existing metadata flow | F3, F5, F6 |
| D3 | Manual subcommand `thuis torrent-upload <dir>` as primary trigger | User said "bestaande files uploaden" (upload existing files) -> batch operation on existing files | User clarification |
| D4 | Optional `--auto-upload` flag for post-download hook | Allows auto-upload after successful download; disabled by default | User control |
| D5 | python-libtorrent for .torrent creation | Robust, supports multi-file, trackers, web seeds; widely used | F8 |
| D6 | TMDB API v3 for metadata + images | Free tier, comprehensive, includes images; user provides API key in config | F9 |
| D7 | Plugins return bool (success/failure) | Simple contract; host can log failures and continue | Matches drm_decrypt pattern |
| D8 | Plugin config under `plugins:` in config.yaml | Consistent with existing config; per-plugin enable/disable/options | F2 |

## Scope IN
- Plugin host architecture: entry-point discovery, config-driven enable/disable, PostprocessContext
- Plugin interface: single postprocess(ctx) function signature
- Torrent upload plugin: creates .torrent files, uploads to configured trackers, enriches with TMDB metadata
- Metadata enricher: TMDB API lookup for series/season/episode, fetches poster images
- CLI integration: `thuis torrent-upload <dir>` subcommand + `--auto-upload` flag
- Config schema: `plugins:` section with per-plugin options
- Tests: unit tests for plugin host, torrent uploader, metadata enricher
- Documentation: plugin development guide in docs/

## Scope OUT (Must NOT have)
- Hardcoded torrent tracker list (configurable via config)
- Hardcoded TMDB API key (user-provided via config/env)
- Automatic upload without explicit `--auto-upload` flag
- Modifications to existing download pipeline (only add optional hook)
- External plugin packaging (user handles pip install for external plugins)
- GUI or web interface (CLI only)
- Support for non-torrent plugins beyond the example (architecture supports any postprocess plugin)

## Open questions
None - all forks resolved via adopted defaults or user clarification.

## Approval gate
status: awaiting-approval
approach: Entry-point + config-driven hybrid plugin architecture. Torrent upload plugin as concrete example with TMDB metadata enrichment. Manual subcommand primary, optional post-download hook.
next: Write .omo/plans/thuis-plugin-system.md after explicit user okay.
