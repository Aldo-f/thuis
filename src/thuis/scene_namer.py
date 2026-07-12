"""Scene-compliant filename builder for media files.

Builds filenames following scene release naming conventions:
  Title.of.show.S00E00.1080p.WEB-DL.AAC.x264.mp4
"""

import re
from typing import Optional

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
    "h264": "x264",
    "hevc": "x265",
    "vp9": "VP9",
    "av1": "AV1",
    "aac": "AAC",
    "mp3": "MP3",
    "ac3": "AC3",
    "eac3": "EAC3",
    "flac": "FLAC",
}


def lookup_codec(codec_str: str) -> str:
    """Look up a codec string in CODEC_MAP using prefix matching.

    Matches the start of *codec_str* against each CODEC_MAP key (e.g.
    ``avc1.64002A`` → ``x264``, ``mp4a.40.2`` → ``AAC``).

    Args:
        codec_str: Raw codec string from yt-dlp or other source.

    Returns:
        Mapped scene-style label, or *codec_str* unchanged if no match.
    """
    if not codec_str:
        return codec_str
    for key, label in CODEC_MAP.items():
        if codec_str.startswith(key):
            return label
    return codec_str


def normalize_show_name(name: str) -> str:
    """Normalise a show / movie name for use in a scene-style filename.

    - Replaces ``&`` with ``And``
    - Replaces runs of whitespace with ``.``
    - Strips all other special characters, keeping only ASCII letters,
      digits and dots.
    - Collapses multiple consecutive dots into one.
    - Strips leading/trailing dots.

    Args:
        name: Raw show or movie name.

    Returns:
        Normalised name safe for scene filenames.
    """
    if not name:
        return name or ""
    name = name.replace("&", "And")
    name = name.replace(" ", ".")
    name = re.sub(r"[^a-zA-Z0-9.]", "", name)
    name = re.sub(r"\.{2,}", ".", name)
    name = name.strip(".")
    return name


def _format_episode(episode: int) -> str:
    """Format episode number per scene naming rules.

    - ``episode > 99``: variable width (e.g. ``E6108``)
    - ``episode == 0``: ``E00``
    - otherwise: zero-padded to 2 digits (e.g. ``E01``, ``E12``)
    """
    if episode > 99:
        return f"E{episode}"
    if episode == 0:
        return "E00"
    return f"E{episode:02d}"


def _codec_tags(
    audio_codec: Optional[str],
    video_codec: Optional[str],
) -> str:
    """Build the dotted codec suffix after ``WEB-DL`` (e.g. ``.AAC.x264``).

    Returns empty string when both inputs are None/empty.
    """
    parts: list[str] = []
    if audio_codec:
        parts.append(lookup_codec(audio_codec))
    if video_codec:
        parts.append(lookup_codec(video_codec))
    return "." + ".".join(parts) if parts else ""


def build_tv_filename(
    show_name: str,
    season: int,
    episode: int,
    resolution: Optional[str] = None,
    audio_codec: Optional[str] = None,
    video_codec: Optional[str] = None,
) -> str:
    """Build a scene-style TV episode filename.

    Format (with all tags present)::

        Show.Name.S02E03.1080p.WEB-DL.AAC.x264.mp4

    Args:
        show_name: Show title (will be normalised).
        season: Season number (zero-padded to 2 digits).
        episode: Episode number (see :func:`_format_episode` for rules).
        resolution: Video height in pixels (e.g. ``"1080"`` → ``1080p``).
        audio_codec: Raw audio codec string (e.g. ``"mp4a"`` → ``AAC``).
        video_codec: Raw video codec string (e.g. ``"avc1"`` → ``x264``).

    Returns:
        Scene-style filename string.
    """
    show = normalize_show_name(show_name)
    res = f".{resolution}p" if resolution else ""
    codecs = _codec_tags(audio_codec, video_codec)
    return f"{show}.S{season:02d}{_format_episode(episode)}{res}.WEB-DL{codecs}.mp4"


def build_movie_filename(
    title: str,
    year: Optional[int] = None,
    resolution: Optional[str] = None,
    audio_codec: Optional[str] = None,
    video_codec: Optional[str] = None,
) -> str:
    """Build a scene-style movie filename.

    Format (with all tags present)::

        Movie.Title.1999.1080p.WEB-DL.AAC.x264.mp4

    The ``year`` tag is omitted when *year* is ``None`` or ``0``.

    Args:
        title: Movie title (will be normalised).
        year: Release year (e.g. 1999).
        resolution: Video height in pixels.
        audio_codec: Raw audio codec string.
        video_codec: Raw video codec string.

    Returns:
        Scene-style filename string.
    """
    show = normalize_show_name(title)
    res = f".{resolution}p" if resolution else ""
    codecs = _codec_tags(audio_codec, video_codec)
    year_str = f".{year}" if year else ""
    return f"{show}{year_str}{res}.WEB-DL{codecs}.mp4"


def build_special_filename(
    show_name: str,
    resolution: Optional[str] = None,
    audio_codec: Optional[str] = None,
    video_codec: Optional[str] = None,
) -> str:
    """Build a scene-style special episode filename.

    Format (with all tags present)::

        Show.Name.Special.1080p.WEB-DL.AAC.x264.mp4

    Args:
        show_name: Show title (will be normalised).
        resolution: Video height in pixels.
        audio_codec: Raw audio codec string.
        video_codec: Raw video codec string.

    Returns:
        Scene-style filename string.
    """
    show = normalize_show_name(show_name)
    res = f".{resolution}p" if resolution else ""
    codecs = _codec_tags(audio_codec, video_codec)
    return f"{show}.Special{res}.WEB-DL{codecs}.mp4"


def build_dated_tv_filename(
    show_name: str,
    date_str: str,
    resolution: Optional[str] = None,
    audio_codec: Optional[str] = None,
    video_codec: Optional[str] = None,
) -> str:
    """Build a scene-style filename for date-based episodes (e.g. news, weather).

    Format (with all tags present)::

        Show.Name.D20260706.1080p.WEB-DL.AAC.x264.mp4

    Args:
        show_name: Show title (will be normalised).
        date_str: Date string in YYYYMMDD format. Prepended with ``D``.
        resolution: Video height in pixels.
        audio_codec: Raw audio codec string.
        video_codec: Raw video codec string.

    Returns:
        Scene-style filename string.
    """
    show = normalize_show_name(show_name)
    res = f".{resolution}p" if resolution else ""
    codecs = _codec_tags(audio_codec, video_codec)
    return f"{show}.D{date_str}{res}.WEB-DL{codecs}.mp4"
