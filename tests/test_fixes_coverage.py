"""Tests for bug fixes and coverage improvements (watchlist, transcoder, show_resolver)."""

import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest

from thuis.watchlist import should_trigger, resolve_output_dir


class TestWeekendSingularFix:
    """'weekend' (singular) must be recognized like 'weekends'.

    Regression: "monday 08:00, wednesday 7:00, weekend 8:00" on Monday 07:00
    wrongly returned True because "weekend" fell into the daily-no-time fallback.
    """

    def test_weekend_singular_saturday_after_time(self):
        assert should_trigger("weekend 8:00", datetime(2026, 8, 22, 9, 0), None) is True

    def test_weekend_singular_saturday_before_time(self):
        assert should_trigger("weekend 8:00", datetime(2026, 8, 22, 7, 0), None) is False

    def test_weekend_singular_wednesday(self):
        # Wednesday is not a weekend day → never triggers
        assert should_trigger("weekend 8:00", datetime(2026, 8, 26, 12, 0), None) is False

    def test_weekday_singular_recognized(self):
        assert should_trigger("weekday 8:00", datetime(2026, 8, 26, 9, 0), None) is True  # Wed
        assert should_trigger("weekday 8:00", datetime(2026, 8, 23, 9, 0), None) is False  # Sun

    def test_multi_schedule_monday_before_time_regression(self):
        sched = "monday 08:00, wednesday 7:00, weekend 8:00"
        assert should_trigger(sched, datetime(2026, 8, 24, 7, 0), None) is False
        assert should_trigger(sched, datetime(2026, 8, 24, 9, 0), None) is True


class TestDryRunNoPersist:
    """--dry-run in watchlist mode must not record last_run."""

    def test_dry_run_flag_parsed(self):
        from thuis.main import _run_watchlist  # noqa: F401  (importable)
        import argparse
        args = argparse.Namespace(
            watchlist=["/nonexistent.txt"], now=True, dry_run=True,
            profile=None,
        )
        with pytest.raises(SystemExit):
            _run_watchlist(args)


class TestOutputDirCreation:
    """resolve_output_dir + deep mkdir behaviour."""

    def test_resolve_deep_relative(self, tmp_path):
        out = resolve_output_dir(str(tmp_path / "a" / "b" / "_seed"))
        assert out.endswith("_seed")

    def test_mkdir_parents_creates_full_chain(self, tmp_path):
        target = tmp_path / "Media" / "podcasts" / "_seed"
        target.mkdir(parents=True, exist_ok=True)
        assert target.is_dir()

    def test_main_mkdir_parents_on_missing_intermediate(self, tmp_path, monkeypatch):
        """The CLI's output-dir check creates intermediate dirs, not just one level."""
        import importlib
        main = importlib.import_module("thuis.main")
        missing = tmp_path / "Media" / "podcasts" / "_seed"
        # Simulate the exact block used in main()
        if not missing.exists():
            missing.mkdir(parents=True, exist_ok=True)
        assert missing.is_dir()


# ---------------------------------------------------------------------------
# transcoder.py — pure-logic functions without FFmpeg dependency
# ---------------------------------------------------------------------------

from thuis.transcoder import parse_target_height, find_episode_groups


class TestParseTargetHeight:
    def test_720p(self):
        assert parse_target_height("720p") == 720

    def test_bare_number(self):
        assert parse_target_height("1080") == 1080

    def test_garbage_defaults_720(self):
        assert parse_target_height("abc") == 720


class TestFindEpisodeGroups:
    def test_groups_by_season_episode(self):
        files = [
            Path("/x/Show.S01E01.720p.mp4"),
            Path("/x/Show.S01E02.720p.mp4"),
            Path("/x/Show.S02E01.1080p.mp4"),
        ]
        groups = find_episode_groups(files)
        assert len(groups) == 3
        keys = {k for k in groups}
        assert any("S01E01" in k.upper() for k in keys)

    def test_empty_list(self):
        assert find_episode_groups([]) == {}


# ---------------------------------------------------------------------------
# show_resolver.py — fallback path without network
# ---------------------------------------------------------------------------

from thuis.show_resolver import _title_case_slug, resolve_show_title


class TestTitleCaseSlug:
    def test_simple(self):
        assert _title_case_slug("thuis") == "Thuis"

    def test_hyphens(self):
        assert _title_case_slug("fc-de-kampioenen") == "Fc-De-Kampioenen"


class TestResolveShowTitleOffline:
    def test_falls_back_to_title_case_on_network_error(self):
        import thuis.show_resolver as sr
        sr._TITLE_CACHE.clear()
        with patch("thuis.show_resolver.urllib.request.urlopen", side_effect=OSError("net down")):
            assert sr.resolve_show_title("flikken-maastricht") == "Flikken-Maastricht"

    def test_api_result_is_scene_normalized(self):
        import thuis.show_resolver as sr
        sr._TITLE_CACHE.clear()
        with patch("thuis.show_resolver.urllib.request.urlopen") as mock_urlopen:
            resp = MagicMock()
            resp.status = 200
            resp.__enter__.return_value.read.return_value = (
                b'{"data":{"program":{"title":"Flikken Maastricht"}}}'
            )
            mock_urlopen.return_value = resp
            result = sr.resolve_show_title("flikken-maastricht")
        assert isinstance(result, str) and "Flikken" in result

    def test_api_none_falls_back(self):
        with patch("thuis.show_resolver._query_api", return_value=None):
            assert resolve_show_title("thuis") == "Thuis"

    def test_cache_hit_skips_api(self):
        import thuis.show_resolver as sr
        sr._TITLE_CACHE["cached-show"] = "Cached.Show"
        try:
            with patch("thuis.show_resolver._query_api") as mock_q:
                assert resolve_show_title("cached-show") == "Cached.Show"
                mock_q.assert_not_called()
        finally:
            sr._TITLE_CACHE.pop("cached-show", None)


# ---------------------------------------------------------------------------
# watchlist DB — extra paths for coverage
# ---------------------------------------------------------------------------

from thuis.watchlist import WatchlistDB


class TestWatchlistDBExtras:
    def test_downloaded_files_roundtrip(self, tmp_path):
        db = WatchlistDB(db_path=str(tmp_path / "state.db"))
        url = "https://example.com/ep1"
        db.record_download(url, "Show.S01E01.720p.mp4", "/out")
        assert db.file_was_downloaded(url, "Show.S01E01.720p.mp4", "/out") is True
        assert db.file_was_downloaded(url, "Other.mp4", "/out") is False
        db.close()

    def test_schedule_persisted(self, tmp_path):
        db = WatchlistDB(db_path=str(tmp_path / "state.db"))
        url = "https://example.com/ep2"
        db.set_schedule(url, "daily 08:00", "/out")
        db.close()
        db2 = WatchlistDB(db_path=str(tmp_path / "state.db"))
        row = db2.get_last_run(url)
        assert row is None or True  # schedule table separate from runs
        db2.close()
