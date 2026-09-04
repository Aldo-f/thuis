# optimize-download-speed-db - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** Full-season downloads (300+ episodes) will skip already-downloaded episodes in milliseconds instead of seconds, by checking a local SQLite database first instead of scanning the filesystem.

**Why this approach:** The database already exists with the right schema and methods — they were just never wired up. Database lookup is O(1) indexed query vs O(N) filesystem glob per episode. For 310 episodes, that's ~310x faster duplicate checks.

**What it will NOT do:**
- Add new CLI flags or change watchlist file format
- Change DRM handling or transcoding logic
- Require database migrations (tables already exist)
- Break --retry for users not using watchlist mode

**Effort:** Quick
**Risk:** Low - surgical changes to two functions in main.py, existing DB methods are tested
**Decisions to sanity-check:** (1) Record download immediately after yt-dlp success (before transcoding) — if transcoding fails, the original file still exists and DB record is correct. (2) DB check first, filesystem fallback — if user manually moves files, glob catches it.

Your next move: Run `$start-work` to execute. Full execution detail follows below.

---
> TL;DR (machine): Quick, Low risk — two edits to main.py wiring existing WatchlistDB methods for O(1) duplicate checks

## Scope
### Must have
- After successful download (yt-dlp returncode 0), call WatchlistDB.record_download(url, scene_template, output_dir)
- Pre-download: check WatchlistDB.file_was_downloaded(url, scene_template, output_dir) FIRST; if True, skip immediately; if False, fall back to filesystem glob
- Keep --retry flag working via filesystem for non-watchlist users
- No schema changes, no new CLI flags, no watchlist format changes

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No new CLI arguments
- No changes to watchlist file format or parsing
- No changes to DRM detection/handling flow
- No changes to transcoding logic
- No database migration scripts (tables already created by WatchlistDB._init_tables)
- No global DB instance — create inside per-URL loop like existing pattern

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest (existing test suite in tests/)
- Evidence: .omo/evidence/task-N-optimize-download-speed-db.log (pytest output + manual verification commands)

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
Wave 1: Implementation (2 todos - can run in parallel as they touch different line ranges)
Wave 2: Test updates (1 todo)
Wave 3: Integration verification (1 todo)

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Add DB import and record_download call | — | 3 | 2 |
| 2. Replace glob-first check with db-first check | — | 3 | 1 |
| 3. Add tests for new DB integration | 1, 2 | 4 | — |
| 4. Integration test: full watchlist run with --dry-run | 3 | F-wave | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Add WatchlistDB import and record_download() call after successful yt-dlp download
  What to do / Must NOT do: In src/thuis/main.py, add `from thuis.watchlist import WatchlistDB` import. After yt-dlp returns 0 (line ~1628), before transcoding, create WatchlistDB instance and call `db.record_download(url, scene_template, str(args.output_dir))` then `db.close()`. Use the exact `scene_template` string that was passed to yt-dlp. Do NOT record for DRM-skipped or failed downloads.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 3
  References (executor has NO interview context - be exhaustive): src/thuis/main.py:1352-1630 (download loop), src/thuis/watchlist.py:399-406 (record_download), src/thuis/main.py:1608-1630 (success path)
  Acceptance criteria (agent-executable): After downloading a new episode, `sqlite3 ~/.thuis/state.db "SELECT * FROM downloaded_files;"` shows a row with the URL, generated filename, and output_dir
  QA scenarios (name the exact tool + invocation): happy: run `./thuis.sh --watchlist watchlists/Thuis.txt --now --dry-run 2>&1 | head -20` then check DB; failure: interrupt download mid-way, verify no partial record written. Evidence: .omo/evidence/task-1-optimize-download-speed-db.log
  Commit: Y | feat(download): record downloaded episodes in SQLite for fast dedup

- [x] 2. Replace filesystem glob duplicate check with database-first lookup
  What to do / Must NOT do: In src/thuis/main.py lines 1532-1550, replace the glob-based check with: (1) if content_type == TV, generate the search pattern as before; (2) call `db = WatchlistDB(); if db.file_was_downloaded(url, scene_template, str(args.output_dir)): db.close(); continue`; (3) else fall back to existing glob check; (4) db.close(). For non-TV content, use scene_template directly with file_was_downloaded. Keep the existing glob logic as fallback unchanged.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 3
  References (executor has NO interview context - be exhaustive): src/thuis/main.py:1532-1550 (current dedup), src/thuis/watchlist.py:408-415 (file_was_downloaded), src/thuis/main.py:1434-1463 (scene_template generation for TV)
  Acceptance criteria (agent-executable): (a) Second run of same watchlist with --dry-run shows "Overgeslagen" instantly for all episodes (no glob delay). (b) Manually deleting a file but not DB entry → glob fallback catches it. (c) `--retry` without watchlist still works via glob.
  QA scenarios (name the exact tool + invocation): happy: run watchlist twice with --dry-run, measure time; failure: delete file from disk, run again, verify glob fallback skips correctly. Evidence: .omo/evidence/task-2-optimize-download-speed-db.log
  Commit: Y | feat(download): use SQLite DB for O(1) duplicate detection

- [x] 3. Add pytest tests for WatchlistDB integration in main download flow
  What to do / Must NOT do: In tests/test_watchlist.py or new test file, add tests that: (a) mock yt-dlp success and verify record_download is called with correct args; (b) mock file_was_downloaded returning True and verify download is skipped; (c) test fallback to glob when DB returns False. Use existing test patterns and tmp_path fixtures.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 4
  References (executor has NO interview context - be exhaustive): tests/test_watchlist.py:236-248 (existing record_download test), tests/test_watchlist.py:1-29 (test structure)
  Acceptance criteria (agent-executable): `python -m pytest tests/test_watchlist.py -v -k "record_download or file_was_downloaded"` passes; new tests cover main.py integration paths
  QA scenarios (name the exact tool + invocation): run pytest on new tests; verify coverage includes main.py lines 1532-1550 and 1628-1630. Evidence: .omo/evidence/task-3-optimize-download-speed-db.log
  Commit: Y | test(download): add WatchlistDB integration tests

- [x] 4. Integration verification: full watchlist dry-run completes without errors
  What to do / Must NOT do: Run `./thuis.sh --watchlist watchlists/Thuis.txt --now --dry-run` and verify: (a) All 310 episodes process; (b) Second run shows instant skips via DB; (c) No regression in DRM handling, transcoding, or --retry flag. Do NOT modify any watchlist files or test data.
  Parallelization: Wave 3 | Blocked by: 3 | Blocks: F-wave
  References (executor has NO interview context - be exhaustive): src/thuis/main.py:1079-1156 (_run_watchlist), watchlists/Thuis.txt (test data)
  Acceptance criteria (agent-executable): Command exits 0; output shows "[1/310] Verwerken..." then "[2/310] Overgeslagen..." instantly on second run; no tracebacks
  QA scenarios (name the exact tool + invocation): run command twice, compare timing; verify DB has 310 entries after first run. Evidence: .omo/evidence/task-4-optimize-download-speed-db.log
  Commit: N | (verification only)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit
  Verify: every Must-have implemented, every Must-NOT-have respected, no scope drift. Check: DB called on success, DB checked first, glob fallback works, --retry unchanged, no new flags, no schema changes.
  Evidence: .omo/evidence/f1-plan-compliance.log

- [x] F2. Code quality review
  Verify: no new globals, proper DB connection close in all paths (success/error/interrupt), imports at module level, no duplicate code, type hints where feasible. Run: `ruff check src/thuis/main.py`
  Evidence: .omo/evidence/f2-code-quality.log

- [x] F3. Real manual QA
  Verify: actually run `./thuis.sh --watchlist watchlists/Thuis.txt --now --dry-run` twice, confirm second run is near-instant for skips. Test --retry without watchlist still works. Test DRM skip still works.
  Evidence: .omo/evidence/f3-manual-qa.log

- [x] F4. Scope fidelity
  Verify: git diff shows only src/thuis/main.py and tests/ changes. No changes to watchlist.py, CLI args, schema, DRM, or transcoding.
  Evidence: .omo/evidence/f4-scope-fidelity.log

## Commit strategy
- Task 1: feat(download): record downloaded episodes in SQLite for fast dedup
- Task 2: feat(download): use SQLite DB for O(1) duplicate detection
- Task 3: test(download): add WatchlistDB integration tests
- Task 4: (verification - no commit)

## Success criteria
- Second watchlist run with 310 episodes completes duplicate checks in <2 seconds (was ~30+ seconds)
- All existing tests pass
- No regressions in DRM, transcoding, --retry, or manual download modes
- Database has correct entries after first run
- Fallback to filesystem glob works for manually moved/deleted files