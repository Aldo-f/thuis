# Scene Naming Specification

## Module
`src/thuis/scene_namer.py`

## Function
```python
def build_tv_filename(vrt_info: VRTInfo, metadata: dict, content_type: ContentType) -> str:
    """
    Generate a scene-compliant filename for TV show videos.
    Format: ShowName.SXXEXX.Resolution.Audio.Extension
    """
```

## Logic
1. Extract show_slug → clean to `Show.Name` (replace `-` with `.`, capitalize)
2. Extract season → format as `SXX` (zero-padded, 2 digits)
3. Extract episode → format as `EXX` (zero-padded, 2 digits)
4. Use `metadata['title']` as episode_name (or fallback to show name)
5. Use `vrt_info.resolution` (e.g. `1080p`, `720p`) if available, else `1080p`
6. Use `vrt_info.audio` (e.g. `AAC`, `AC3`) if available, else `AAC`
7. Append `.mp4` as default extension

## Rules
- Show name: replace `-` with `.`, capitalize each word
- Season: `SXX` where XX = season number (1-99)
- Episode: `EXX` where XX = episode number (1-99)
- Resolution: `1080p`, `720p`, `540p`, `480p` (from yt-dlp or `probe.py`)
- Audio: `AAC`, `AC3`, `MP3` (from codec_map)
- Extension: `.mp4` (default), `.mkv` (if ffmpeg used)

## Tests
- `tests/scene_namer_test.py` (exists — verify coverage)
- Unit tests for edge cases: no season, no episode, unknown show, etc.