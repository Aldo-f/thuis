# Plan: Make --auto-upload work on existing downloaded files

## Problem
`--auto-upload` only runs post-process plugins after a *new* download (`main.py:2064`).
When a URL is already in the DB (`db.any_file_for_url` → True at `main.py:1884`),
the script logs `Skipped ... already downloaded` (silent logger.info, not print)
and `continue`s — never reaching the download/auto-upload path.

Verified: DB row for `f-c--de-kampioenen-s1a2/` → file
`Fc.De.Kampioenen.S01E02.1080p.WEB-DL.AAC.x264.mp4` already recorded.

## Goal
When `--auto-upload` is set and a URL is skipped due to DB dedup, still locate the
recorded file on disk and run postprocess plugins on it.

## Tasks
- [ ] **Task 1** — Log skip reason visibly: replace `logger.info("Skipped ...")`
  with a `print(f"Skipped ... already downloaded as {recorded_filename}")` so
  users see *why* no download occurred. Files: `main.py:1903-1904`.
- [ ] **Task 2** — Add auto-upload branch on skip: in the DB-skip block
  (`main.py:1884-1904`), if `args.auto_upload` is set, look up the recorded
  filename via `db.get_filename_for_url` (new helper — see below), reconstruct
  the file path in `args.output_dir`, verify it exists, then run PluginManager
  plugins (`main.py:2064-2087` refactor). Files: `main.py`, `watchlist.py`.
- [ ] **Task 3** — Add `WatchlistDB.get_filename_for_url(url, output_dir)`
  helper returning the recorded filename or None. File: `watchlist.py`.
- [ ] **Task 4** — Add/extend unit tests to cover the skip + auto-upload
  path with an existing DB row + existing file. File:
  `tests/test_auto_upload_existing.py` (or extend existing test suite).

- [ ] **Task 5** — Verify with real invocation on the `fc-de-kampioenen` URL
  (dry-run with file present in DB). Confirm plugins are invoked for the
  existing file.

## Out of scope
- Changing dedup logic for non-auto-upload invocations (behavior stays the same).
- Not touching the `--force` semantics (user explicitly does not want disk recheck).
