# Metadata Fetcher Specification

## Module
`src/thuis/metadata_fetcher.py`

## Function
```python
def fetch_metadata(url: str) -> dict | None:
    """
    Fetch metadata from VRT MAX GraphQL API.
    Returns None on failure (network, auth, API error).
    """
```

## GraphQL Query
- Uses `_LIST_QUERY` from `main.py` (cursor-based pagination)
- Requests title, year, duration, description, genres
- Handles pagination to get all metadata for a show/season

## Process
1. Parse URL with `url_parser.parse_vrt_url(url)`
2. Execute paginated GraphQL query to get tile list
3. Extract first matching tile for the episode/video
4. Return dict with: title, year, duration, description, genres
5. Cache results in SQLite DB (`episode_cache` table, TTL 24h)

## Error Handling
- Network error → return None
- Non-200 status → return None
- JSON decode error → return None
- No matching tile → return None

## Tests
- `tests/metadata_fetcher_test.py` (exists — mock urlopen)
- `tests/test_download_db_integration.py` — tests episode_cache

## Key Returned Fields
- title (str)
- year (int)
- duration_ms (int)  
- description (str)
- genres (list[str])
- thumbnail_url (str)