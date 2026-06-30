"""TV/movie/special classifier for VRT MAX content based on URL structure and yt-dlp metadata."""

import enum
from typing import Optional

try:
    from .url_parser import VrtUrlInfo
except ImportError:
    from url_parser import VrtUrlInfo


class ContentType(enum.Enum):
    """Content type classification for VRT MAX media.

    Values:
        TV:       A standard TV episode (identified by season+episode or series metadata).
        MOVIE:    A movie-length feature (identified by lack of episode data).
        SPECIAL:  A behind-the-scenes extra, trailer, or similar non-episodic content.
        UNKNOWN:  Could not be classified with available information.
    """
    TV = "tv"
    MOVIE = "movie"
    SPECIAL = "special"
    UNKNOWN = "unknown"


def _is_missing_episode(value) -> bool:
    """Check if a value represents missing episode information.

    Returns True when the value is None, an empty string, or a string
    like "N/A" or "NA" (case-insensitive, after stripping whitespace).
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip().upper() in ("N/A", "NA", ""):
        return True
    return False


def classify(vrt_info: VrtUrlInfo, ytdlp_meta: Optional[dict] = None) -> ContentType:
    """Classify a VRT MAX video based on its URL and optional yt-dlp metadata.

    Rules are evaluated in order — the first match wins:

    1. **SPECIAL** — URL path contains ``/extra-s/`` or ``/trailer/``.
    2. **TV** — ``vrt_info.season > 0`` **and** ``vrt_info.episode > 0``.
    3. **TV** — ``ytdlp_meta`` contains a truthy ``"series"`` key.
    4. **MOVIE** — ``ytdlp_meta`` has no episode info (``None`` / ``"N/A"`` / empty)
       **and** ``vrt_info.season == 0``.
    5. **UNKNOWN** — fallback.

    Args:
        vrt_info: Parsed URL information from :func:`thuis.url_parser.parse_vrt_url`.
        ytdlp_meta: Optional dictionary with keys such as ``series``, ``episode``,
            ``season``, ``title``, etc., as returned by yt-dlp's ``--dump-json``.

    Returns:
        A :class:`ContentType` value.
    """
    # Rule 1 — special URL patterns
    path_lower = vrt_info.path.lower()
    if "/extra-s/" in path_lower or "/trailer/" in path_lower:
        return ContentType.SPECIAL

    # Rule 2 — TV from URL structure (both season and episode present)
    if vrt_info.season > 0 and vrt_info.episode > 0:
        return ContentType.TV

    # Rules 3-4 require yt-dlp metadata
    if ytdlp_meta is not None:
        # Rule 3 — TV from series metadata
        series = ytdlp_meta.get("series")
        if series and str(series).strip():
            return ContentType.TV

        # Rule 4 — Movie (no episode info, no season from URL)
        episode = ytdlp_meta.get("episode")
        if _is_missing_episode(episode) and vrt_info.season == 0:
            return ContentType.MOVIE

    # Rule 5 — fallback
    return ContentType.UNKNOWN
