"""VRT MAX URL parser — extract show slug, season, and episode from VRT URLs."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class VrtUrlInfo:
    """Parsed information from a VRT MAX URL.

    Attributes:
        show_slug: Normalized show identifier from the URL path.
        season: Season number (0 if not applicable, e.g. specials/trailers).
        episode: Episode number (0 if not applicable).
        path: Raw URL path after normalization (no trailing slash, no double slashes).
        url: Original URL as provided.
    """
    show_slug: str
    season: int
    episode: int
    path: str
    url: str


def _normalize_path(path: str) -> str:
    """Strip trailing slash and collapse double slashes in a URL path."""
    normalized = path.rstrip("/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def parse_vrt_url(url: str) -> VrtUrlInfo:
    """Parse a VRT MAX URL into its components.

    Expected URL pattern:
        https://www.vrt.be/vrtmax/a-z/{show-slug}/{season}/{show-slug}-s{season}a{episode}/

    Handles edge cases:
    - `/extra-s/` or `/trailer/` in path → season=0, episode=0
    - No ``s(\\d+)a(\\d+)`` pattern in last segment → season=0, episode=0
    - Triple hyphens in slug → single hyphen
    - Ampersand in slug → ``And``

    Args:
        url: A VRT MAX URL string.

    Returns:
        VrtUrlInfo with parsed fields.

    Raises:
        ValueError: If the URL cannot be parsed as a VRT MAX URL.
    """
    parsed = urlparse(url)
    path = _normalize_path(parsed.path)

    if "/vrtmax/a-z/" not in path:
        raise ValueError(f"Could not parse VRT URL: {url}")

    # Extract path segments after /vrtmax/a-z/
    az_marker = "/vrtmax/a-z/"
    after_az = path.split(az_marker, 1)[1].strip("/")
    segments = after_az.split("/")

    if not segments or not segments[0]:
        raise ValueError(f"Could not parse VRT URL: {url}")

    show_slug_raw = segments[0]

    # Normalize show slug
    show_slug = show_slug_raw.replace("---", "-").replace("&", "And")

    # Check for special/trailer edge cases
    path_lower = path.lower()
    if "/extra-s/" in path_lower or "/trailer/" in path_lower:
        return VrtUrlInfo(show_slug=show_slug, season=0, episode=0, path=path, url=url)

    season = 0
    episode = 0

    # Extract season from a numeric segment (normally segments[1])
    if len(segments) > 1 and re.match(r"^\d+$", segments[1]):
        season = int(segments[1])

    # Extract episode from the last path segment: s{season}a{episode}
    last_segment = segments[-1] if segments else ""
    ep_match = re.search(r"s(\d+)a(\d+)", last_segment, re.IGNORECASE)
    if ep_match:
        episode = int(ep_match.group(2))
        if season == 0:
            season = int(ep_match.group(1))

    return VrtUrlInfo(show_slug=show_slug, season=season, episode=episode, path=path, url=url)
