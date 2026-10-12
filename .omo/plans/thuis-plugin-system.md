# thuis-plugin-system - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** A plugin system for thuis that lets you extend functionality (like uploading downloaded files to torrent sites with full metadata). Includes a working torrent upload plugin that creates .torrent files with rich descriptions (encoding, IMDb info, episode details, images).

**Why this approach:** Entry-point based plugin discovery (Python standard) + config-driven enable/disable gives you both pip-installable plugins and simple in-tree examples. Single postprocess() interface keeps plugins simple. Manual subcommand for existing files + optional auto-hook for new downloads covers both use cases.

**What it will NOT do:** No hardcoded tracker lists (you configure them), no hardcoded API keys (you provide TMDB key), no automatic uploads without explicit flag, no changes to existing download flow (only adds optional hook).

**Effort:** Large
**Risk:** Medium - External dependencies (python-libtorrent, TMDB API), new architecture
**Decisions to sanity-check:** Entry-point + config hybrid for plugins, python-libtorrent for torrent creation, TMDB API for metadata, manual subcommand as primary trigger

Your next move: Approve and run `/start-work thuis-plugin-system`, or request a high-accuracy review first. Full execution detail follows below.

---

> TL;DR (machine): Large effort, Medium risk, Plugin system + torrent upload plugin with TMDB enrichment

## Scope
### Must have
- Plugin host architecture with entry-point discovery and config-driven enable/disable
- PostprocessContext dataclass with filepath, metadata, db reference passed to plugins
- Single postprocess(ctx) -> bool plugin interface
- Torrent upload plugin: creates .torrent files, enriches with TMDB metadata (title, year, season, episode, encoding, images)
- CLI: `thuis torrent-upload <dir>` subcommand for batch upload of existing files
- CLI: `--auto-upload` flag to enable post-download hook
- Config: `plugins:` section in config.yaml with per-plugin enable/options
- python-libtorrent integration for .torrent creation
- TMDB API v3 integration for metadata + image fetching
- Unit tests for plugin host, torrent uploader, metadata enricher
- Integration test for full torrent upload flow
- Documentation: plugin development guide

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No hardcoded torrent tracker URLs (must be configurable via config)
- No hardcoded TMDB API key (must come from config.local.yaml or env)
- No automatic torrent upload without explicit `--auto-upload` flag
- No modifications to existing download pipeline logic (only add optional hook call)
- No GUI or web interface (CLI only)
- No support for plugins beyond the postprocess hook (architecture allows expansion but not required)
- No external plugin packaging (user handles pip install for their own plugins)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest
- Evidence: .omo/evidence/thuis-plugin-system/

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | None | 2,3,4 | 5,6,7,8 |
| 2 | 1 | 3,4 | 5,6,7,8 |
| 3 | 1,2 | 4 | 5,6,7,8 |
| 4 | 1,2,3 | None | 5,6,7,8 |
| 5 | 1 | 6 | 7,8 |
| 6 | 1,5 | 7 | 8 |
| 7 | 1,5,6 | 8 | None |
| 8 | 1,5,6,7 | None | None |
| 9 | 1,2,3,4 | None | 10,11 |
| 10 | 9 | 11 | None |
| 11 | 9,10 | None | None |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Create plugin host architecture with PostprocessContext and entry-point discovery
  What to do / Must NOT do: Create src/thuis/plugin_host.py with PluginManager class, PostprocessContext dataclass, load_entry_point_plugins() function. Must NOT hardcode plugin paths or names. Must NOT modify existing modules yet.
  Parallelization: Wave 1 | Blocked by: None | Blocks: 2,3,4
  References (executor has NO interview context - be exhaustive): src/thuis/main.py:128-132 (drm_decrypt pattern), src/thuis/config.py (config pattern), librarian research on entry_points
  Acceptance criteria (agent-executable): pytest tests/test_plugin_host.py passes; importlib.metadata.entry_points(group="thuis.postprocess") returns empty list when no plugins installed
  QA scenarios (name the exact tool + invocation): happy: pytest tests/test_plugin_host.py -v; failure: pytest tests/test_plugin_host.py -v with broken plugin; Evidence .omo/evidence/thuis-plugin-system/task-1-plugin-host.<ext>
  Commit: Y | feat(plugin): Add plugin host architecture with entry-point discovery

- [x] 2. Add plugins section to config schema and loader
  What to do / Must NOT do: Extend src/thuis/config.py to support plugins: section in config.yaml. Add plugins key to default config. Must NOT break existing config loading.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 3,4
  References: src/thuis/config.py:21-61, config.yaml
  Acceptance criteria: config.get("plugins", {}) returns {} when no plugins section; config with plugins: section loads correctly
  QA scenarios: happy: python -c "from thuis.config import get_config; print(get_config())"; failure: load config with invalid YAML; Evidence .omo/evidence/thuis-plugin-system/task-2-config-schema.<ext>
  Commit: Y | feat(config): Add plugins section to config schema

- [x] 3. Create PostprocessContext dataclass with all required fields
  What to do / Must NOT do: Create PostprocessContext in src/thuis/plugin_host.py with fields: filepath (Path), metadata (dict), output_dir (Path), db (WatchlistDB), dry_run (bool). Must NOT include sensitive data like credentials.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 4
  References: src/thuis/metadata_fetcher.py:109-120 (metadata fields), src/thuis/watchlist.py:333-380 (WatchlistDB)
  Acceptance criteria: PostprocessContext instantiates with all fields; dataclass(frozen=True)
  QA scenarios: happy: python -c "from thuis.plugin_host import PostprocessContext; ctx = PostprocessContext(...); print(ctx)"; failure: missing required field; Evidence .omo/evidence/thuis-plugin-system/task-3-postprocess-context.<ext>
  Commit: Y | feat(plugin): Add PostprocessContext dataclass

- [x] 4. Implement plugin loading and execution in plugin host
  What to do / Must NOT do: Implement load_plugins() and run_plugins(ctx) in src/thuis/plugin_host.py. load_plugins() discovers via entry_points and filters by config enabled list. run_plugins() calls each plugin's postprocess(ctx) wrapped in try/except. Must NOT crash on plugin failure.
  Parallelization: Wave 1 | Blocked by: 1,2,3 | Blocks: None
  References: src/thuis/main.py:128-132 (try/except pattern), librarian research on entry_points
  Acceptance criteria: run_plugins(ctx) returns dict of plugin_name -> success bool; failures logged but not raised
  QA scenarios: happy: run_plugins with working plugin returns {"plugin_name": True}; failure: run_plugins with broken plugin returns {"plugin_name": False} and logs error; Evidence .omo/evidence/thuis-plugin-system/task-4-plugin-execution.<ext>
  Commit: Y | feat(plugin): Implement plugin loading and execution

- [x] 5. Create metadata enricher module for TMDB lookups
  What to do / Must NOT do: Create src/thuis/plugins/metadata_enricher.py with TMDBClient class. Methods: lookup_show(series, season, episode) -> dict, lookup_movie(title, year) -> dict, fetch_poster_image(series/movie) -> bytes. Must NOT hardcode API key. Must NOT fail on network errors.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 6
  References: librarian research on TMDB API v3
  Acceptance criteria: TMDBClient instantiates with api_key; lookup_show returns dict with title, year, overview, poster_path; fetch_poster_image returns JPEG bytes
  QA scenarios: happy: lookup_show("Thuis", 31, 6108) returns metadata; failure: lookup_show with invalid API key returns None; Evidence .omo/evidence/thuis-plugin-system/task-5-metadata-enricher.<ext>
  Commit: Y | feat(plugin): Add TMDB metadata enricher

- [x] 6. Create torrent uploader plugin with python-libtorrent
  What to do / Must NOT do: Create src/thuis/plugins/torrent_uploader.py with TorrentUploader class. Methods: create_torrent(filepath, trackers, piece_size) -> Path, upload_to_trackers(torrent_path, trackers) -> bool. Uses python-libtorrent. Must NOT hardcode trackers. Must NOT hardcode piece size.
  Parallelization: Wave 2 | Blocked by: 1,5 | Blocks: 7
  References: librarian research on python-libtorrent, src/thuis/scene_namer.py (naming pattern)
  Acceptance criteria: create_torrent generates valid .torrent file; upload_to_trackers returns True on success
  QA scenarios: happy: create_torrent on test file generates .torrent; failure: create_torrent on non-existent file raises FileNotFoundError; Evidence .omo/evidence/thuis-plugin-system/task-6-torrent-uploader.<ext>
  Commit: Y | feat(plugin): Add torrent uploader with python-libtorrent

- [x] 7. Integrate metadata enricher and torrent uploader into plugin
  What to do / Must NOT do: Create postprocess(ctx) function in src/thuis/plugins/torrent_uploader.py that: 1) enriches metadata via TMDBClient, 2) creates torrent via TorrentUploader, 3) builds description with all info. Must NOT upload without --auto-upload or explicit call.
  Parallelization: Wave 2 | Blocked by: 1,5,6 | Blocks: 8
  References: src/thuis/metadata_fetcher.py:109-120 (existing metadata), src/thuis/scene_namer.py (naming)
  Acceptance criteria: postprocess(ctx) returns True; generates .torrent file with description containing series, season, episode, resolution, codecs, TMDB info
  QA scenarios: happy: postprocess on test file generates torrent with metadata; failure: postprocess with missing TMDB data uses fallback; Evidence .omo/evidence/thuis-plugin-system/task-7-plugin-integration.<ext>
  Commit: Y | feat(plugin): Integrate enricher and uploader into torrent plugin

- [x] 8. Register torrent plugin via entry point in pyproject.toml
  What to do / Must NOT do: Add [project.entry-points."thuis.postprocess"] section to pyproject.toml with torrent_uploader = "thuis.plugins.torrent_uploader:postprocess". Must NOT add other plugins without approval.
  Parallelization: Wave 2 | Blocked by: 1,5,6,7 | Blocks: None
  References: pyproject.toml, librarian research on entry_points
  Acceptance criteria: entry_points(group="thuis.postprocess") returns torrent_uploader
  QA scenarios: happy: importlib.metadata.entry_points(group="thuis.postprocess") lists torrent_uploader; failure: invalid entry point format; Evidence .omo/evidence/thuis-plugin-system/task-8-entry-point.<ext>
  Commit: Y | build: Register torrent plugin entry point

- [x] 9. Add torrent-upload CLI subcommand to args.py
  What to do / Must NOT do: Add torrent-upload subcommand to src/thuis/cli/args.py with arguments: directory (Path, required), --dry-run, --auto-upload, --trackers (list), --tmdb-key. Must NOT modify existing subcommands.
  Parallelization: Wave 3 | Blocked by: 1,2,3,4 | Blocks: 10,11
  References: src/thuis/cli/args.py, src/thuis/main.py:1359-1372 (doctor subcommand pattern)
  Acceptance criteria: --help shows torrent-upload subcommand; parser accepts all arguments
  QA scenarios: happy: ./thuis.sh torrent-upload --help; failure: ./thuis.sh torrent-upload without directory shows error; Evidence .omo/evidence/thuis-plugin-system/task-9-cli-subcommand.<ext>
  Commit: Y | feat(cli): Add torrent-upload subcommand

- [x] 10. Implement torrent-upload subcommand handler in main.py
  What to do / Must NOT do: Add torrent_upload_subcommand() in src/thuis/main.py that: 1) parses args, 2) scans directory for video files, 3) builds PostprocessContext for each, 4) calls run_plugins(ctx). Must NOT upload without user confirmation in dry-run mode.
  Parallelization: Wave 3 | Blocked by: 9 | Blocks: 11
  References: src/thuis/main.py:1359-1372 (doctor pattern), src/thuis/main.py:1515-2039 (download loop pattern)
  Acceptance criteria: --dry-run shows what would be uploaded without uploading; real run creates .torrent files
  QA scenarios: happy: ./thuis.sh torrent-upload --dry-run /test/media shows files; failure: ./thuis.sh torrent-upload /nonexistent shows error; Evidence .omo/evidence/thuis-plugin-system/task-10-subcommand-handler.<ext>
  Commit: Y | feat(cli): Implement torrent-upload subcommand handler

- [x] 11. Add optional post-download hook for auto-upload
  What to do / Must NOT do: Modify download pipeline in src/thuis/main.py to call run_plugins(ctx) after successful download if --auto-upload flag is set. Must NOT slow down downloads. Must NOT upload on failure.
  Parallelization: Wave 3 | Blocked by: 1,2,3,4,9,10 | Blocks: None
  References: src/thuis/main.py:1515-2039 (download loop), src/thuis/main.py:1956-1963 (download success handling)
  Acceptance criteria: --auto-upload triggers plugin after download; without --auto-upload, no plugin call
  QA scenarios: happy: ./thuis.sh --auto-upload <url> triggers upload; failure: ./thuis.sh <url> does not trigger upload; Evidence .omo/evidence/thuis-plugin-system/task-11-auto-upload-hook.<ext>
  Commit: Y | feat(cli): Add optional post-download auto-upload hook

- [x] 12. Add plugins section to config.yaml with example
  What to do / Must NOT do: Add plugins: section to config.yaml with torrent_uploader enabled and example trackers/tmdb_key. Must NOT commit actual API keys.
  Parallelization: Wave 4 | Blocked by: 2 | Blocks: None
  References: config.yaml
  Acceptance criteria: config.yaml has plugins: section with torrent_uploader example
  QA scenarios: happy: config loads with plugins section; failure: invalid YAML in plugins section; Evidence .omo/evidence/thuis-plugin-system/task-12-config-example.<ext>
  Commit: Y | docs(config): Add plugins section to config.yaml

- [x] 13. Write unit tests for plugin host
  What to do / Must NOT do: Create tests/test_plugin_host.py with tests for PluginManager, PostprocessContext, load_plugins, run_plugins. Must NOT test external plugins.
  Parallelization: Wave 4 | Blocked by: 1,2,3,4 | Blocks: None
  References: tests/conftest.py, tests/test_watchlist.py
  Acceptance criteria: pytest tests/test_plugin_host.py -v passes
  QA scenarios: happy: all tests pass; failure: tests fail on broken plugin; Evidence .omo/evidence/thuis-plugin-system/task-13-plugin-host-tests.<ext>
  Commit: Y | test(plugin): Add unit tests for plugin host

- [x] 14. Write unit tests for metadata enricher
  What to do / Must NOT do: Create tests/test_metadata_enricher.py with mocked TMDB API responses. Must NOT make real API calls in tests.
  Parallelization: Wave 4 | Blocked by: 5 | Blocks: None
  References: tests/metadata_fetcher_test.py (mock pattern)
  Acceptance criteria: pytest tests/test_metadata_enricher.py -v passes
  QA scenarios: happy: all tests pass; failure: tests fail on network error; Evidence .omo/evidence/thuis-plugin-system/task-14-enricher-tests.<ext>
  Commit: Y | test(plugin): Add unit tests for metadata enricher

- [x] 15. Write unit tests for torrent uploader
  What to do / Must NOT do: Create tests/test_torrent_uploader.py with tests for create_torrent, upload_to_trackers. Must NOT upload to real trackers in tests.
  Parallelization: Wave 4 | Blocked by: 6 | Blocks: None
  References: tests/test_transcoder.py (file operation tests)
  Acceptance criteria: pytest tests/test_torrent_uploader.py -v passes
  QA scenarios: happy: all tests pass; failure: create_torrent fails on invalid input; Evidence .omo/evidence/thuis-plugin-system/task-15-uploader-tests.<ext>
  Commit: Y | test(plugin): Add unit tests for torrent uploader

- [x] 16. Write integration test for full torrent upload flow
  What to do / Must NOT do: Create tests/test_torrent_upload_integration.py that tests the full flow: metadata enrichment + torrent creation. Must NOT require real TMDB API key (use mock).
  Parallelization: Wave 4 | Blocked by: 5,6,7 | Blocks: None
  References: tests/test_integration.py
  Acceptance criteria: pytest tests/test_torrent_upload_integration.py -v passes
  QA scenarios: happy: full flow generates torrent with metadata; failure: missing metadata uses fallback; Evidence .omo/evidence/thuis-plugin-system/task-16-integration-test.<ext>
  Commit: Y | test(plugin): Add integration test for torrent upload

- [x] 17. Add python-libtorrent to requirements.txt
  What to do / Must NOT do: Add python-libtorrent>=2.0.0 to requirements.txt. Must NOT add other dependencies without approval.
  Parallelization: Wave 5 | Blocked by: 6 | Blocks: None
  References: requirements.txt
  Acceptance criteria: requirements.txt contains python-libtorrent>=2.0.0
  QA scenarios: happy: uv pip install -r requirements.txt succeeds; failure: invalid package name; Evidence .omo/evidence/thuis-plugin-system/task-17-dependencies.<ext>
  Commit: Y | build: Add python-libtorrent dependency

- [x] 18. Create plugin development documentation
  What to do / Must NOT do: Create docs/PLUGINS.md with: plugin interface, entry point registration, config options, PostprocessContext fields, example plugin. Must NOT document internal implementation details.
  Parallelization: Wave 5 | Blocked by: 1,2,3,4,5,6,7,8 | Blocks: None
  References: docs/DRM_KEY_EXTENSION_SPEC.md (existing doc pattern)
  Acceptance criteria: docs/PLUGINS.md exists and documents plugin development
  QA scenarios: happy: docs/PLUGINS.md is readable; failure: missing key sections; Evidence .omo/evidence/thuis-plugin-system/task-18-documentation.<ext>
  Commit: Y | docs: Add plugin development guide

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit - verify all todos have references + acceptance + QA + commit
- [x] F2. Code quality review - check for circular imports, proper error handling, type hints
- [x] F3. Real manual QA - run ./thuis.sh torrent-upload --dry-run on test directory
- [x] F4. Scope fidelity - verify no hardcoded trackers/keys, no auto-upload without flag

## Commit strategy
- Use conventional commits: feat(plugin):, feat(cli):, test(plugin):, docs:, build:
- Squash related changes into logical commits
- Do NOT commit .env or API keys

## Success criteria
- Plugin system is functional: entry-point discovery + config-driven enable/disable works
- Torrent upload plugin works: creates .torrent files with rich metadata descriptions
- CLI integration works: `thuis torrent-upload <dir>` subcommand processes files
- Optional auto-upload works: `--auto-upload` flag triggers upload after download
- All tests pass: pytest tests/test_plugin_*.py -v
- Documentation is complete: docs/PLUGINS.md exists
