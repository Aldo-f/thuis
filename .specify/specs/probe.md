# Probe Specification

## Module
`src/thuis/probe.py`

## Function
```python
def probe_video(path: str) -> dict:
    """
    Run ffprobe on a downloaded file and return stream info.
    """
```

## Output
```python
{
    "duration": float,        # seconds
    "video_codec": str,      # e.g. "h264"
    "audio_codec": str,      # e.g. "aac"
    "width": int,
    "height": int,
    "resolution": "1080p",
    "has_video": bool,
    "has_audio": bool,
}
```

## Logic
1. Run `ffprobe -v error -show_streams -show_format path`
2. Parse JSON output
3. Extract video stream (first video stream) and audio stream (first audio stream)
4. Determine resolution from width×height
5. Determine codecs from stream info

## Use
- `transcoder.py` — checks if post-processing needed
- `scene_namer.py` — uses resolution/audio to build filename
- `test_audio_stream_detection.py` — tests audio stream detection

## Error Handling
- ffprobe not found → return None
- Invalid JSON → return None
- No video stream → raise ValueError
- No audio stream → return dict with `has_audio=False`