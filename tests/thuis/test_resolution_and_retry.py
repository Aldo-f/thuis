"""Unit tests for resolution parsing and retry skip logic in thuis.main.

Tests cover:
1. normalize_resolution() accepts int (1080) and str ("1080", "1080p")
   and always returns "1080p".
2. Resolution validation warns when resolution is not in VALIDATIONS.
3. build_yt_dlp_args() produces correct format string with and without
   resolution.
4. Retry logic skips downloaded file when --retry flag is set and file
   exists.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from thuis import classifier
from thuis.main import normalize_resolution, VALIDATIONS, build_yt_dlp_args


# ===================================================================
# normalize_resolution
# ===================================================================


class TestNormalizeResolution:
    """normalize_resolution returns canonical 'Np' form for int and str input."""

    def test_int_input(self):
        """Accepts int 1080 and returns '1080p'."""
        assert normalize_resolution(1080) == "1080p"

    def test_str_digits(self):
        """Accepts str '1080' and returns '1080p'."""
        assert normalize_resolution("1080") == "1080p"

    def test_str_with_p(self):
        """Accepts str '1080p' (already canonical) and returns '1080p'."""
        assert normalize_resolution("1080p") == "1080p"

    def test_str_uppercase_p(self):
        """Accepts str '1080P' and returns lowercase '1080p'."""
        assert normalize_resolution("1080P") == "1080p"

    def test_str_trailing_ps_stripped(self):
        """Multiple trailing 'p's are stripped correctly."""
        assert normalize_resolution("720pp") == "720p"

    def test_other_resolutions(self):
        """Works identically for 720, 1440, 2160."""
        assert normalize_resolution(720) == "720p"
        assert normalize_resolution("1440") == "1440p"
        assert normalize_resolution("2160p") == "2160p"


# ===========================================================================
# VALIDATIONS warning (via main's logic)
# ===========================================================================


class TestResolutionValidation:
    """Resolution not in VALIDATIONS triggers a warning in main()."""

    def test_known_resolution_does_not_warn(self, caplog):
        """Resolutions 720, 1080, 1440, 2160 are each treated as valid."""
        import logging
        from thuis.main import main

        caplog.set_level(logging.WARNING)

        test_urls = [
            "https://www.vrt.be/vrtmax/a-z/thuis/1/thuis-s01e01/",
        ]

        with patch("sys.argv", ["main.py", *test_urls, "--profile", "1080"]), \
             patch("thuis.main.patch_ytdlp_if_needed"), \
             patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
             patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
             patch("thuis.main.classifier.classify") as mock_classify, \
             patch("thuis.main.scene_namer.build_tv_filename") as mock_build, \
             patch("subprocess.run") as mock_run, \
             patch("os.access", return_value=True):

            mock_parse.return_value = MagicMock(
                show_slug="thuisow", season="1", episode="1",
                path="/vrtmax/a-z/thuisow/1/thuisow-s01e01/",
            )
            mock_fetch.return_value = {}
            mock_classify.return_value = None
            mock_build.return_value = "Thuisow.S01E01.mp4"
            mock_run.return_value = MagicMock(returncode=0)

            with pytest.raises(SystemExit):
                main()

        warnings = [r.message for r in caplog.records if "not in standard resolutions" in r.message]
        assert len(warnings) == 0, f"Unexpected warnings for valid resolution 720: {warnings}"

    def test_unknown_resolution_warns(self, caplog):
        """Resolution 480 (not in VALIDATIONS) logs a warning."""
        import logging
        from thuis.main import main

        caplog.set_level(logging.WARNING)

        test_urls = [
            "https://www.vrt.be/vrtmax/a-z/thuisow/1/thuisow-s01e01/",
        ]

        with patch("sys.argv", ["thuis.py", *test_urls, "--profile", "480"]), \
             patch("thuis.main.patch_ytdlp_if_needed"), \
             patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
             patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
             patch("thuis.main.classifier.classify") as mock_classify, \
             patch("thuis.main.scene_namer.build_tv_filename") as mock_build, \
             patch("subprocess.run") as mock_run, \
             patch("thuis.main.os.access", return_value=True):

            mock_parse.return_value = MagicMock(
                show_slug="thuisow", season="1", episode="1",
                path="/vrt/thuisow/1/thuisow-s01e01/",
            )
            mock_fetch.return_value = {}
            mock_classify.return_value = None
            mock_build.return_value = "Thuisow.S01E01.mp4"
            mock_run.return_value = MagicMock(returncode=0)

            with pytest.raises(SystemExit):
                main()

        warn_messages = [r.message for r in caplog.records]
        found = any("480" in m and "not in standard resolutions" in m for m in warn_messages)
        assert found, f"Expected warning about '480 not in standard resolutions', got: {warn_messages}"


# ===========================================================================
# build_yt_dlp_args — format string
# ===========================================================================


class TestBuildYtDlpArgs:
    """build_yt_dlp_args produces correct format selection strings."""

    def test_without_resolution(self):
        """When resolution is None, format is 'bestvideo+bestaudio'."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=False,
            output_dir=Path("media"),
            email="a@b.com",
            password="pw",
            resolution=None,
        )
        fmt_idx = args.index("-f") + 1 if "-f" in args else -1
        assert fmt_idx > 0, f"Expected '-f' flag in args: {args}"
        assert args[fmt_idx] == "bestvideo+bestaudio", (
            f"Expected 'bestvideo+bestaudio' without resolution, got {args[fmt_idx]}"
        )

    def test_with_resolution(self):
        """When resolution='1080p', format is 'bestvideo[height<=1080]+bestaudio'."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=False,
            output_dir=Path("output"),
            email="a@b.com",
            password="pw",
            resolution="1080p",
        )
        fmt_idx = args.index("-f") + 1 if "-f" in args else -1
        assert fmt_idx > 0, f"Expected '-f' flag in args: {args}"
        assert args[fmt_idx] == "bestvideo[height<=1080]+bestaudio", (
            f"Expected 'bestvideo[height<=1080]+bestaudio', got {args[fmt_idx]}"
        )

    def test_with_resolution_numeric_string(self):
        """When resolution='2160', the number is parsed and format uses height<=2160."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=False,
            output_dir=Path("output"),
            email="a@b.com",
            password="pw",
            resolution="2160",
        )
        fmt_idx = args.index("-f") + 1
        assert args[fmt_idx] == "bestvideo[height<=2160]+bestaudio"

    def test_with_resolution_int(self):
        """When resolution=720 (int), the number is parsed and format uses height<=720."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=False,
            output_dir=Path("output"),
            email="a@b.com",
            password="pw",
            resolution="720p",
        )
        fmt_idx = args.index("-f") + 1
        assert args[fmt_idx] == "bestvideo[height<=720]+bestaudio"

    def test_dry_run_adds_simulate(self):
        """dry_run=True adds --simulate to args."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=True,
            output_dir=Path("output"),
            email="a@b.com",
            password="pw",
            resolution=None,
        )
        assert "--simulate" in args, f"Expected --simulate in dry-run args: {args}"

    def test_credentials_in_args(self):
        """Email and password appear as --username and --password."""
        args = build_yt_dlp_args(
            ["https://example.com/video"],
            dry_run=False,
            output_dir=Path("output"),
            email="user@test.com",
            password="secret",
            resolution=None,
        )
        assert "--username" in args
        assert "user@test.com" in args
        assert "--password" in args
        assert "secret" in args


# ===========================================================================
# Retry skip logic
# ===========================================================================


class TestRetrySkip:
    """When --retry is set and the output file exists, the URL is skipped."""

    def test_retry_skips_existing_file(self, caplog):
        """If --retry flag is set and the output file already exists,
        the URL is skipped and subprocess.run is NOT called."""
        import logging
        from thuis.main import main

        caplog.set_level(logging.INFO)

        test_url = "https://www.vrt.be/vrtmax/a-z/thuisow/1/thuisow-s01e01/"

        with patch("sys.argv", ["thuis.py", test_url, "--retry"]), \
             patch("thuis.main.patch_ytdlp_if_needed"), \
             patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
             patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
             patch("thuis.main.metadata_fetcher.fetch_preview_height", return_value=None), \
             patch("thuis.main.classifier.classify") as mock_classify, \
             patch("thuis.main.scene_namer.build_tv_filename") as mock_build, \
             patch("thuis.main.os.access", return_value=True), \
             patch("thuis.main.Path.exists", return_value=True) as mock_exists, \
             patch("thuis.main.Path.glob", return_value=[Path("Thuisow.S01E01.mp4")]) as mock_glob, \
             patch("subprocess.run") as mock_run:

            mock_parse.return_value = MagicMock(
                show_slug="thuisow", season="1", episode="1",
                path="/vrt/thuisow/1/thuisow-s01e01/",
            )
            mock_fetch.return_value = {"series": "Test Show"}
            mock_classify.return_value = classifier.ContentType.TV
            mock_build.return_value = "Thuisow.S01E01.mp4"
            mock_run.return_value = MagicMock(returncode=0)

            with pytest.raises(SystemExit):
                main()

            # Verify subprocess.run was never called (skip happened)
            mock_run.assert_not_called()

            # Verify the skip log message
            skip_messages = [
                r.message for r in caplog.records if "bestaat al als" in r.message
            ]
            assert any(test_url in m for m in skip_messages), (
                f"Expected skip log for {test_url}, got: {skip_messages}"
            )

    def test_retry_runs_if_file_does_not_exist(self):
        """If --retry flag is set but output file does NOT exist,
        subprocess.run IS called normally."""
        from thuis.main import main

        test_url = "https://www.vrt.be/vrtmax/a-z/thuisow/1/thuisow-s01e01/"

        with patch("sys.argv", ["thuis.py", test_url, "--retry"]), \
             patch("thuis.main.patch_ytdlp_if_needed"), \
             patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
             patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
             patch("thuis.main.metadata_fetcher.fetch_preview_height", return_value=None), \
             patch("thuis.main.classifier.classify") as mock_classify, \
             patch("thuis.main.scene_namer.build_tv_filename") as mock_build, \
             patch("thuis.main.os.access", return_value=True), \
             patch("thuis.main.Path.exists", return_value=False) as mock_exists, \
             patch("subprocess.run") as mock_run:

            mock_parse.return_value = MagicMock(
                show_slug="thuisow", season="1", episode="1",
                path="/vrt/thuisow/1/thuisow-s01e01/",
            )
            mock_fetch.return_value = {}
            mock_classify.return_value = None
            mock_build.return_value = "Thuisow.S01E01.mp4"
            mock_run.return_value = MagicMock(returncode=0)

            with pytest.raises(SystemExit):
                main()

            mock_run.assert_called_once()

    def test_no_retry_runs_normally(self):
        """When --retry is not set, the file existence check is not performed
        and subprocess.run is called."""
        from thuis.main import main

        test_url = "https://www.vrt.be/vrtmax/a-z/thuisow/1/thuisow-s01e01/"

        with patch("sys.argv", ["thuis.py", test_url]), \
             patch("thuis.main.patch_ytdlp_if_needed"), \
             patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
             patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
             patch("thuis.main.metadata_fetcher.fetch_preview_height", return_value=None), \
             patch("thuis.main.classifier.classify") as mock_classify, \
             patch("thuis.main.scene_namer.build_tv_filename") as mock_build, \
             patch("thuis.main.os.access", return_value=True), \
             patch("subprocess.run") as mock_run:

            mock_parse.return_value = MagicMock(
                show_slug="thuisow", season="1", episode="1",
                path="/vrt/thuisow/1/thuisow-s01e01/",
            )
            mock_fetch.return_value = {}
            mock_classify.return_value = None
            mock_build.return_value = "Thuisow.S01E01.mp4"
            mock_run.return_value = MagicMock(returncode=0)

            with pytest.raises(SystemExit):
                main()

            mock_run.assert_called_once()