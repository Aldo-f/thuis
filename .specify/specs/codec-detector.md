# Codec Detector Specification

## Module
`src/thuis/codec_detector.py`

## Function
```python
def detect_highest_profile(video_data: list[dict]) -> dict:
    """
    From yt-dlp JSON format data, select the best quality stream.
    Prioritizes: resolution → codec → audio quality
    """
```

## Logic
1. Input: list of stream formats from yt-dlp (`--list-formats` JSON)
2. Filter to video+audio streams (not audio-only, not subtitles)
3. Sort by: resolution descending, then codec quality
4. Return dict with: resolution, codec, audio, file_size, url

## Resolution Priority
```
4K > 2160p > 1080p > 1440p > 720p > 540p > 480p > 360p > 240p > 144p
```

## Codec Priority (within same resolution)
```
H.265 (HEVC) > H.264 (AVC) > VP9 > VP8
```

## Audio Priority
```
AC3 > AAC > MP3 > Vorbis > Opus
```

## Tests
- `tests/thuis/test_codec_detector.py` (exists)
- Test with mock yt-dlp JSON data