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


class TestStealthImport:
    """Test stealth functionality is properly imported"""

    def test_stealth_import(self):
        """Should import stealth module"""
        from playwright_stealth import stealth as playwright_stealth

        assert hasattr(playwright_stealth, "Stealth")

    def test_stealth_class(self):
        """Should create Stealth instance"""
        from playwright_stealth import stealth as playwright_stealth

        stealth = playwright_stealth.Stealth()
        assert stealth is not None
        assert hasattr(stealth, "apply_stealth_async")


class TestCookiePersistence:
    """Test cookie save/load functionality"""

    def test_save_and_load_cookies(self, tmp_path):
        """Should save and load cookies"""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from thuis import save_cookies, load_cookies

        test_cookies = [
            {"name": "session", "value": "abc123", "domain": ".vrt.be"},
            {"name": "token", "value": "xyz789", "domain": ".vrt.be"},
        ]

        cookie_file = tmp_path / "test_cookies.json"
        save_cookies(test_cookies, cookie_file)

        loaded = load_cookies(cookie_file)

        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["name"] == "session"
        assert loaded[1]["value"] == "xyz789"

    def test_load_cookies_nonexistent(self, tmp_path):
        """Should return None for nonexistent cookie file"""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from thuis import load_cookies

        cookie_file = tmp_path / "nonexistent.json"
        loaded = load_cookies(cookie_file)

        assert loaded is None


class MockLink:
    """Mock link element for testing"""

    def __init__(self, href):
        self.href = href

    def get_attribute(self, name):
        return self.href if name == "href" else None


class MockPage:
    """Mock Playwright page for testing episode discovery"""

    def __init__(self, links):
        self.links = links

    def query_selector_all(self, selector):
        return [MockLink(href) for href in self.links]


class TestEpisodeDiscovery:
    """Test episode discovery from season page"""

    def test_discover_episodes_with_results(self):
        """Should discover episodes from season page"""
        from thuis import discover_season_episodes

        page = MockPage(
            [
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6001/",
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6002/",
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6003/",
            ]
        )

        result = discover_season_episodes(page)

        assert len(result) == 3
        assert "thuis-s31a6001" in result[0]
        assert "thuis-s31a6002" in result[1]
        assert "thuis-s31a6003" in result[2]

    def test_discover_episodes_relative_urls(self):
        """Should convert relative URLs to absolute"""
        from thuis import discover_season_episodes

        page = MockPage(
            [
                "/vrtmax/a-z/thuis/31/thuis-s31a6001/",
                "/vrtmax/a-z/thuis/31/thuis-s31a6002/",
            ]
        )

        result = discover_season_episodes(page)

        assert len(result) == 2
        assert result[0].startswith("https://www.vrt.be")
        assert "/thuis-s31a6001/" in result[0]

    def test_discover_episodes_no_results(self):
        """Should return empty list when no episodes found"""
        from thuis import discover_season_episodes

        page = MockPage(
            [
                "https://www.vrt.be/vrtmax/a-z/thuis/",
                "https://www.vrt.be/vrtmax/a-z/ander-programma/",
            ]
        )

        result = discover_season_episodes(page)

        assert result == []

    def test_discover_episodes_dedup(self):
        """Should deduplicate episode URLs"""
        from thuis import discover_season_episodes

        page = MockPage(
            [
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6001/",
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6001/",  # duplicate
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6002/",
            ]
        )

        result = discover_season_episodes(page)

        assert len(result) == 2

    def test_discover_episodes_sorted(self):
        """Should return sorted episode URLs"""
        from thuis import discover_season_episodes

        page = MockPage(
            [
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6003/",
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6001/",
                "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6002/",
            ]
        )

        result = discover_season_episodes(page)

        assert "6001" in result[0]
        assert "6002" in result[1]
        assert "6003" in result[2]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_filter_empty_list(self):
        """Should handle empty episode list"""
        from thuis import filter_episodes_to_download

        result = filter_episodes_to_download([])

        assert result == []

    def test_filter_all_existing(self):
        """Should return empty when all episodes exist"""
        from thuis import filter_episodes_to_download

        all_episodes = ["thuis-s31a6001.mp4", "thuis-s31a6002.mp4"]
        existing = ["thuis-s31a6001.mp4", "thuis-s31a6002.mp4"]

        result = filter_episodes_to_download(all_episodes, existing)

        assert result == []

    def test_parse_invalid_url(self):
        """Should handle invalid URL gracefully"""
        from thuis import parse_episode_info

        url = "https://example.com/"
        info = parse_episode_info(url)

        assert info["program"] == "" or info["program"] == "example.com"
