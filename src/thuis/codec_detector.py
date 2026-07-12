"""Detect audio/video codecs from media files using ffprobe."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional


def detect_codecs(path: Path) -> tuple[Optional[str], Optional[str]]:
    """Detect audio and video codecs from a media file.

    Uses ``ffprobe`` to inspect the file at *path* and returns the raw
    ``codec_name`` values of the first video stream and the first audio
    stream.

    Args:
        path: Path to the media file.

    Returns:
        ``(audio_codec_raw, video_codec_raw)`` — the raw codec strings
        (e.g. ``"mp4a"``, ``"avc1"``). Either or both may be ``None``
        when the file has no stream of that type. Returns ``(None, None)``
        on any error (ffprobe not found, file not found, invalid JSON,
        timeout, etc.).
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return (None, None)

    if result.returncode != 0:
        return (None, None)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return (None, None)

    streams = data.get("streams", [])
    audio_codec: Optional[str] = None
    video_codec: Optional[str] = None

    for stream in streams:
        codec_type = stream.get("codec_type")
        codec_name = stream.get("codec_name")
        if codec_type == "video" and video_codec is None:
            video_codec = codec_name
        elif codec_type == "audio" and audio_codec is None:
            audio_codec = codec_name

    return (audio_codec, video_codec)
