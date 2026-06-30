"""Edge case and error isolation tests for thuis.main.

Tests cover:
- Special characters in show names (&, %, #)
- Double slashes in URLs (//)
- Missing metadata (all NA/None values)
- High episode numbers (>999)
- Network failures (simulated subprocess failure)
- Classifier returns UNKNOWN
- Per-URL error isolation (one bad URL doesn't break batch)
- Fallback to "%(title)s.%(ext)s" template
- Dry-run mode with edge cases
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from unittest.mock import patch, MagicMock

import pytest
from thuis.main import main, build_yt_dlp_args, get_credentials
from thuis.classifier import ContentType
from thuis.url_parser import _normalize_path, parse_vrt_url


# ===================================================================
# Edge case: URL with special characters (&, %, #)
# ===================================================================

def test_special_chars_ampersand_causes_parse_failure(monkeypatch):
    """URL with & in show name that can't be parsed triggers fallback template."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.side_effect = ValueError("bad url with &")
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Ignore.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/show&test/1/show&test-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # Even with a parse failure, subprocess.run should be called
        # with the fallback template "%(title)s.%(ext)s"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template in -o arg, got: {output_arg}"


def test_special_chars_percent_in_url_triggers_fallback(monkeypatch):
    """URL with %% in show name causes parse failure and fallback."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.side_effect = ValueError("bad url with %")
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Ignore.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/100%25-show/1/100%25-show-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template in -o arg, got: {output_arg}"


def test_special_chars_hash_in_url_triggers_fallback(monkeypatch):
    """URL with # in show name causes parse failure and fallback."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.side_effect = ValueError("bad url with #")
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Ignore.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/show#1/1/show#1-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template in -o arg, got: {output_arg}"


# ===================================================================
# Edge case: Double slashes in URLs (//)
# ===================================================================

def test_normalize_path_collapses_double_slashes():
    """Direct test of url_parser._normalize_path: // → /."""
    assert _normalize_path("/vrtmax//a-z//test-show//1//ep/") == "/vrtmax/a-z/test-show/1/ep"
    assert _normalize_path("//vrtmax/a-z/test-show////") == "/vrtmax/a-z/test-show"
    assert _normalize_path("/vrtmax/a-z/test-show") == "/vrtmax/a-z/test-show"
    assert _normalize_path("/") == ""


def test_double_slashes_still_process_successfully(monkeypatch):
    """URL with double slashes is normalized by URL parser and processing continues."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        # Simulate that URL parser handled the double slashes and returned
        # a valid VrtUrlInfo with a normalized path
        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=1, episode=1,
            path="/vrtmax/a-z/test-show/1/test-show-s01e01",
            url="https://www.vrt.be//vrtmax//a-z//test-show//1//test-show-s01e01//"
        )
        mock_fetch.return_value = {
            "series": "Test Show", "season": "1", "episode": "1",
            "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
            "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
            "title": "Test Episode"
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4"

        test_url = "https://www.vrt.be//vrtmax//a-z//test-show//1//test-show-s01e01//"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        # Scene template should be in output, NOT fallback
        assert "Test.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4" in output_arg, \
            f"Expected scene template in -o arg, got: {output_arg}"
        assert "%(title)s.%(ext)s" not in output_arg, \
            "Fallback template should NOT be used when parsing succeeds"


# ===================================================================
# Edge case: Missing metadata (all NA/None values)
# ===================================================================

def test_metadata_all_none_falls_back_to_unknown(monkeypatch):
    """When metadata_fetcher returns all None/NA, classifier returns UNKNOWN
    and fallback template is used (when URL has no season/episode)."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        # URL has no season/episode info (special-like)
        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=0, episode=0,
            path="/vrtmax/a-z/test-show/extra-s/test-show-extra",
            url="https://www.vrt.be/vrtmax/a-z/test-show/extra-s/test-show-extra/"
        )
        # Metadata returns empty dict (simulating yt-dlp failure or missing data)
        mock_fetch.return_value = {}
        # Classifier returns UNKNOWN when there's no metadata and no URL structure
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Test.Show.S01E01.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/extra-s/test-show-extra/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        # Should use fallback because classifier returned UNKNOWN
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template for UNKNOWN content type, got: {output_arg}"


def test_metadata_all_na_values_from_fetcher(monkeypatch):
    """When metadata contains NA strings, these should be handled gracefully."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        # URL has season/episode info -> classifier returns TV from URL
        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=1, episode=1,
            path="/vrtmax/a-z/test-show/1/test-show-s01e01",
            url="https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01e01/"
        )
        # Metadata with NA values (as would come from yt-dlp --print)
        mock_fetch.return_value = {
            "series": "NA", "season": "NA", "episode": "NA",
            "height": None, "vcodec_raw": "NA", "acodec_raw": "NA",
            "vcodec_label": "NA", "acodec_label": "NA", "ext": "mp4",
            "title": None
        }
        # With season>0 and episode>0 from URL, classifier returns TV (rule 2)
        mock_classify.return_value = ContentType.TV
        # Scene namer called with fallback values: show_slug for name, 
        # season=1 from URL, episode=1 from URL, None resolution/codecs
        mock_build.return_value = "Test.Show.S01E01.WEB-DL.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        # Scene template should be used (classifier returned TV from URL structure)
        assert "Test.Show.S01E01.WEB-DL.mp4" in output_arg, \
            f"Expected scene template, got: {output_arg}"
        assert "%(title)s.%(ext)s" not in output_arg, \
            "Fallback should NOT be used when classifier returns TV"


# ===================================================================
# Edge case: High episode numbers (>999)
# ===================================================================

def test_high_episode_number_formatting():
    """Direct test of scene_namer high episode formatting (>99 = variable width)."""
    from thuis.scene_namer import _format_episode
    assert _format_episode(100) == "E100"
    assert _format_episode(999) == "E999"
    assert _format_episode(1000) == "E1000"
    assert _format_episode(6108) == "E6108"
    assert _format_episode(1) == "E01"
    assert _format_episode(0) == "E00"


def test_high_episode_number_in_pipeline(monkeypatch):
    """Episode number >999 is correctly passed through the pipeline."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        mock_parse.return_value = MagicMock(
            show_slug="long-running-show", season=1, episode=1000,
            path="/vrtmax/a-z/long-running-show/1/long-running-show-s01e1000",
            url="https://www.vrt.be/vrtmax/a-z/long-running-show/1/long-running-show-s01e1000/"
        )
        mock_fetch.return_value = {
            "series": "Long Running Show", "season": "1", "episode": "1000",
            "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
            "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
            "title": "Episode 1000"
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Long.Running.Show.S01E1000.WEB-DL.1080p.AAC.x264.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/long-running-show/1/long-running-show-s01e1000/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "S01E1000" in output_arg, \
            f"Expected episode 1000 in output, got: {output_arg}"


# ===================================================================
# Edge case: Network failure (simulate subprocess failure)
# ===================================================================

def test_metadata_fetch_network_failure_uses_fallback(monkeypatch):
    """When metadata_fetcher fails (returns {}), fallback template is used
    for URLs that lack season/episode structure (classifier -> UNKNOWN)."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        # URL has no season/episode
        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=0, episode=0,
            path="/vrtmax/a-z/test-show/extra-s/test-show-extra",
            url="https://www.vrt.be/vrtmax/a-z/test-show/extra-s/test-show-extra/"
        )
        # Simulate network failure: fetch_metadata returns empty dict
        mock_fetch.return_value = {}
        # With empty metadata and no URL season/episode -> UNKNOWN
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Does.Not.Matter.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/extra-s/test-show-extra/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template after network failure, got: {output_arg}"


def test_ytdlp_subprocess_nonzero_exit(monkeypatch, capsys):
    """When yt-dlp subprocess returns non-zero, main() continues and
    exits with code 1 (tracking failures)."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        # Subprocess returns non-zero (simulating yt-dlp failure)
        mock_run.return_value = MagicMock(returncode=1)

        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=1, episode=1,
            path="/vrtmax/a-z/test-show/1/test-show-s01e01",
            url="https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01e01/"
        )
        mock_fetch.return_value = {
            "series": "Test Show", "season": "1", "episode": "1",
            "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
            "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
            "title": "Test Episode"
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                # Non-zero exit because subprocess failed
                assert e.code == 1
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        # Verify the URL was still passed to yt-dlp
        args = mock_run.call_args[0][0]
        assert test_url in args


# ===================================================================
# Edge case: Classifier returns UNKNOWN
# ===================================================================

def test_classifier_unknown_triggers_fallback(monkeypatch):
    """When classifier returns UNKNOWN, fallback template '%(title)s.%(ext)s' is used."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(
            show_slug="test-show", season=0, episode=0,
            path="/vrtmax/a-z/test-show/unknown/test-show-unknown",
            url="https://www.vrt.be/vrtmax/a-z/test-show/unknown/test-show-unknown/"
        )
        mock_fetch.return_value = {"title": "Unknown Content"}
        # Classifier returns UNKNOWN
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "Should.Not.Be.Used.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/unknown/test-show-unknown/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template for UNKNOWN content type, got: {output_arg}"
        # The scene namer output should NOT appear since UNKNOWN skips scene naming
        assert "Should.Not.Be.Used" not in output_arg, \
            "Scene namer output should not be used for UNKNOWN content type"


# ===================================================================
# Per-URL error isolation
# ===================================================================

def test_error_isolation_mixed_good_and_bad_urls(monkeypatch):
    """One bad URL should not prevent other URLs from processing.
    Mix of 3 URLs: good, bad (parse failure), good.
    - All 3 should be passed to subprocess.run
    - Good URLs should use scene template
    - Bad URL should use fallback template
    """
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        good_url_1 = "https://www.vrt.be/vrtmax/a-z/good-show/1/good-show-s01e01/"
        bad_url = "https://www.vrt.be/vrtmax/a-z/bad%%show/1/bad%%show-s01e01/"
        good_url_2 = "https://www.vrt.be/vrtmax/a-z/another-show/2/another-show-s02e03/"

        # First call succeeds, second raises, third succeeds
        mock_parse.side_effect = [
            MagicMock(show_slug="good-show", season=1, episode=1,
                      path="/vrtmax/a-z/good-show/1/good-show-s01e01",
                      url=good_url_1),
            ValueError("bad url with %%"),
            MagicMock(show_slug="another-show", season=2, episode=3,
                      path="/vrtmax/a-z/another-show/2/another-show-s02e03",
                      url=good_url_2),
        ]

        # fetch_metadata: first succeeds, second is never called (parse fails early),
        # third succeeds
        mock_fetch.side_effect = [
            {
                "series": "Good Show", "season": "1", "episode": "1",
                "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
                "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
                "title": "Good Episode"
            },
            # Second call never happens because parse raises first
            # But pytest needs 3 side effects, so add dummy entries
            {},
            {
                "series": "Another Show", "season": "2", "episode": "3",
                "height": "720p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
                "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
                "title": "Another Episode"
            },
        ]

        # Classify: first TV, second is never called, third TV
        mock_classify.side_effect = [
            ContentType.TV,
            ContentType.TV,  # Won't actually be called but needed for side_effect length
            ContentType.TV,
        ]

        # Both good URLs get scene names
        mock_build.side_effect = [
            "Good.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4",
            "Another.Show.S02E03.WEB-DL.720p.AAC.x264.mp4",
        ]

        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", good_url_1, bad_url, good_url_2]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # Should have been called 3 times (once per URL)
        assert mock_run.call_count == 3, \
            f"Expected 3 subprocess.run calls, got {mock_run.call_count}"

        # First call: good_url_1 should have scene template
        first_args = mock_run.call_args_list[0][0][0]
        idx_o1 = first_args.index("-o")
        first_output = first_args[idx_o1 + 1]
        assert "Good.Show.S01E01" in first_output, \
            f"Expected scene template for good URL 1, got: {first_output}"
        assert good_url_1 in first_args

        # Second call: bad_url should have fallback template
        second_args = mock_run.call_args_list[1][0][0]
        idx_o2 = second_args.index("-o")
        second_output = second_args[idx_o2 + 1]
        assert "%(title)s.%(ext)s" in second_output, \
            f"Expected fallback template for bad URL, got: {second_output}"
        assert bad_url in second_args

        # Third call: good_url_2 should have scene template
        third_args = mock_run.call_args_list[2][0][0]
        idx_o3 = third_args.index("-o")
        third_output = third_args[idx_o3 + 1]
        assert "Another.Show.S02E03" in third_output, \
            f"Expected scene template for good URL 2, got: {third_output}"
        assert good_url_2 in third_args


# ===================================================================
# Fallback to "%(title)s.%(ext)s" works correctly
# ===================================================================

def test_fallback_template_after_parse_failure(monkeypatch):
    """When URL parsing fails, the fallback template must be exactly
    '%(title)s.%(ext)s' (the default yt-dlp template)."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.side_effect = ValueError("cannot parse")
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "NotUsed.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/broken-url/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        # The output arg should be Path("media") / "%(title)s.%(ext)s"
        # which on Linux is "media/%(title)s.%(ext)s"
        assert output_arg.endswith("%(title)s.%(ext)s"), \
            f"Expected fallback template 'media/%(__title__)s.%(__ext__)s', got: {output_arg}"


def test_fallback_template_after_unknown_classification(monkeypatch):
    """When classifier returns UNKNOWN, fallback '%(title)s.%(ext)s' must be used."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(
            show_slug="unclassified-show", season=0, episode=0,
            path="/vrtmax/a-z/unclassified-show/uncl/unclassified-show-uncl",
            url="https://www.vrt.be/vrtmax/a-z/unclassified-show/uncl/unclassified-show-uncl/"
        )
        mock_fetch.return_value = {"title": "Something"}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "NotUsed.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/unclassified-show/uncl/unclassified-show-uncl/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert output_arg.endswith("%(title)s.%(ext)s"), \
            f"Expected fallback template for UNKNOWN, got: {output_arg}"


# ===================================================================
# Dry-run mode with edge cases
# ===================================================================

def test_dry_run_with_bad_url_shows_fallback(monkeypatch, capsys):
    """--dry-run with a bad URL should print fallback notice and use --simulate."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.side_effect = ValueError("cannot parse in dry-run")
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN
        mock_build.return_value = "NotUsed.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/broken-dry-run/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--dry-run", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # In dry-run mode, --simulate should be in the args
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--simulate" in args, \
            "--simulate should be present in dry-run mode"

        # Fallback template should be used
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "%(title)s.%(ext)s" in output_arg, \
            f"Expected fallback template in dry-run, got: {output_arg}"

        # Warning message should be printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "DRY-RUN" in captured.out, \
            "Expected warning message in output"


def test_dry_run_with_good_url_shows_scene_name(monkeypatch, capsys):
    """--dry-run with a good URL should show the scene name in output."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(
            show_slug="good-show", season=1, episode=1,
            path="/vrtmax/a-z/good-show/1/good-show-s01e01",
            url="https://www.vrt.be/vrtmax/a-z/good-show/1/good-show-s01e01/"
        )
        mock_fetch.return_value = {
            "series": "Good Show", "season": "1", "episode": "1",
            "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
            "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
            "title": "Good Episode"
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Good.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/good-show/1/good-show-s01e01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--dry-run", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--simulate" in args
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        assert "Good.Show.S01E01" in output_arg, \
            f"Expected scene template in dry-run, got: {output_arg}"
        assert "%(title)s" not in output_arg, \
            "Fallback should NOT be used for good URL in dry-run"

        # Captured output should mention DRY-RUN with scene name
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out, \
            "Expected DRY-RUN prefix in output for dry-run mode"


def test_dry_run_with_mixed_urls(monkeypatch, capsys):
    """--dry-run with mixed good and bad URLs: both should be processed,
    good ones get scene names, bad ones get fallback."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)

        good_url = "https://www.vrt.be/vrtmax/a-z/good-show/1/good-show-s01e01/"
        bad_url = "https://www.vrt.be/vrtmax/a-z/#broken/1/#broken-s01e01/"

        mock_parse.side_effect = [
            MagicMock(show_slug="good-show", season=1, episode=1,
                      path="/vrtmax/a-z/good-show/1/good-show-s01e01",
                      url=good_url),
            ValueError("bad url with #"),
        ]

        mock_fetch.side_effect = [
            {
                "series": "Good Show", "season": "1", "episode": "1",
                "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
                "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
                "title": "Good Episode"
            },
            {},
        ]

        mock_classify.side_effect = [
            ContentType.TV,
            ContentType.UNKNOWN,
        ]

        mock_build.side_effect = [
            "Good.Show.S01E01.WEB-DL.1080p.AAC.x264.mp4",
        ]

        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--dry-run", good_url, bad_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        assert mock_run.call_count == 2, \
            f"Expected 2 subprocess.run calls in dry-run, got {mock_run.call_count}"

        # First call: good URL with scene template and --simulate
        first_args = mock_run.call_args_list[0][0][0]
        assert "--simulate" in first_args
        idx_o1 = first_args.index("-o")
        assert "Good.Show.S01E01" in first_args[idx_o1 + 1]

        # Second call: bad URL with fallback template and --simulate
        second_args = mock_run.call_args_list[1][0][0]
        assert "--simulate" in second_args
        idx_o2 = second_args.index("-o")
        assert "%(title)s.%(ext)s" in second_args[idx_o2 + 1]


# ===================================================================
# build_yt_dlp_args unit tests
# ===================================================================

def test_build_args_with_fallback_template(monkeypatch):
    """build_yt_dlp_args should use fallback template when output_template is None."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    from pathlib import Path
    with patch("thuis.main.get_yt_dlp_cmd", return_value=["/fake/yt-dlp"]):
        args = build_yt_dlp_args(["https://example.com/video"])
        idx_o = args.index("-o")
        output_arg = args[idx_o + 1]
        # When output_template is None, it defaults to "%(title)s.%(ext)s"
        assert "%(title)s.%(ext)s" in output_arg


def test_build_args_handles_dry_run_flag(monkeypatch):
    """build_yt_dlp_args should add --simulate when dry_run=True."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    from pathlib import Path
    with patch("thuis.main.get_yt_dlp_cmd", return_value=["/fake/yt-dlp"]):
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=True,
            output_template="Test.Show.S01E01.mp4"
        )
        assert "--simulate" in args


# ===================================================================
# get_credentials edge cases
# ===================================================================

def test_get_credentials_fallback_to_defaults(monkeypatch):
    """get_credentials returns default credentials when env vars are not set."""
    monkeypatch.delenv("VRT_EMAIL", raising=False)
    monkeypatch.delenv("VRT_PASSWORD", raising=False)
    email, password = get_credentials()
    assert email == "kuxelu@ipdeer.com"
    assert password == "Els123456"


def test_get_credentials_uses_env_vars(monkeypatch):
    """get_credentials returns env vars when set."""
    monkeypatch.setenv("VRT_EMAIL", "custom@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "custompass")
    email, password = get_credentials()
    assert email == "custom@example.com"
    assert password == "custompass"
