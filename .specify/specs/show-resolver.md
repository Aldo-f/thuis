# Show Resolver Specification

## Module
`src/thuis/show_resolver.py`

## Function
```python
def resolve_show_id_from_url(url: str) -> str | None:
    """
    Given a VRT URL, return the show slug (used for episode progress tracking).
    Resolves show ID via GraphQL if URL is to a specific episode.
    """
```

## Logic
1. Parse URL with `url_parser.parse_vrt_url(url)` → get `show_slug`
2. If URL is to a specific episode, fetch GraphQL to get canonical show slug
3. If URL is already a show list page, return the show slug directly
4. Cache results in SQLite DB (`episode_progress` table? or separate cache)

## Use Case
- Used by `watchlist.py` episode progress tracking
- Tracks last seen episode per show+season: `episode_progress` table

## Tests
- `tests/test_show_resolver.py` (exists — mock GraphQL responses)
- Tests: valid show URL, episode URL, podcast URL, invalid URL

## Returns
- Show slug string (e.g. "thuis", "flikken")
- None if URL invalid or not resolvable