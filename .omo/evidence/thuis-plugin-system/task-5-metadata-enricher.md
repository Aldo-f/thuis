# Evidence — Task 5: Metadata Enricher (TMDBClient)

## Files Created

- `src/thuis/plugins/__init__.py` — empty init (allows `from thuis.plugins import ...`)
- `src/thuis/plugins/metadata_enricher.py` — `TMDBClient` class (213 lines)
- `tests/test_metadata_enricher.py` — 26 test cases

## Dependencies Checked

- `requests` 2.34.2 confirmed available in `.venv` (transitive dep via `pywidevine`)
- Not in `requirements.txt` directly, but installed — used per task instructions ("if available")
- Fallback `urllib.request` was considered but requests chosen for cleaner API

## TMDB API Endpoints Used

| Method | Endpoint |
|--------|----------|
| `lookup_show` search | `GET /search/tv?query={series}` |
| `lookup_show` details | `GET /tv/{id}` |
| `lookup_show` episode | `GET /tv/{id}/season/{s}/episode/{e}` + fallback to `/tv/{id}/season/{s}` |
| `lookup_movie` search | `GET /search/movie?query={title}&year={year}` |
| `lookup_movie` details | `GET /movie/{id}` |
| `fetch_poster_image` | `GET https://image.tmdb.org/t/p/w{width}{path}` |

## Test Results

```
26 passed in 0.79s
```

Coverage includes:
- Baseline: network error returns None
- Happy path: show lookup, movie lookup, poster fetch
- Episode lookup with fallback chain
- 401 unauthorized, 404 not found, malformed response
- Empty/missing poster_path guards
- Default width (500) verification

## Key Design Decisions

- `_get_json` private helper centralizes all HTTP + error handling → single retry/mock point
- Episode endpoint failure falls back to season-level fetch + filter (robustness)
- `seasons` key is always present: `int` count for shows, `0` for movies
- Year extracted from `first_air_date`/`release_date` via `date_str[:4]` (tolerant of malformed strings)
- API key stored on `Session.params` so every request includes it automatically

## Existing Test Suite Impact

Full suite still green (no regressions).

## References

- TMDB API v3 docs: https://developer.themoviedb.org/reference
- Patched via `unittest.mock.patch.object(client, "_get_json", side_effect=...)` for zero-network tests
