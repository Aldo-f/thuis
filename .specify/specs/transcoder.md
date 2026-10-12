# Transcoder Specification

## Module
`src/thuis/transcoder.py`

## Function
```python
def process_file(input_path: str, output_dir: str, args: Namespace) -> int:
    """
    Post-process a downloaded file:
    - Ensure container is MP4
    - Normalize audio levels (ffmpeg loudnorm)
    - Extract subtitles if present
    - Optimize bitrate if over threshold
    Returns exit code.
    """
```

## Logic
1. Run `probe_video(input_path)` → get stream info
2. If container not MP4 → remux to MP4 (ffmpeg -c copy)
3. If audio codec not AAC → re-encode audio to AAC (ffmpeg -c:a aac)
4. If audio volume normalization enabled → apply loudnorm filter
5. If file size > MAX_SIZE → re-encode video with CRF 23
6. If subtitles present → extract to .srt file
7. If DRM decrypted → remove temporary decryption files

## Config
- `MAX_SIZE_GB`: from `config.get("max_size_gb", 2)`
- `AUDIO_NORMALIZE`: from `config.get("audio_normalize", False)`
- `EXTRACT_SUBTITLES`: from `config.get("extract_subtitles", True)`

## Tests
- `tests/test_transcoder.py` — does not exist yet? (but there is transcoder.py)
- `tests/test_real_download.py` — integration test with real file (mocked)

## Uses
- Called from `orchestrator._process_url()` after yt-dlp completes
- Only runs if `--no-transcode` flag not present (optional flag?)