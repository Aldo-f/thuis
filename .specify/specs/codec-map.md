# Codec Map Specification

## Module
`src/thuis/codec_map.py`

## Content
```python
CODEC_PRIORITIES = {
    # video codecs (high → low priority)
    "video": ["h265", "hev", "h264", "avc", "vp9", "vp8", "av1"],
    "audio": ["ac3", "eac3", "aac", "mp3", "vorbis", "opus", "flac"],
}

RESOLUTION_ORDER = ["4k", "2160p", "1440p", "1080p", "720p", "540p", "480p", "360p", "240p", "144p"]
```

## Functions
```python
def codec_sort_key(codec: str) -> tuple[int, int]:
    """Return (video_rank, audio_rank) for sorting."""

def resolution_sort_key(res: str) -> int:
    """Return numeric rank from RESOLUTION_ORDER."""
```

## Use
- `codec_detector.detect_highest_profile()` uses this map
- `scene_namer` uses resolution + audio to build filename template

## Tests
- `tests/thuis/test_codec_detector.py` — indirectly tests codec_map