#!/usr/bin/env python3
"""
Tests for watchlist parser, schedule checker, and state database.
"""

import os
import sys
import sqlite3
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from thuis.watchlist import (
    parse_watchlist_file,
    should_trigger,
    WatchlistEntry,
    WatchlistFile,
    resolve_output_dir,
    WatchlistDB,
    generate_scene_filename,
    check_file_exists,
)


class TestParseWatchlistFile:
    """Tests for parsing watchlist file format."""

    def test_parse_first_line_as_output_dir(self, tmp_path):
        """First non-comment line is the output directory."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""media
https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/
""")
        result = parse_watchlist_file(str(wl_file))
        assert isinstance(result, WatchlistFile)
        assert result.output_dir == "media"
        assert len(result.entries) == 1
        assert result.entries[0].url == "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/"

    def test_parse_first_line_with_home(self, tmp_path):
        """First line with ~ is treated as output dir."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""~/downloads
https://www.example.com/episode/
""")
        result = parse_watchlist_file(str(wl_file))
        assert result.output_dir == "~/downloads"

    def test_parse_first_line_absolute(self, tmp_path):
        """First line with / is treated as output dir."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""/mnt/HDD1/media
https://www.example.com/episode/
""")
        result = parse_watchlist_file(str(wl_file))
        assert result.output_dir == "/mnt/HDD1/media"

    def test_skip_comment_lines(self, tmp_path):
        """Lines starting with # are comments, not output dir."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""# This is a comment
# Another comment
media
https://www.example.com/episode/
""")
        result = parse_watchlist_file(str(wl_file))
        assert result.output_dir == "media"

    def test_parse_schedule_tag(self, tmp_path):
        """[schedule] tag at start of URL line."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""media
[daily 08:30] https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/
""")
        result = parse_watchlist_file(str(wl_file))
        assert len(result.entries) == 1
        assert result.entries[0].schedule == "daily 08:30"
        assert result.entries[0].url == "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/"

    def test_parse_multiple_entries(self, tmp_path):
        """Multiple URL lines with different schedules."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""media
[daily] https://www.example.com/show1/ep1
[weekly] https://www.example.com/show2/ep1
https://www.example.com/show3/ep1
""")
        result = parse_watchlist_file(str(wl_file))
        assert len(result.entries) == 3
        assert result.entries[0].schedule == "daily"
        assert result.entries[1].schedule == "weekly"
        assert result.entries[2].schedule is None  # No tag = None

    def test_skip_blank_and_comment_lines(self, tmp_path):
        """Empty lines and comment lines are skipped."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""
# Comment line
media

# Another comment

[daily] https://www.example.com/ep1
""")
        result = parse_watchlist_file(str(wl_file))
        assert result.output_dir == "media"
        assert len(result.entries) == 1

    def test_parse_multiple_schedules_comma_separated(self, tmp_path):
        """Comma-separated schedules like [monday 8:00, wednesday 7:00]."""
        wl_file = tmp_path / "test.txt"
        wl_file.write_text("""media
[monday 8:00, wednesday 7:00, weekend 8:00] https://www.example.com/ep1
""")
        result = parse_watchlist_file(str(wl_file))
        assert result.entries[0].schedule == "monday 8:00, wednesday 7:00, weekend 8:00"


class TestResolveOutputDir:
    """Tests for output directory path resolution."""

    def test_resolve_home_path(self):
        """~ expands to user's home directory."""
        result = resolve_output_dir("~/downloads")
        assert result == str(Path.home() / "downloads")

    def test_resolve_absolute_path(self):
        """Absolute paths are used as-is."""
        path = "/mnt/HDD1/media"
        result = resolve_output_dir(path)
        assert result == path

    def test_resolve_relative_path(self, tmp_path, monkeypatch):
        """Relative paths are relative to cwd."""
        monkeypatch.chdir(tmp_path)
        result = resolve_output_dir("media")
        assert result == str(tmp_path / "media")

    def test_resolve_empty_falls_back_to_env(self, monkeypatch):
        """Empty output_dir falls back to OUTPUT_DIR env."""
        monkeypatch.setenv("OUTPUT_DIR", "/env/override")
        result = resolve_output_dir("")
        assert result == "/env/override"

    def test_resolve_empty_falls_back_to_media(self, monkeypatch):
        """Empty output_dir with no env falls back to 'media'."""
        monkeypatch.delenv("OUTPUT_DIR", raising=False)
        result = resolve_output_dir("")
        assert result == "media"


class TestParseSchedule:
    """Tests for schedule parsing and checking."""

    @pytest.mark.parametrize("schedule,now,last_run,expected", [
        # daily: runs once per day
        ("daily", datetime(2026, 8, 22, 10, 0), datetime(2026, 8, 22, 8, 0), False),  # Same day, already ran
        ("daily", datetime(2026, 8, 23, 8, 0), datetime(2026, 8, 22, 8, 0), True),     # New day
        ("daily", datetime(2026, 8, 22, 15, 0), None, True),                            # Never ran
        # daily with time: runs if current time >= specified time AND not run today
        ("daily 08:30", datetime(2026, 8, 22, 9, 0), None, True),                        # After 8:30, not run
        ("daily 08:30", datetime(2026, 8, 22, 7, 0), None, False),                       # Before 8:30
        ("daily 08:30", datetime(2026, 8, 22, 9, 0), datetime(2026, 8, 22, 9, 30), False),  # Already ran today
        ("daily 08:30", datetime(2026, 8, 23, 9, 0), datetime(2026, 8, 22, 9, 30), True),    # New day
        # weekday-specific
        ("monday", datetime(2026, 8, 24, 0, 0), None, True),  # Monday
        ("monday", datetime(2026, 8, 25, 0, 0), None, False),  # Tuesday
        ("monday 08:00", datetime(2026, 8, 24, 9, 0), datetime(2026, 8, 24, 9, 0), False),  # Already ran Monday
        ("monday 08:00", datetime(2026, 8, 24, 7, 0), datetime(2026, 8, 17, 9, 0), False),  # Not Monday after 8am yet
        # weekdays
        ("weekdays", datetime(2026, 8, 24, 9, 0), datetime(2026, 8, 24, 0, 0), False),  # Monday, already ran
        ("weekdays", datetime(2026, 8, 24, 9, 0), datetime(2026, 8, 22, 9, 0), True),   # Previous was Saturday - now Mon, should trigger
        # weekends
        ("weekends", datetime(2026, 8, 22, 12, 0), datetime(2026, 8, 22, 0, 0), False),  # Saturday, already ran
        ("weekends", datetime(2026, 8, 24, 12, 0), datetime(2026, 8, 23, 12, 0), False),  # Monday, not weekend
    ])
    def test_should_trigger(self, schedule, now, last_run, expected):
        assert should_trigger(schedule, now, last_run) == expected

    @pytest.mark.parametrize("schedule,now,last_run,expected", [
        ("weekly", datetime(2026, 8, 22, 10, 0), datetime(2026, 8, 15, 10, 0), False),  # 7 days ago, not a full week
        ("weekly", datetime(2026, 8, 23, 10, 0), datetime(2026, 8, 15, 10, 0), True),      # Over a week
        ("1 week", datetime(2026, 8, 23, 10, 0), datetime(2026, 8, 15, 10, 0), True),       # Same as weekly
        ("2 weeks", datetime(2026, 8, 23, 10, 0), datetime(2026, 8, 15, 10, 0), False),     # Only 1 week
        ("2 weeks", datetime(2026, 8, 30, 10, 0), datetime(2026, 8, 15, 10, 0), True),      # 2+ weeks
    ])
    def test_should_trigger_weekly(self, schedule, now, last_run, expected):
        assert should_trigger(schedule, now, last_run) == expected

    @pytest.mark.parametrize("schedule,now,last_run,expected", [
        ("monday 08:00, wednesday 7:00, weekend 8:00", datetime(2026, 8, 24, 9, 0), None, True),  # Monday
        ("monday 08:00, wednesday 7:00, weekend 8:00", datetime(2026, 8, 24, 7, 0), None, False),  # Monday before 8am
        ("monday 08:00, wednesday 7:00, weekend 8:00", datetime(2026, 8, 26, 9, 0), None, True),  # Wednesday
        ("monday 08:00, wednesday 7:00, weekend 8:00", datetime(2026, 8, 22, 9, 0), None, True),  # Saturday (weekend)
    ])
    def test_should_trigger_multiple(self, schedule, now, last_run, expected):
        assert should_trigger(schedule, now, last_run) == expected


class TestWatchlistDB:
    """Tests for SQLite state database."""

    def test_db_creation(self, tmp_path):
        """DB file is created."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        assert os.path.exists(db_path)
        db.close()

    def test_set_and_get_last_run(self, tmp_path):
        """Set and retrieve last run timestamp."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        ts = datetime(2026, 8, 22, 10, 0)
        db.set_last_run(url, "ok", timestamp=ts)
        retrieved = db.get_last_run(url)
        assert retrieved is not None
        assert abs((retrieved - ts).total_seconds()) < 1
        assert db.get_last_status(url) == "ok"
        db.close()

    def test_get_last_run_none(self, tmp_path):
        """Returns None for unknown URL."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        assert db.get_last_run("https://unknown.com") is None
        db.close()

    def test_record_download_and_check_exists(self, tmp_path):
        """Record download and check existence."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        url = "https://example.com/ep1"
        filename = "Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        output_dir = str(tmp_path / "media")
        os.makedirs(output_dir)
        
        db.record_download(url, filename, output_dir)
        assert db.file_was_downloaded(url, filename, output_dir) is True
        assert db.file_was_downloaded(url, "other.mp4", output_dir) is False
        db.close()

    def test_db_watchlist_scan_record(self, tmp_path):
        """Record and check watchlist file scan time."""
        db_path = str(tmp_path / "state.db")
        db = WatchlistDB(db_path)
        path = str(tmp_path / "tv.txt")
        ts = datetime(2026, 8, 22, 10, 0)
        db.set_last_scan(path, ts)
        retrieved = db.get_last_scan(path)
        assert retrieved is not None
        assert abs((retrieved - ts).total_seconds()) < 1
        db.close()


class TestFileExistenceCheck:
    """Tests for scene filename-based file existence checking."""

    def test_file_exists_matching_filename(self, tmp_path):
        """File with matching scene filename exists → skip."""
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()
        filename = "Thuis.S31E6108.1080p.WEB-DL.AAC.x264.mp4"
        (output_dir / filename).write_text("dummy")
        
        result = check_file_exists(str(output_dir), filename)
        assert result is True

    def test_file_does_not_exist(self, tmp_path):
        """File not in directory → don't skip."""
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()
        result = check_file_exists(str(output_dir), "nonexistent.mp4")
        assert result is False

    def test_partial_download_handling(self, tmp_path):
        """Partial (.part) file exists, final file doesn't → proceed with download."""
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()
        filename = "Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        
        # Partial file exists
        (output_dir / (filename + ".part")).write_text("partial")
        
        # Final file doesn't exist → should proceed
        exists = check_file_exists(str(output_dir), filename)
        assert exists is False  # Not skipped

    def test_partial_removed_when_final_exists(self, tmp_path):
        """Partial file exists AND final file exists → partial should be cleaned."""
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()
        filename = "Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        
        (output_dir / filename).write_text("complete")
        (output_dir / (filename + ".part")).write_text("partial")
        
        # Final exists → should be detected as existing
        exists = check_file_exists(str(output_dir), filename)
        assert exists is True
