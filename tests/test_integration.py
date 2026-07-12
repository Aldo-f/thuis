"""End-to-end integration tests for the thuis download pipeline.

All external calls (yt-dlp subprocess, network) are mocked so tests are
fast, deterministic, and require no real VRT MAX access.

Test scenarios:
  - TV URL  → TV scene filename in -o argument
  - Special URL → special scene filename in -o argument
  - Movie URL → movie scene filename in -o argument
  - Fallback URL → %(title)s.%(ext)s when content type is UNKNOWN
  - Multi-URL batch → each URL processed with correct scene filename
  - Dry-run mode → --simulate flag with scene filename still applied
"""

import sys
import os

# Add src/ to sys.path so we can import thuis modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from unittest.mock import patch, MagicMock

from thuis.main import main
from thuis.classifier import ContentType
from thuis.url_parser import VrtUrlInfo


# ---------------------------------------------------------------------------
# TV URL
# ---------------------------------------------------------------------------

def test_integration_tv_url(monkeypatch):
    """TV URL → TV scene filename in yt-dlp -o argument."""
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
        mock_parse.return_value = VrtUrlInfo(
            show_slug="test-show",
            season=1,
            episode=1,
            path="/vrtmax/a-z/test-show/1/test-show-s01a01/",
            url="https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01a01/",
        )
        mock_fetch.return_value = {
            "series": "Test Show",
            "season": "1",
            "episode": "1",
            "height": "1080p",
            "vcodec_raw": "avc1",
            "acodec_raw": "mp4a",
            "vcodec_label": "x264",
            "acodec_label": "AAC",
            "ext": "mp4",
            "title": "Test Show S01E01",
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01a01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # Verify subprocess.run called exactly once
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]

        # Verify scene filename in -o
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg, \
            "Should NOT fall back to default template for TV content"
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg

        # Verify URL is passed to yt-dlp
        assert test_url in called_args

        # Verify credentials
        assert "--username" in called_args
        assert "test@example.com" in called_args
        assert "--password" in called_args
        assert "testpass" in called_args


# ---------------------------------------------------------------------------
# Special URL
# ---------------------------------------------------------------------------

def test_integration_special_url(monkeypatch):
    """Special URL → special scene filename in yt-dlp -o argument."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_special_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = VrtUrlInfo(
            show_slug="test-show",
            season=0,
            episode=0,
            path="/vrtmax/a-z/test-show/extra-s/test-show-extra/",
            url="https://www.vrt.be/vrtmax/a-z/test-show/extra-s/test-show-extra/",
        )
        mock_fetch.return_value = {
            "series": "Test Show",
            "season": None,
            "episode": None,
            "height": "1080p",
            "vcodec_raw": "avc1",
            "acodec_raw": "mp4a",
            "vcodec_label": "x264",
            "acodec_label": "AAC",
            "ext": "mp4",
            "title": "Test Show Extra",
        }
        mock_classify.return_value = ContentType.SPECIAL
        mock_build.return_value = "Test.Show.Special.1080p.WEB-DL.AAC.x264.mp4"

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
        called_args = mock_run.call_args[0][0]
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg, \
            "Should NOT fall back to default template for special content"
        assert "Test.Show.Special.1080p.WEB-DL.AAC.x264.mp4" in output_arg
        assert test_url in called_args


# ---------------------------------------------------------------------------
# Movie URL
# ---------------------------------------------------------------------------

def test_integration_movie_url(monkeypatch):
    """Movie URL → movie scene filename in yt-dlp -o argument."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_movie_filename") as mock_build:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = VrtUrlInfo(
            show_slug="a-movie-title",
            season=0,
            episode=0,
            path="/vrtmax/a-z/a-movie-title/0/",
            url="https://www.vrt.be/vrtmax/a-z/a-movie-title/0/",
        )
        mock_fetch.return_value = {
            "series": None,
            "season": "2023",
            "episode": None,
            "height": "2160p",
            "vcodec_raw": "hvc1",
            "acodec_raw": "ec-3",
            "vcodec_label": "x265",
            "acodec_label": "EAC3",
            "ext": "mp4",
            "title": "A Movie Title",
        }
        mock_classify.return_value = ContentType.MOVIE
        mock_build.return_value = "A.Movie.Title.2023.2160p.WEB-DL.EAC3.x265.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/a-movie-title/0/"
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
        called_args = mock_run.call_args[0][0]
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg, \
            "Should NOT fall back to default template for movie content"
        assert "A.Movie.Title.2023.2160p.WEB-DL.EAC3.x265.mp4" in output_arg
        assert test_url in called_args


# ---------------------------------------------------------------------------
# Fallback URL (UNKNOWN content type)
# ---------------------------------------------------------------------------

def test_integration_fallback_url(monkeypatch):
    """UNKNOWN content type → fallback to %(title)s.%(ext)s."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify:

        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = VrtUrlInfo(
            show_slug="unknown-content",
            season=0,
            episode=0,
            path="/vrtmax/a-z/unknown-content/something/",
            url="https://www.vrt.be/vrtmax/a-z/unknown-content/something/",
        )
        # Metadata fetch succeeds but classifier returns UNKNOWN
        mock_fetch.return_value = {}
        mock_classify.return_value = ContentType.UNKNOWN

        test_url = "https://www.vrt.be/vrtmax/a-z/unknown-content/something/"
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
        called_args = mock_run.call_args[0][0]
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        # Fallback must use the default template
        assert "%(title)s.%(ext)s" in output_arg, \
            "UNKNOWN content should fall back to default template"
        assert test_url in called_args


# ---------------------------------------------------------------------------
# Multi-URL batch
# ---------------------------------------------------------------------------

def test_integration_multi_url_batch(monkeypatch):
    """Multiple URLs → each processed with correct scene filename."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")

    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build_tv, \
         patch("thuis.main.scene_namer.build_special_filename") as mock_build_special:

        mock_run.return_value = MagicMock(returncode=0)

        # -- side effects for two different URLs --
        url1 = "https://www.vrt.be/vrtmax/a-z/show-a/1/show-a-s01a01/"
        url2 = "https://www.vrt.be/vrtmax/a-z/show-b/extra-s/show-b-extra/"

        mock_parse.side_effect = [
            VrtUrlInfo(
                show_slug="show-a", season=1, episode=1,
                path="/vrtmax/a-z/show-a/1/show-a-s01a01/",
                url=url1,
            ),
            VrtUrlInfo(
                show_slug="show-b", season=0, episode=0,
                path="/vrtmax/a-z/show-b/extra-s/show-b-extra/",
                url=url2,
            ),
        ]
        mock_fetch.side_effect = [
            {
                "series": "Show A", "season": "1", "episode": "1",
                "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
                "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
                "title": "Show A S01E01",
            },
            {
                "series": "Show B", "season": None, "episode": None,
                "height": "720p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
                "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
                "title": "Show B Extra",
            },
        ]
        mock_classify.side_effect = [ContentType.TV, ContentType.SPECIAL]
        mock_build_tv.return_value = "Show.A.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        mock_build_special.return_value = "Show.B.Special.720p.WEB-DL.AAC.x264.mp4"

        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", url1, url2]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # Two subprocess calls — one per URL
        assert mock_run.call_count == 2

        # --- First call: TV URL ---
        first_args = mock_run.call_args_list[0][0][0]
        assert url1 in first_args
        assert "-o" in first_args
        idx_o1 = first_args.index("-o")
        assert "%(title)s" not in first_args[idx_o1 + 1]
        assert "Show.A.S01E01.1080p.WEB-DL.AAC.x264.mp4" in first_args[idx_o1 + 1]

        # --- Second call: Special URL ---
        second_args = mock_run.call_args_list[1][0][0]
        assert url2 in second_args
        assert "-o" in second_args
        idx_o2 = second_args.index("-o")
        assert "%(title)s" not in second_args[idx_o2 + 1]
        assert "Show.B.Special.720p.WEB-DL.AAC.x264.mp4" in second_args[idx_o2 + 1]

        # Both calls pass credentials
        for call_args in mock_run.call_args_list:
            args = call_args[0][0]
            assert "--username" in args
            assert "test@example.com" in args
            assert "--password" in args
            assert "testpass" in args


# ---------------------------------------------------------------------------
# Dry-run mode
# ---------------------------------------------------------------------------

def test_integration_dry_run_mode(monkeypatch):
    """--dry-run → --simulate flag passed, scene filename still applied."""
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
        mock_parse.return_value = VrtUrlInfo(
            show_slug="test-show",
            season=1,
            episode=1,
            path="/vrtmax/a-z/test-show/1/test-show-s01a01/",
            url="https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01a01/",
        )
        mock_fetch.return_value = {
            "series": "Test Show", "season": "1", "episode": "1",
            "height": "1080p", "vcodec_raw": "avc1", "acodec_raw": "mp4a",
            "vcodec_label": "x264", "acodec_label": "AAC", "ext": "mp4",
            "title": "Test Show S01E01",
        }
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"

        test_url = "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s01a01/"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--dry-run", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv

        # subprocess.run is still called once, but with --simulate
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]

        # Dry-run flag must translate to --simulate for yt-dlp
        assert "--simulate" in called_args, \
            "Dry-run mode should pass --simulate to yt-dlp"

        # Scene filename should still be in -o, NOT the default template
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg, \
            "Dry-run should still use scene filename, not fallback template"
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg

        # Credentials still present
        assert "--username" in called_args
        assert "test@example.com" in called_args
        assert "--password" in called_args
        assert "testpass" in called_args

        # URL is passed
        assert test_url in called_args
