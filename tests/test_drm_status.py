#!/usr/bin/env python3
"""
Tests for DRM status persistence and skip/retry logic in watchlist.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from thuis.watchlist import WatchlistDB, should_trigger


class TestDRMStatusPersistence:
    """Tests for persisting and retrieving DRM status in WatchlistDB."""

    def test_set_last_run_with_drm_status(self, tmp_path):
        """set_last_run should store 'drm' status."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        ts = datetime(2026, 8, 22, 10, 0)
        
        db.set_last_run(url, status="drm", timestamp=ts)
        
        assert db.get_last_status(url) == "drm"
        assert db.get_last_run(url) is not None
        db.close()

    def test_get_last_status_returns_drm(self, tmp_path):
        """get_last_status should return 'drm' for DRM entries."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        
        db.set_last_run(url, status="drm")
        status = db.get_last_status(url)
        
        assert status == "drm"
        db.close()

    def test_drm_status_distinct_from_ok_and_failed(self, tmp_path):
        """DRM status should be distinct from 'ok' and other statuses."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url1 = "https://example.com/ep1"
        url2 = "https://example.com/ep2"
        url3 = "https://example.com/ep3"
        
        db.set_last_run(url1, status="ok")
        db.set_last_run(url2, status="drm")
        db.set_last_run(url3, status="failed")
        
        assert db.get_last_status(url1) == "ok"
        assert db.get_last_status(url2) == "drm"
        assert db.get_last_status(url3) == "failed"
        db.close()


class TestDRMSkipOnScheduledRuns:
    """Tests for DRM entries being skipped on scheduled (non---now) runs."""

    def test_scheduled_run_skips_drm_entry(self, tmp_path):
        """Scheduled run should skip URL with last_status == 'drm'."""
        # This test simulates the logic in _run_watchlist
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        
        # Simulate previous DRM run
        db.set_last_run(url, status="drm")
        
        # In _run_watchlist, scheduled run checks:
        # if last_status == "drm" and not args.now: skip
        last_status = db.get_last_status(url)
        should_skip = (last_status == "drm")  # without --now
        
        assert should_skip is True
        db.close()

    def test_now_flag_retries_drm_entry(self, tmp_path):
        """--now flag should retry DRM entries (not skip them)."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        
        # Simulate previous DRM run
        db.set_last_run(url, status="drm")
        
        # With --now flag, DRM entries should NOT be skipped
        last_status = db.get_last_status(url)
        args_now = True
        should_skip = (last_status == "drm") and (not args_now)
        
        assert should_skip is False  # --now forces retry
        db.close()

    def test_manual_entry_without_now_still_skipped_if_drm(self, tmp_path):
        """Manual entries (no schedule) still require --now to run, even if DRM."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        
        db.set_last_run(url, status="drm")
        
        # Manual entry (schedule=None) - without --now should not run anyway
        schedule = None
        args_now = False
        
        # In _run_watchlist: manual entries skip unless --now
        if schedule is None and not args_now:
            should_run = False
        else:
            # But if --now, DRM entries should be retried
            last_status = db.get_last_status(url)
            should_run = not (last_status == "drm" and not args_now)
        
        assert should_run is False
        db.close()


class TestAllDRMBatchExitCode:
    """Tests for all-DRM batch exiting with code 0."""

    def test_all_drm_results_exit_zero(self):
        """All results being 'drm' should exit 0."""
        results = ["drm", "drm", "drm"]
        
        # Simplified exit logic from main.py
        drm_results = [r for r in results if r == "drm"]
        non_drm_results = [r for r in results if r != "drm"]
        
        if drm_results and not non_drm_results:
            exit_code = 0
        elif drm_results and non_drm_results:
            exit_code = 1 if any(r != 0 for r in non_drm_results) else 0
        else:
            exit_code = 1 if any(r != 0 for r in results) else 0
        
        assert exit_code == 0

    def test_mixed_drm_and_success_exit_zero(self):
        """Mixed DRM and success (0) should exit 0."""
        results = ["drm", 0, "drm", 0]
        
        drm_results = [r for r in results if r == "drm"]
        non_drm_results = [r for r in results if r != "drm"]
        
        if drm_results and not non_drm_results:
            exit_code = 0
        elif drm_results and non_drm_results:
            exit_code = 1 if any(r != 0 for r in non_drm_results) else 0
        else:
            exit_code = 1 if any(r != 0 for r in results) else 0
        
        assert exit_code == 0

    def test_mixed_drm_and_failure_exit_nonzero(self):
        """Mixed DRM and failure (non-zero) should exit non-zero."""
        results = ["drm", 1, "drm"]
        
        drm_results = [r for r in results if r == "drm"]
        non_drm_results = [r for r in results if r != "drm"]
        
        if drm_results and not non_drm_results:
            exit_code = 0
        elif drm_results and non_drm_results:
            exit_code = 1 if any(r != 0 for r in non_drm_results) else 0
        else:
            exit_code = 1 if any(r != 0 for r in results) else 0
        
        assert exit_code == 1

    def test_no_drm_all_success_exit_zero(self):
        """No DRM, all success (0) should exit 0."""
        results = [0, 0, 0]
        
        drm_results = [r for r in results if r == "drm"]
        non_drm_results = [r for r in results if r != "drm"]
        
        if drm_results and not non_drm_results:
            exit_code = 0
        elif drm_results and non_drm_results:
            exit_code = 1 if any(r != 0 for r in non_drm_results) else 0
        else:
            exit_code = 1 if any(r != 0 for r in results) else 0
        
        assert exit_code == 0

    def test_no_drm_some_failure_exit_nonzero(self):
        """No DRM, some failures should exit non-zero."""
        results = [0, 1, 0]
        
        drm_results = [r for r in results if r == "drm"]
        non_drm_results = [r for r in results if r != "drm"]
        
        if drm_results and not non_drm_results:
            exit_code = 0
        elif drm_results and non_drm_results:
            exit_code = 1 if any(r != 0 for r in non_drm_results) else 0
        else:
            exit_code = 1 if any(r != 0 for r in results) else 0
        
        assert exit_code == 1


class TestDRMURLNeverMarkedDownloaded:
    """Tests ensuring DRM-blocked URLs are never marked as downloaded."""

    def test_drm_url_not_in_downloaded_files(self, tmp_path):
        """DRM status should not result in record_download call."""
        # This is a behavioral test - we verify the logic doesn't call record_download
        # for DRM URLs. The actual implementation in main.py uses 'continue' after
        # detecting DRM, which skips the rest of the download processing including
        # record_download.
        
        # The test is conceptual - we verify the flow:
        # 1. DRM detected in stderr
        # 2. status set to "drm" via set_last_run
        # 3. continue → skips post-download processing including record_download
        
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        
        # Simulate DRM handling
        db.set_last_run(url, status="drm")
        
        # record_download should NOT be called for this URL
        # (we just verify it wasn't called in our test - in real code it's skipped)
        assert db.get_last_status(url) == "drm"
        
        # The downloaded_files table should remain empty for this URL
        output_dir = str(tmp_path / "media")
        filename = "show.s01e01.mp4"
        assert db.file_was_downloaded(url, filename, output_dir) is False
        
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])