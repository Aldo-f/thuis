"""Shared codec mapping for scene filename generation and metadata parsing.

Consolidates the duplicate CODEC_MAP definitions from
``scene_namer`` and ``metadata_fetcher`` into a single source of truth.
"""

from __future__ import annotations

CODEC_MAP: dict[str, str] = {
    # H.264 / AVC
    "avc1": "x264",
    "h264": "x264",
    # H.265 / HEVC
    "hev1": "x265",
    "hvc1": "x265",
    "hevc": "x265",
    # VP9
    "vp09": "VP9",
    "vp9": "VP9",
    # AV1
    "av01": "AV1",
    "av1": "AV1",
    # Audio codecs
    "mp4a": "AAC",
    "aac": "AAC",
    "ac-3": "AC3",
    "ac3": "AC3",
    "ec-3": "EAC3",
    "eac3": "EAC3",
    "opus": "Opus",
    "mp3": "MP3",
    "flac": "FLAC",
    "dts": "DTS",
}


def lookup_codec(codec_str: str) -> str:
    """Map a raw codec string to a human-readable label via CODEC_MAP.

    Matches on ``codec_str.startswith(key)`` so that e.g.
    ``avc1.64002A`` -> ``x264``.

    Returns the mapped label, or the original *codec_str* unchanged if
    no key matches.
    """
    for key, label in CODEC_MAP.items():
        if codec_str.startswith(key):
            return label
    return codec_str


def parse_resolution(height_str: str | None) -> str | None:
    """Normalise a numeric height string to a resolution label.

    Examples:
        ``"1080"`` -> ``"1080p"``
        ``"720"``  -> ``"720p"``
        ``None`` / ``""`` / ``"NA"`` -> ``None``
    """
    if not height_str or height_str == "NA":
        return None
    return f"{height_str}p"
