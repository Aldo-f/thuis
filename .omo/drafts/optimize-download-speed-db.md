---
slug: optimize-download-speed-db
status: approved
intent: clear
review_required: false
pending-action: write .omo/plans/optimize-download-speed-db.md
approach: Replace filesystem glob-based duplicate checking with SQLite database lookups for O(1) speed. After successful download, immediately record the (url, generated_filename, output_dir) tuple in the WatchlistDB. On subsequent runs, check the database first (fast indexed query) before falling back to filesystem glob.
---

# Draft: optimize-download-speed-db

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
c1 | Persist download state to SQLite after each successful download | active | src/thuis/main.py:1608-1630 (download success path)
c2 | Use database lookup as primary duplicate check, filesystem glob as fallback | active | src/thuis/main.py:1532-1550 (pre-download dedup)
c3 | Ensure WatchlistDB.record_download() is called with correct generated scene filename | active | src/thuis/watchlist.py:399-406 (record_download method)

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
a1 | Database check runs first, filesystem glob only as fallback | Yes - DB is authoritative for "we downloaded this"; filesystem handles edge cases like manual file moves | Reversible - can swap order or add flag
a2 | Record download immediately after yt-dlp returns 0 (before transcoding) | Yes - yt-dlp 0 = file written to disk; transcoding creates new file | Reversible - can move after transcoding if needed
a3 | Use the exact scene_template filename as the database key | Yes - this is the deterministic output name | Reversible - could use URL+season+episode but filename is simpler

## Findings (cited - path:lines)
f1 | WatchlistDB has record_download(url, filename, output_dir) and file_was_downloaded(url, filename, output_dir) but they are NEVER called in main.py | src/thuis/watchlist.py:399-415
f2 | Main download loop uses filesystem glob (args.output_dir.glob(search)) for duplicate detection - slow for 310+ episodes | src/thuis/main.py:1532-1550
f3 | Watchlist mode invokes main.py with --retry flag (line 1151) which triggers this slow glob check | src/thuis/main.py:1151
f4 | Scene filename is generated BEFORE download (scene_template variable) and available at line 1628 when returncode == 0 | src/thuis/main.py:1508-1628
f5 | WatchlistDB.downloaded_files table has PRIMARY KEY (url, filename, output_dir) - perfect for O(1) lookup | src/thuis/watchlist.py:333-339
f6 | No migration needed - tables already exist in current schema | src/thuis/watchlist.py:319-341

## Decisions (with rationale)
d1 | Call WatchlistDB.record_download() immediately after yt-dlp returns 0, using the scene_template that was used for download | Uses existing deterministic filename; no extra computation
d2 | In pre-download check, query file_was_downloaded() FIRST; if True, skip immediately. Only if False, fall back to filesystem glob | DB is O(1) vs filesystem O(N); filesystem handles files downloaded outside thuis
d3 | Keep --retry flag behavior unchanged for users who don't use watchlist/DB | Backward compatible; --retry still works via filesystem
d4 | Pass output_dir and scene_template to WatchlistDB at the right scope (inside the per-URL loop) | Avoids global DB instance issues; matches existing pattern

## Scope IN
- Modify src/thuis/main.py: add DB import, call record_download() on success, replace glob-first check with db-first check
- No changes to watchlist.py (methods already exist)
- No changes to CLI interface (--retry still works)
- No schema changes (tables exist)

## Scope OUT (Must NOT have)
- No new CLI flags
- No changes to watchlist file format
- No changes to DRM handling flow
- No changes to transcoding logic
- No migration scripts (tables already exist)

## Open questions
None - all decisions resolved by exploration and best-practice defaults.

## Approval gate
status: approved
