"""yt-dlp metadata wrapper with codec mapping.

Fetches video metadata from VRT MAX / any yt-dlp-compatible URL
using a lightweight subprocess call to yt-dlp --print.

Standalone module — CODEC_MAP is duplicated here intentionally
(they will be refactored into a shared location in a later commit).
"""

from __future__ import annotations

import subprocess
import sys

# ---------------------------------------------------------------------------
# Codec mapping — standalone copy (will be consolidated later)
# ---------------------------------------------------------------------------

CODEC_MAP: dict[str, str] = {
    "avc1": "x264",
    "hev1": "x265",
    "hvc1": "x265",
    "vp09": "VP9",
    "av01": "AV1",
    "mp4a": "AAC",
    "ac-3": "AC3",
    "ec-3": "EAC3",
    "opus": "Opus",
    "dts": "DTS",
}


def lookup_codec(codec_str: str) -> str:
    """Map a raw codec string to a human-readable label via CODEC_MAP.

    Matches on ``codec_str.startswith(key)`` so that e.g.
    ``avc1.64002A`` → ``x264``.

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
        ``"1080"`` → ``"1080p"``
        ``"720"``  → ``"720p"``
        ``None`` / ``""`` / ``"NA"`` → ``None``
    """
    if not height_str or height_str == "NA":
        return None
    return f"{height_str}p"


# ---------------------------------------------------------------------------
# yt-dlp metadata fetch
# ---------------------------------------------------------------------------

_PRINT_FMT = (
    "%(series)s|%(season_number)s|%(episode_number)s|"
    "%(height)s|%(vcodec)s|%(acodec)s|%(ext)s|%(title)s"
)


def _na_to_none(value: str) -> str | None:
    """Return ``None`` if *value* is ``"NA"``, otherwise return *value*."""
    return None if value == "NA" else value


def fetch_metadata(
    url: str, credentials: tuple[str, str] | None = None
) -> dict:
    """Fetch video metadata from *url* via ``yt-dlp --print``.

    Parameters
    ----------
    url:
        A yt-dlp-compatible video URL.
    credentials:
        Optional ``(email, password)`` tuple for authenticated sources.

    Returns
    -------
    dict
        Keys: ``series``, ``season``, ``episode``, ``height``,
        ``vcodec_raw``, ``vcodec_label``, ``acodec_raw``,
        ``acodec_label``, ``ext``, ``title``.

        If the subprocess fails for any reason an **empty dict** is
        returned (no exception is raised).
    """
    cmd = [sys.executable, "-m", "yt_dlp", "--print", _PRINT_FMT, url]

    if credentials:
        email, password = credentials
        cmd.extend(["--username", email, "--password", password])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        return {}

    if result.returncode != 0:
        return {}

    raw = result.stdout.strip()
    if not raw:
        return {}

    parts = raw.split("|", 7)
    if len(parts) < 8:
        return {}

    series, season, episode, height, vcodec_raw, acodec_raw, ext, title = parts

    vcodec_label = lookup_codec(vcodec_raw)
    acodec_label = lookup_codec(acodec_raw)

    return {
        "series": _na_to_none(series),
        "season": _na_to_none(season),
        "episode": _na_to_none(episode),
        "height": parse_resolution(height),
        "vcodec_raw": vcodec_raw,
        "vcodec_label": vcodec_label,
        "acodec_raw": acodec_raw,
        "acodec_label": acodec_label,
        "ext": ext,
        "title": _na_to_none(title),
    }


def fetch_preview_height(
    url: str, credentials: tuple[str, str] | None = None
) -> int | None:
    """Fetch only the video height from *url* via a lightweight yt-dlp call.

    Much cheaper than :func:`fetch_metadata` because it requests a
    single field instead of eight.

    Parameters
    ----------
    url:
        A yt-dlp-compatible video URL.
    credentials:
        Optional ``(email, password)`` tuple for authenticated sources.

    Returns
    -------
    int or None
        The video height as an integer (e.g. ``1080``), or ``None`` if
        unavailable or the call fails.
    """
    cmd = [sys.executable, "-m", "yt_dlp", "--print", "%(height)s", url]
    if credentials:
        email, password = credentials
        cmd.extend(["--username", email, "--password", password])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception:
        return None

    if result.returncode != 0:
        return None

    raw = result.stdout.strip()
    if not raw or raw == "NA":
        return None

    try:
        return int(raw)
    except ValueError:
        return None


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else input("URL: ")
    meta = fetch_metadata(url)
    for k, v in meta.items():
        print(f"{k}: {v}")
