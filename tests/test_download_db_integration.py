"""Integration tests for WatchlistDB in the main download flow.

Tests the database integration points added for fast duplicate checking:
- record_download called on successful download
- file_was_downloaded skips download when file already recorded
- glob fallback still works when DB returns False
- record_download NOT called for dry-run
- record_download NOT called for failed downloads
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Add repository root to sys.path so we can import thuis.main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from thuis.main import main
from thuis.classifier import ContentType


class TestDownloadDBIntegration:
    """Tests for WatchlistDB integration in the main download flow."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, tmp_path, monkeypatch):
        """Set up common mocks for all tests."""
        self.output_dir = tmp_path / "downloads"
        self.output_dir.mkdir()
        self.test_url = "https://www.vrt.be/vrtmax/a-z/thuis/1/thuis-s01e01/"
        self.scene_template = "Thuis.S01E01.1080p.WEB-DL.AAC.x264.mp4"

        # Mock environment variables
        monkeypatch.setenv("VRT_EMAIL", "test@example.com")
        monkeypatch.setenv("VRT_PASSWORD", "testpass")

        # Common patches
        self.patches = {
            'run_ytdlp': patch("thuis.main._run_ytdlp_with_drm_detection"),
            'get_yt_dlp_location': patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"),
            'patch_ytdlp': patch("thuis.main.patch_ytdlp_if_needed"),
            'parse_url': patch("thuis.main.url_parser.parse_vrt_url"),
            'fetch_metadata': patch("thuis.main.metadata_fetcher.fetch_metadata"),
            'classify': patch("thuis.main.classifier.classify"),
            'build_tv_filename': patch("thuis.main.scene_namer.build_tv_filename"),
            'normalize_show_name': patch("thuis.main.scene_namer.normalize_show_name"),
        }

        # Start all patches
        self.mocks = {name: p.start() for name, p in self.patches.items()}

        # Configure common mock return values
        self.mocks['parse_url'].return_value = MagicMock(
            show_slug="thuis",
            season=1,
            episode=1,
            path="/vrtmax/a-z/thuis/1/thuis-s01e01/",
            url=self.test_url
        )
        self.mocks['fetch_metadata'].return_value = {
            "series": "Thuis",
            "season": 1,
            "episode": 1,
            "height": "1080",
            "vcodec_raw": "avc1",
            "acodec_raw": "mp4a"
        }
        self.mocks['classify'].return_value = ContentType.TV
        self.mocks['build_tv_filename'].return_value = self.scene_template
        self.mocks['normalize_show_name'].return_value = "Thuis"

        yield

        # Stop all patches
        for p in self.patches.values():
            p.stop()

    def _run_main(self, args):
        """Helper to run main() with given args."""
        original_argv = sys.argv
        try:
            sys.argv = ["main.py"] + args
            try:
                main()
            except SystemExit as e:
                return e.code
        finally:
            sys.argv = original_argv
        return 0

    # -------------------------------------------------------------------------
    # Test 1: record_download called on successful download
    # -------------------------------------------------------------------------
    def test_record_download_called_on_success(self, monkeypatch):
        """Mock yt-dlp to return 0, verify record_download is called with correct args."""
        # Mock yt-dlp to return success
        self.mocks['run_ytdlp'].return_value = (0, "")

        # Mock WatchlistDB to track calls
        with patch("thuis.main.watchlist.WatchlistDB") as mock_db_class:
            mock_db = MagicMock()
            mock_db.file_was_downloaded.return_value = False  # Not in DB, proceed
            mock_db_class.return_value = mock_db

            rc = self._run_main(["--output-dir", str(self.output_dir), self.test_url])

        # Verify successful exit
        assert rc == 0

        # Verify record_download was called with correct args
        mock_db.record_download.assert_called_once_with(
            self.test_url, self.scene_template, str(self.output_dir)
        )
        # close() called twice: once for pre-download check, once for record_download
        assert mock_db.close.call_count == 2

    # -------------------------------------------------------------------------
    # Test 2: file_was_downloaded skips download when file already recorded
    # -------------------------------------------------------------------------
    def test_file_was_downloaded_skips_download(self, monkeypatch):
        """Mock file_was_downloaded to return True, verify download is skipped."""
        # Mock WatchlistDB to return True for file_was_downloaded
        with patch("thuis.main.watchlist.WatchlistDB") as mock_db_class:
            mock_db = MagicMock()
            mock_db.file_was_downloaded.return_value = True  # Already in DB, skip
            mock_db_class.return_value = mock_db

            rc = self._run_main(["--output-dir", str(self.output_dir), self.test_url])

        # Verify successful exit (skipped is not an error)
        assert rc == 0

        # Verify file_was_downloaded was called
        mock_db.file_was_downloaded.assert_called_once_with(
            self.test_url, self.scene_template, str(self.output_dir)
        )
        mock_db.close.assert_called_once()

        # Verify yt-dlp was NOT called (download skipped)
        self.mocks['run_ytdlp'].assert_not_called()

        # Verify record_download was NOT called
        mock_db.record_download.assert_not_called()

    # -------------------------------------------------------------------------
    # Test 3: glob fallback when DB returns False
    # -------------------------------------------------------------------------
    def test_glob_fallback_when_db_returns_false(self, monkeypatch):
        """Mock file_was_downloaded to return False, verify glob fallback still works."""
        # Mock yt-dlp to return success
        self.mocks['run_ytdlp'].return_value = (0, "")

        # Create a file that matches the glob pattern (simulating existing download)
        show_norm = "Thuis"
        res_part = ".1080p"
        existing_file = self.output_dir / f"{show_norm}.S01E01{res_part}.WEB-DL.AAC.x264.mp4"
        existing_file.write_text("dummy")

        # Mock WatchlistDB to return False for file_was_downloaded (not in DB)
        with patch("thuis.main.watchlist.WatchlistDB") as mock_db_class:
            mock_db = MagicMock()
            mock_db.file_was_downloaded.return_value = False  # Not in DB
            mock_db_class.return_value = mock_db

            rc = self._run_main(["--output-dir", str(self.output_dir), self.test_url])

        # Verify successful exit (skipped via glob fallback)
        assert rc == 0

        # Verify file_was_downloaded was called
        mock_db.file_was_downloaded.assert_called_once_with(
            self.test_url, self.scene_template, str(self.output_dir)
        )
        mock_db.close.assert_called()

        # Verify yt-dlp was NOT called (skipped via glob fallback)
        self.mocks['run_ytdlp'].assert_not_called()

        # Verify record_download was NOT called
        mock_db.record_download.assert_not_called()

    # -------------------------------------------------------------------------
    # Test 4: record_download NOT called for dry-run
    # -------------------------------------------------------------------------
    def test_no_record_for_dry_run(self, monkeypatch):
        """Verify record_download is NOT called when args.dry_run is True."""
        # Mock yt-dlp to return success
        self.mocks['run_ytdlp'].return_value = (0, "")

        # Mock WatchlistDB to track calls
        with patch("thuis.main.watchlist.WatchlistDB") as mock_db_class:
            mock_db = MagicMock()
            mock_db.file_was_downloaded.return_value = False  # Not in DB
            mock_db_class.return_value = mock_db

            rc = self._run_main(["--dry-run", "--output-dir", str(self.output_dir), self.test_url])

        # Verify successful exit
        assert rc == 0

        # Verify yt-dlp was called (with --simulate)
        self.mocks['run_ytdlp'].assert_called_once()

        # Verify file_was_downloaded was still called for dedup check
        mock_db.file_was_downloaded.assert_called_once()

        # Verify record_download was NOT called (dry-run mode)
        mock_db.record_download.assert_not_called()

        mock_db.close.assert_called()

    # -------------------------------------------------------------------------
    # Test 5: record_download NOT called for failed download
    # -------------------------------------------------------------------------
    def test_no_record_for_failed_download(self, monkeypatch):
        """Verify record_download is NOT called when returncode != 0."""
        # Mock yt-dlp to return failure
        self.mocks['run_ytdlp'].return_value = (1, "ERROR: Something went wrong")

        # Mock WatchlistDB to track calls
        with patch("thuis.main.watchlist.WatchlistDB") as mock_db_class:
            mock_db = MagicMock()
            mock_db.file_was_downloaded.return_value = False  # Not in DB
            mock_db_class.return_value = mock_db

            rc = self._run_main(["--output-dir", str(self.output_dir), self.test_url])

        # Verify non-zero exit (download failed)
        assert rc != 0

        # Verify yt-dlp was called
        self.mocks['run_ytdlp'].assert_called_once()

        # Verify file_was_downloaded was called for dedup check
        mock_db.file_was_downloaded.assert_called_once()

        # Verify record_download was NOT called (download failed)
        mock_db.record_download.assert_not_called()

        mock_db.close.assert_called()


if __name__ == "__main__":
    # Simple runner for debugging. If pytest isn't available, exit gracefully.
    try:
        import pytest
    except Exception:
        print("pytest not available; skipping test runner")
    else:
        pytest.main([__file__, "-v"])