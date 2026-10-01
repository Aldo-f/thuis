"""Tests for season_detector — checks season completion via TMDB + local files."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from thuis.plugins.season_detector import SeasonDetector


class TestSeasonDetector:
    """SeasonDetector checks if all episodes of a season are present."""

    def test_season_complete(self, tmp_path):
        """Returns (True, [], 13) when 13/13 episodes present."""
        # Create 13 fake episode files
        for i in range(1, 14):
            (tmp_path / f"FC.De.Kampioenen.S01E{i:02d}.1080p.WEB-DL.AAC.x264.mp4").touch()

        detector = SeasonDetector(
            download_dir=tmp_path,
            show_name="FC De Kampioenen",
            season=1,
            tmdb_key="fake_key",
        )
        with patch.object(detector, "_tmdb_episode_count", return_value=13):
            complete, missing, expected = detector.check()
        assert complete is True
        assert missing == []
        assert expected == 13

    def test_season_incomplete(self, tmp_path):
        """Returns (False, [3,5,7], 13) when 10/13 episodes present."""
        for i in [1, 2, 4, 6, 8, 9, 10, 11, 12, 13]:
            (tmp_path / f"FC.De.Kampioenen.S01E{i:02d}.1080p.WEB-DL.AAC.x264.mp4").touch()

        detector = SeasonDetector(
            download_dir=tmp_path,
            show_name="FC De Kampioenen",
            season=1,
            tmdb_key="fake_key",
        )
        with patch.object(detector, "_tmdb_episode_count", return_value=13):
            complete, missing, expected = detector.check()
        assert complete is False
        assert sorted(missing) == [3, 5, 7]
        assert expected == 13

    def test_no_files(self, tmp_path):
        """Returns (False, list(range(1,14)), 13) when no files present."""
        detector = SeasonDetector(
            download_dir=tmp_path,
            show_name="FC De Kampioenen",
            season=1,
            tmdb_key="fake_key",
        )
        with patch.object(detector, "_tmdb_episode_count", return_value=13):
            complete, missing, expected = detector.check()
        assert complete is False
        assert len(missing) == 13
        assert expected == 13

    def test_collect_season_files(self, tmp_path):
        """collect_files returns sorted list of episode files for a season."""
        for i in range(1, 4):
            (tmp_path / f"FC.De.Kampioenen.S01E{i:02d}.1080p.WEB-DL.AAC.x264.mp4").touch()
        # Also create a season 2 file — should NOT be included
        (tmp_path / "FC.De.Kampioenen.S02E01.1080p.WEB-DL.AAC.x264.mp4").touch()

        detector = SeasonDetector(
            download_dir=tmp_path,
            show_name="FC De Kampioenen",
            season=1,
            tmdb_key="fake_key",
        )
        files = detector.collect_files()
        assert len(files) == 3
        assert all("S01E" in f.name for f in files)
