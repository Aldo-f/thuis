# Filename Parser Specification

## Module
`src/thuis/filename_parser.py`

## Function
```python
def parse_scene_filename(filename: str) -> SceneInfo | None:
    """
    Parse a scene-formatted filename into structured info.
    Handles: Show.SXXEXX.1080p.WEB-DL.AAC.x264.mp4
    """
```

## Parsing Rules
1. Regex-based parsing for: `Show.Name.SXXEXX.Res.Other.mp4`
2. Extract: show_name, season (int), episode (int), resolution, codec, audio
3. Support variations:
   - `Show Name SXXEXX` (space-separated)
   - `Show-Name.SXXEXX` (dash-separated)
   - `ShowName S01E01` (common format)
   - `ShowName [SXXEXX]` (brackets)

## Dataclass
```python
@dataclass
class SceneInfo:
    show_name: str
    season: int
    episode: int
    resolution: str  # e.g. "1080p", "720p"
    codec: str      # e.g. "H.264", "H.265"
    audio: str      # e.g. "AAC", "AC3"
    extension: str  # e.g. ".mp4"
```

## Tests
- `tests/thuis/test_filename_parser.py` (exists)
- Test all format variations
- Test edge cases: no resolution, no codec, weird characters

## Uses
- Watchlist dedup: `check_file_exists()` in watchlist.py