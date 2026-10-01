"""Season completion detector — checks TMDB vs local files."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SeasonDetector:
    """Checks whether all episodes of a TV season are present locally.

    Compares the number of local episode files (matching
    ``ShowName.S{NN}E{NN}.*`` pattern) against the expected episode
    count from TMDB.
    """

    _EPISODE_PATTERN = re.compile(r"\.S(\d{2})E(\d{2})\.", re.IGNORECASE)

    def __init__(
        self,
        download_dir: Path,
        show_name: str,
        season: int,
        tmdb_key: str,
    ) -> None:
        self._download_dir = Path(download_dir)
        self._show_name = show_name
        self._season = season
        self._tmdb_key = tmdb_key

    def collect_files(self) -> list[Path]:
        """Return sorted list of episode files for this season."""
        season_prefix = f"S{self._season:02d}E"
        files = [
            f
            for f in self._download_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in (".mp4", ".mkv", ".avi")
            and season_prefix in f.name
        ]
        return sorted(files, key=lambda f: f.name)

    def _local_episode_numbers(self) -> set[int]:
        """Return set of episode numbers found locally."""
        numbers: set[int] = set()
        for f in self.collect_files():
            match = self._EPISODE_PATTERN.search(f.name)
            if match:
                s = int(match.group(1))
                e = int(match.group(2))
                if s == self._season:
                    numbers.add(e)
        return numbers

    def _tmdb_episode_count(self) -> int | None:
        """Return expected episode count from TMDB."""
        from thuis.plugins.metadata_enricher import TMDBClient

        client = TMDBClient(api_key=self._tmdb_key)
        return client.get_season_episode_count(self._show_name, season=self._season)

    def check(self) -> tuple[bool, list[int], int]:
        """Check if the season is complete.

        Returns
        -------
        (is_complete, missing_episodes, expected_count)
        """
        expected = self._tmdb_episode_count()
        if expected is None or expected <= 0:
            logger.warning(
                "Could not determine episode count for %s S%02d from TMDB",
                self._show_name,
                self._season,
            )
            return False, [], 0

        local = self._local_episode_numbers()
        missing = sorted(set(range(1, expected + 1)) - local)

        is_complete = len(missing) == 0
        if is_complete:
            logger.info(
                "Season %02d complete: %d/%d episodes",
                self._season,
                len(local),
                expected,
            )
        else:
            logger.info(
                "Season %02d incomplete: %d/%d episodes (missing: %s)",
                self._season,
                len(local),
                expected,
                missing,
            )
        return is_complete, missing, expected
