"""Test season/episode download functionality"""

import sys
import pytest
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestURLDetection:
    """Test URL type detection (season vs single episode)"""

    def test_detect_single_episode(self):
        """Single episode URL should be detected"""
        from thuis import detect_url_type

        url = "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
        result = detect_url_type(url)

        assert result == "single", f"Expected 'single', got '{result}'"

    def test_detect_season_url(self):
        """Season URL should be detected"""
        from thuis import detect_url_type

        url = "https://www.vrt.be/vrtmax/a-z/thuis/31/"
        result = detect_url_type(url)

        assert result == "season", f"Expected 'season', got '{result}'"

    def test_detect_trailer_url(self):
        """Trailer URL should be detected as trailer"""
        from thuis import detect_url_type

        url = "https://www.vrt.be/vrtmax/a-z/flikken-maastricht/trailer/flikken-maastricht-trailer-s15/"
        result = detect_url_type(url)

        assert result == "trailer", f"Expected 'trailer', got '{result}'"


class TestEpisodeParsing:
    """Test episode info extraction from URL"""

    def test_parse_single_episode(self):
        """Extract episode info from single episode URL"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
        info = parse_episode_info(url)

        assert info["program"] == "thuis"
        assert info["season"] == "31"
        assert info["episode"] == "6017"

    def test_parse_trailer(self):
        """Extract info from trailer URL"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/flikken-maastricht/trailer/flikken-maastricht-trailer-s15/"
        info = parse_episode_info(url)

        assert info["type"] == "trailer"


class TestPathGeneration:
    """Test output path generation"""

    def test_single_episode_path(self):
        """Single episode should have consistent path"""
        from thuis import get_output_path

        url = "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
        path = get_output_path(url)

        assert "thuis" in path.name.lower()
        assert path.suffix == ".mp4"

    def test_season_single_episode_path(self):
        """Season episode should have same folder as single episode"""
        from thuis import get_output_path

        url_season = "https://www.vrt.be/vrtmax/a-z/thuis/31/"
        url_single = "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"

        path_season = get_output_path(url_season)
        path_single = get_output_path(url_single)

        # Should be in same folder
        assert path_season.parent == path_single.parent, (
            f"Season and single episode should be in same folder. "
            f"Got: {path_season.parent} vs {path_single.parent}"
        )


class TestEpisodeFiltering:
    """Test episode filtering (skip existing, start from X)"""

    def test_filter_skip_existing(self):
        """Should skip already downloaded episodes"""
        from thuis import filter_episodes_to_download

        all_episodes = [
            "thuis-s31a6001.mp4",
            "thuis-s31a6002.mp4",
            "thuis-s31a6003.mp4",
            "thuis-s31a6004.mp4",
        ]
        existing_files = ["thuis-s31a6001.mp4", "thuis-s31a6003.mp4"]

        result = filter_episodes_to_download(all_episodes, existing_files)

        assert result == ["thuis-s31a6002.mp4", "thuis-s31a6004.mp4"]

    def test_filter_start_from_episode(self):
        """Should filter from specific episode number"""
        from thuis import filter_episodes_to_download

        all_episodes = [
            "thuis-s31a6001.mp4",
            "thuis-s31a6002.mp4",
            "thuis-s31a6003.mp4",
            "thuis-s31a6004.mp4",
        ]

        result = filter_episodes_to_download(all_episodes, start_episode=6003)

        assert result == ["thuis-s31a6003.mp4", "thuis-s31a6004.mp4"]

    def test_filter_start_and_existing(self):
        """Should combine start and skip existing"""
        from thuis import filter_episodes_to_download

        all_episodes = [
            "thuis-s31a6001.mp4",
            "thuis-s31a6002.mp4",
            "thuis-s31a6003.mp4",
            "thuis-s31a6004.mp4",
        ]
        existing_files = ["thuis-s31a6002.mp4"]

        result = filter_episodes_to_download(
            all_episodes, existing_files=existing_files, start_episode=6001
        )

        assert result == [
            "thuis-s31a6001.mp4",
            "thuis-s31a6003.mp4",
            "thuis-s31a6004.mp4",
        ]


class TestFilenameFormat:
    """Test filename format generation"""

    def test_filename_format(self):
        """Should generate correct filename format"""
        from thuis import generate_filename

        info = {"program": "thuis", "season": "31", "episode": "6001"}
        filename = generate_filename(info)

        assert filename == "thuis-s31a6001.mp4"

    def test_filename_format_trailer(self):
        """Should generate trailer filename"""
        from thuis import generate_filename

        info = {"program": "flikken-maastricht", "type": "trailer"}
        filename = generate_filename(info)

        assert "flikken-maastricht" in filename
        assert filename.endswith(".mp4")
