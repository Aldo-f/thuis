"""yt-dlp metadata wrapper with codec mapping.

Fetches video metadata from VRT MAX / any yt-dlp-compatible URL
using a lightweight subprocess call to yt-dlp --print.
"""

from __future__ import annotations

import json
import subprocess
import sys

try:
    from .codec_map import lookup_codec, parse_resolution
except ImportError:
    # Standalone execution (e.g. `python src/thuis/metadata_fetcher.py`)
    import importlib, os as _os
    _src = _os.path.join(_os.path.dirname(__file__))
    if _src not in sys.path:
        sys.path.insert(0, _src)
    from codec_map import lookup_codec, parse_resolution

# Backward-compatibility alias — CODEC_MAP was previously defined locally
CODEC_MAP: dict[str, str] = lookup_codec.__module__  # type: ignore[misc]
# Re-export the original CODEC_MAP for tests that import it
try:
    from .codec_map import CODEC_MAP as _CODEC_MAP  # noqa: F401
    CODEC_MAP = _CODEC_MAP
except ImportError:
    pass


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
        ``acodec_label``, ``ext``, ``title``, and DRM fields:
        ``_vrt_drm_vudrm_token``, ``_vrt_drm_mpd_url``, ``_vrt_drm_init_url``.

        If the subprocess fails for any reason an **empty dict** is
        returned (no exception is raised).
    """
    # First, get the basic metadata via --print
    cmd = [sys.executable, "-m", "yt_dlp", "--print", _PRINT_FMT, "--ignore-no-formats-error", url]

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
        # Even if --print fails, try to get DRM metadata
        return _fetch_drm_metadata(url, credentials)

    if result.returncode != 0:
        # If --print failed, still try to get DRM metadata
        drm_fields = _fetch_drm_metadata(url, credentials)
        if drm_fields:
            return drm_fields
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

    metadata = {
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

    # Also fetch DRM metadata via -J (JSON output) if available
    # This gets _vrt_drm_* fields from the fork
    drm_fields = _fetch_drm_metadata(url, credentials)
    metadata.update(drm_fields)

    return metadata


def _fetch_drm_metadata(
    url: str, credentials: tuple[str, str] | None = None
) -> dict:
    """Fetch DRM metadata fields from yt-dlp -J output.
    
    Returns dict with _vrt_drm_vudrm_token, _vrt_drm_mpd_url, _vrt_drm_init_url
    if present, empty dict otherwise.
    """
    cmd = [sys.executable, "-m", "yt_dlp", "-J", "--ignore-no-formats-error", url]

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

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    drm_fields = {}
    for key in ("_vrt_drm_vudrm_token", "_vrt_drm_mpd_url", "_vrt_drm_init_url"):
        if key in data:
            drm_fields[key] = data[key]

    return drm_fields


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
