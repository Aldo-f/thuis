"""Test season/episode download functionality"""

import sys
import pytest
import re
import time
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

    def test_parse_season_url_with_query_param(self):
        """Extract season from URL with ?seizoen query param"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/thuis/?seizoen=seizoen-30"
        info = parse_episode_info(url)

        assert info["program"] == "thuis"
        assert info["season"] == "30"
        assert info["episode"] == ""

    def test_parse_season_url_no_trailing_slash(self):
        """Extract season from URL without trailing slash"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/thuis?seizoen=seizoen-1"
        info = parse_episode_info(url)

        assert info["program"] == "thuis"
        assert info["season"] == "1"


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


class TestExistingEpisodes:
    """Test get_existing_episodes function"""

    def test_get_existing_episodes_with_files(self, tmp_path):
        """Should return list of .mp4 files in directory"""
        from thuis import get_existing_episodes

        (tmp_path / "video1.mp4").touch()
        (tmp_path / "video2.mp4").touch()
        (tmp_path / "video3.txt").touch()

        result = get_existing_episodes(tmp_path)

        assert len(result) == 2
        assert "video1.mp4" in result
        assert "video2.mp4" in result
        assert "video3.txt" not in result

    def test_get_existing_episodes_empty_dir(self, tmp_path):
        """Should return empty list for empty directory"""
        from thuis import get_existing_episodes

        result = get_existing_episodes(tmp_path)

        assert result == []

    def test_get_existing_episodes_nonexistent_dir(self):
        """Should return empty list for nonexistent directory"""
        from thuis import get_existing_episodes

        result = get_existing_episodes(Path("/nonexistent/path"))

        assert result == []


class TestRandomDelay:
    """Test random_delay function"""

    def test_random_delay_returns(self):
        """Should complete without error"""
        from thuis import random_delay

        start = time.time()
        random_delay(0.01, 0.02)
        elapsed = time.time() - start

        assert 0.005 <= elapsed <= 0.05


class TestURLEdgeCases:
    """Test URL edge cases"""

    def test_url_with_special_chars(self):
        """URLs met special characters in program name"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/de-camping/1/de-camping-s1a1/"
        info = parse_episode_info(url)

        assert info["program"] == "de-camping"
        assert info["season"] == "1"
        assert info["episode"] == "1"

    def test_url_dash_in_name(self):
        """URL with dash in program name"""
        from thuis import parse_episode_info

        url = "https://www.vrt.be/vrtmax/a-z/den-elfde-van-den-elfde/1/den-elfde-van-den-elfde-s1a1/"
        info = parse_episode_info(url)

        assert "den-elfde-van-den-elfde" in info["program"]

    def test_detect_season_single_digit(self):
        """Season with single digit"""
        from thuis import detect_url_type

        url = "https://www.vrt.be/vrtmax/a-z/thuis/1/"
        result = detect_url_type(url)

        assert result == "season"

    def test_detect_season_double_digit(self):
        """Season with double digit"""
        from thuis import detect_url_type

        url = "https://www.vrt.be/vrtmax/a-z/thuis/31/"
        result = detect_url_type(url)

        assert result == "season"


class TestFilenameGeneration:
    """Test filename generation edge cases"""

    def test_filename_single_digit_episode(self):
        """Episode with single digit"""
        from thuis import generate_filename

        info = {"program": "thuis", "season": "1", "episode": "1"}
        filename = generate_filename(info)

        assert filename == "thuis-s1a1.mp4"

    def test_filename_double_digit_episode(self):
        """Episode with double digit"""
        from thuis import generate_filename

        info = {"program": "thuis", "season": "31", "episode": "6017"}
        filename = generate_filename(info)

        assert filename == "thuis-s31a6017.mp4"

    def test_filename_missing_season(self):
        """Filename without season"""
        from thuis import generate_filename

        info = {"program": "movie", "season": "", "episode": ""}
        filename = generate_filename(info)

        assert filename == "movie.mp4"


class TestFilterEdgeCases:
    """Test filter edge cases"""

    def test_filter_start_equals_first(self):
        """Start is first episode"""
        from thuis import filter_episodes_to_download

        episodes = ["video-s1a1.mp4", "video-s1a2.mp4"]
        result = filter_episodes_to_download(episodes, start_episode=1)

        assert len(result) == 2

    def test_filter_start_after_all(self):
        """Start is after all episodes"""
        from thuis import filter_episodes_to_download

        episodes = ["video-s1a1.mp4", "video-s1a2.mp4"]
        result = filter_episodes_to_download(episodes, start_episode=999)

        assert result == []

    def test_filter_start_and_existing_complex(self):
        """Complex filter with start and existing"""
        from thuis import filter_episodes_to_download

        all_episodes = ["s1a1.mp4", "s1a2.mp4", "s1a3.mp4", "s1a4.mp4", "s1a5.mp4"]
        existing = ["s1a2.mp4", "s1a4.mp4"]

        result = filter_episodes_to_download(
            all_episodes, existing_files=existing, start_episode=1
        )

        assert "s1a1.mp4" in result
        assert "s1a3.mp4" in result
        assert "s1a5.mp4" in result
        assert "s1a2.mp4" not in result
        assert "s1a4.mp4" not in result


class TestOutputPath:
    """Test output path generation"""

    def test_output_path_case_insensitive(self):
        """Should handle case differences"""
        from thuis import get_output_path

        url1 = "https://www.vrt.be/vrtmax/a-z/THUIS/31/"
        url2 = "https://www.vrt.be/vrtmax/a-z/thuis/31/"

        path1 = get_output_path(url1)
        path2 = get_output_path(url2)

        # Both should be in similar directory
        assert "thuis" in path1.parent.name.lower()
        assert "thuis" in path2.parent.name.lower()

    def test_output_path_creates_directory(self, tmp_path, monkeypatch):
        """Should create directory if it doesn't exist"""
        from thuis import get_output_path, MEDIA_DIR

        monkeypatch.setattr("thuis.MEDIA_DIR", tmp_path)

        url = "https://www.vrt.be/vrtmax/a-z/test/1/"
        path = get_output_path(url)

        assert path.parent.exists()
