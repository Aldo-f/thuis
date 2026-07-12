"""Parse video filenames into structured components.

Handles scene-style naming conventions, duplicate markers (``_1``),
partial download markers (``.part``), and extracts show slug, season,
episode, and resolution information.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ParsedFilename:
    """Structured components extracted from a video filename.

    Attributes:
        show_slug: Normalised show identifier (lowercase, dot-separated).
        season: Season number (0 if not available).
        episode: Episode number (0 for Specials, date-based, or unknown).
        resolution: Video height in pixels without ``p`` suffix, or ``None``.
        is_duplicate: ``True`` if the filename had a ``_1`` duplicate marker.
        is_part: ``True`` if the filename ends with ``.part``.
        original_path: The original :class:`pathlib.Path` that was parsed.
    """
    show_slug: str
    season: int
    episode: int
    resolution: Optional[str]
    is_duplicate: bool
    is_part: bool
    original_path: Path


#: Primary regex for scene-style filenames.
#: Matches: ``Show.Name.s01e12.1080p.mp4``,
#: ``Show.Name.S01E12.1080p.WEB-DL.AAC.x264.mp4``,
#: ``Show.Name.Special.1080p.mp4``, ``Show.Name.D20260706.1080p.mp4``
#:
#: The ``show`` group is matched lazily so the regex engine backtracks
#: through longer show-name candidates until it finds position where the
#: season/episode/Special/date markers align correctly.
_RE_STANDARD = re.compile(
    r'^(?P<show>[\w.]+?)\.'
    r'(?:[sS](?P<season>\d+))?'
    r'(?:[eE](?P<episode>\d+)|[Ss]pecial|[Dd]\d{8})'
    r'(?:\.(?P<resolution>\d+)[pP])?'
)

#: Fallback regex for a single dot-separated part.
#: Only used when the primary regex fails — matches ``s01e12`` or ``S21E12``.
_RE_FALLBACK = re.compile(r'^[sS](\d+)[eE](\d+)$')

#: Regex to detect a resolution tag (digits followed by *p* / *P*).
_RE_RESOLUTION = re.compile(r'^(\d+)[pP]$')


def parse_filename(path: Path) -> Optional[ParsedFilename]:
    """Parse a video filename into structured components.

    Handles scene naming conventions, ``.part`` partial downloads, and
    ``_1`` duplicate markers.

    Parser pipeline:

    1. Check if the filename ends with ``.part`` — mark and strip it.
    2. Separate the stem (everything before the last ``.``).
    3. Check for a trailing ``_1`` — mark and strip it.
    4. Try the primary scene-style regex.
    5. If that fails, fall back to dot-splitting and scanning for a
       ``sXXeYY`` part.
    6. Return ``None`` only for completely unrecognisable filenames.

    Args:
        path: Path to the video file.

    Returns:
        A :class:`ParsedFilename` instance if the filename could be parsed,
        or ``None`` if no recognisable media pattern was found.

    Example:
        >>> from pathlib import Path
        >>> p = parse_filename(Path("fc.de.kampioenen.s01e12.1080p.mp4"))
        >>> p.show_slug
        'fc.de.kampioenen'
        >>> p.season
        1
        >>> p.episode
        12
        >>> p.resolution
        '1080'
    """
    name = path.name
    if not name:
        return None

    # --- Step 1: Handle .part suffix -------------------------------------------
    is_part = False
    if name.endswith('.part'):
        is_part = True
        name = name[:-5]  # strip ``.part``

    # --- Step 2: Separate stem from extension ----------------------------------
    dot = name.rfind('.')
    if dot <= 0:
        # No identifiable extension — e.g. ``file.part`` → stem is ``file``
        if is_part:
            return ParsedFilename(
                show_slug='',
                season=0,
                episode=0,
                resolution=None,
                is_duplicate=False,
                is_part=True,
                original_path=path,
            )
        return None

    stem = name[:dot]

    # --- Step 3: Handle _1 duplicate marker ------------------------------------
    is_duplicate = False
    if stem.endswith('_1'):
        is_duplicate = True
        stem = stem[:-2]

    # --- Step 4: Try primary scene-style regex ---------------------------------
    m = _RE_STANDARD.match(stem)
    if m:
        show_slug = m.group('show').lower()
        season = int(m.group('season')) if m.group('season') else 0
        episode_str = m.group('episode')
        episode = int(episode_str) if episode_str else 0
        resolution = m.group('resolution')
        return ParsedFilename(
            show_slug=show_slug,
            season=season,
            episode=episode,
            resolution=resolution,
            is_duplicate=is_duplicate,
            is_part=is_part,
            original_path=path,
        )

    # --- Step 5: Fallback — split on dots, scan for sXXeYY --------------------
    parts = stem.split('.')
    for idx, part in enumerate(parts):
        fm = _RE_FALLBACK.match(part)
        if fm:
            show_slug = '.'.join(p.lower() for p in parts[:idx])
            season = int(fm.group(1)) if fm.group(1) else 0
            episode = int(fm.group(2))

            # Look for resolution in parts after the sXXeYY marker
            resolution: Optional[str] = None
            for candidate in parts[idx + 1:]:
                rm = _RE_RESOLUTION.match(candidate)
                if rm:
                    resolution = rm.group(1)
                    break
            if not resolution:
                # Fall back to searching parts before the marker
                for candidate in parts[:idx]:
                    rm = _RE_RESOLUTION.match(candidate)
                    if rm:
                        resolution = rm.group(1)
                        break

            return ParsedFilename(
                show_slug=show_slug,
                season=season,
                episode=episode,
                resolution=resolution,
                is_duplicate=is_duplicate,
                is_part=is_part,
                original_path=path,
            )

    # --- Step 6: Nothing matched -----------------------------------------------
    if is_part:
        return ParsedFilename(
            show_slug='',
            season=0,
            episode=0,
            resolution=None,
            is_duplicate=is_duplicate,
            is_part=True,
            original_path=path,
        )

    return None
