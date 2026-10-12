# Task 2 Evidence — Plugin Config Schema

## Change Made

**File:** `src/thuis/config.py`
**Line added:** `config.setdefault("plugins", {})` (line 61, after env overrides)

One-line change. Uses existing `setdefault` pattern already used by `apply_env_overrides` for nested dicts. No new functions, no abstractions.

## What was skipped
- No schema validation (no Pydantic models for plugins section) — that would be overkill for a default value
- No docs update — plugins section is documented in the task spec only

## Acceptance criteria verified
- `config.get("plugins", {})` returns `{}` when no plugins section exists ✓
- Config with plugins section loads correctly via `load_config()` ✓
- Nested plugin options (trackers list, tmdb_key string, piece_size int) all load correctly ✓
- No config.yaml at all → still returns `{}` for plugins ✓

## Tests
Created `tests/test_config_plugins.py` — 4 tests, all passing.

## Existing tests
`pytest tests/ -v` (venv): 496 passed, 2 failed (pre-existing edge-case tests unrelated to config/plugins).
No regressions introduced.

## Pre-existing failures (not caused by this change)
- `test_graphql_invalid_identifier_with_hash_is_skipped` — SQLite readonly DB issue in test
- `test_error_isolation_mixed_good_and_bad_urls` — same SQLite readonly DB issue

Both are in `test_edge_cases.py`, pre-existing, zero relation to config loading.
