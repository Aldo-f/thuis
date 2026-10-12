# URL Parser Specification

## Module
`src/thuis/url_parser.py` — parses VRT MAX URLs

## Function
```python
def parse_vrt_url(url: str) -> VRTInfo:
    """
    Parse a VRT MAX URL into structured info.
    Handles:
    - https://www.vrt.be/vrtmax/a/show/
    - https://www.vrt.be/vrtnu/a/videopagina/
    - https://www.vrt.be/vrtnu/a/video/
    - https://www.vrt.be/vrtnu/a/program/
    - https://www.vrt.be/vrtnu/a/podcast/
    - https://www.vrt.be/vrtnu/a/podcast/.../
    """
```

## Dataclass
```python
@dataclass
class VRTInfo:
    url: str
    show_slug: str
    season: int | None
    episode: int | None
    episode_name: str | None
    content_type: str  # 'show', 'movie', 'podcast', 'video', 'unknown'
    is_season_url: bool
```

## Parsing Rules
1. Extract `show_slug` from URL path segments
2. Extract `season` and `episode` numbers if present (e.g. `/s12/e3/`)
3. Extract `episode_name` from URL if present
4. Classify content type:
   - `podcast` if path contains `/podcast/`
   - `show` if path contains `/show/` or `/program/`
   - `video` if path contains `/video/` or `/videopagina/`
   - `movie` if path contains `/film/`
5. `is_season_url` = True if URL contains episode list (e.g. `/season/` or multiple `e` segments)

## Edge Cases
- Invalid URL → raise `ValueError`
- URL without `/a/` segment → raise `ValueError`
- URL with only show slug (no episode) → `season=None, episode=None`
- Podcast URL → `content_type='podcast'`

## Tests
- `tests/test_url_parser.py` — unit tests for each URL type
- `tests/thuis/test_url_parser.py` — integration tests with real URLs (mocked network)