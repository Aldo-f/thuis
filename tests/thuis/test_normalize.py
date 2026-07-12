"""Unit tests for thuis.normalizer.run_normalize.

Tests cover dry-run mode, actual renaming, collision warnings,
cleanup of stale ``.part`` files, cleanup of ``_1`` duplicates,
and skipping of already-correct filenames.

All external calls (``resolve_show_title``, ``detect_codecs``) are
mocked so no real VRT API or ffprobe calls are made.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from thuis.codec_detector import detect_codecs
from thuis.normalizer import run_normalize
from thuis.show_resolver import resolve_show_title

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_resolve(title_map: dict[str, str]):
    """Return a ``resolve_show_title`` mock based on a slug→title dict.

    Slugs not in the map fall back to ``slug.title()``.
    """

    def mock_resolve(slug: str) -> str:
        return title_map.get(slug, slug.title())

    return mock_resolve


def _touch(path: Path, mtime: float | None = None):
    """Create an empty file at *path*, optionally setting its mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def _assert_exists(path: Path) -> None:
    """Assert a file exists (helper for clear assertions)."""
    assert path.exists(), f"Expected file to exist: {path}"


def _assert_not_exists(path: Path) -> None:
    """Assert a file does not exist."""
    assert not path.exists(), f"Expected file to NOT exist: {path}"


# ===================================================================
# Dry run
# ===================================================================


class TestDryRun:
    """With ``dry_run=True`` no files should be renamed or removed."""

    def test_dry_run_does_not_rename(self, tmp_path, monkeypatch):
        """Dry run: file keeps its original name after run_normalize."""
        src = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4"
        _touch(src)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=True)

        _assert_exists(src)
        # The canonical name should NOT exist
        canonical = tmp_path / "Fc.De.Kampioenen.S01E12.1080p.WEB-DL.AAC.x264.mp4"
        _assert_not_exists(canonical)

    def test_dry_run_cleanup_does_not_delete(self, tmp_path, monkeypatch):
        """Dry run + cleanup: stale .part file and duplicate kept."""
        normal = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4"
        dup = tmp_path / "fc.de.kampioenen.s01e12.1080p_1.mp4"
        part = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4.part"
        old_mtime = time.time() - 48 * 3600  # 48 hours ago
        _touch(normal)
        _touch(dup)
        _touch(part, mtime=old_mtime)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=True, cleanup=True)

        _assert_exists(normal)
        _assert_exists(dup)
        _assert_exists(part)


# ===================================================================
# Actual rename
# ===================================================================


class TestActualRename:
    """With ``dry_run=False`` files should be renamed correctly."""

    def test_basic_rename(self, tmp_path, monkeypatch):
        """A single file is renamed to canonical scene-style name."""
        src = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4"
        _touch(src)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        _assert_not_exists(src)
        canonical = tmp_path / "Fc.De.Kampioenen.S01E12.1080p.WEB-DL.AAC.x264.mp4"
        _assert_exists(canonical)

    def test_multiple_files_rename(self, tmp_path, monkeypatch):
        """Multiple files in the same dir are renamed."""
        files = [
            "fc.de.kampioenen.s01e12.1080p.mp4",
            "fc.de.kampioenen.s01e13.1080p.mp4",
        ]
        for name in files:
            _touch(tmp_path / name)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        for name in files:
            _assert_not_exists(tmp_path / name)
        _assert_exists(
            tmp_path / "Fc.De.Kampioenen.S01E12.1080p.WEB-DL.AAC.x264.mp4"
        )
        _assert_exists(
            tmp_path / "Fc.De.Kampioenen.S01E13.1080p.WEB-DL.AAC.x264.mp4"
        )

    def test_rename_no_resolution(self, tmp_path, monkeypatch):
        """File without resolution in name is renamed (no resolution tag)."""
        src = tmp_path / "show.s01e02.mp4"
        _touch(src)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"show": "Show"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        _assert_not_exists(src)
        canonical = tmp_path / "Show.S01E02.WEB-DL.AAC.x264.mp4"
        _assert_exists(canonical)


# ===================================================================
# Skip correctly-named files
# ===================================================================


class TestSkipAlreadyCanonical:
    """Files already in canonical format should be skipped."""

    def test_skip_correctly_named_file(self, tmp_path, monkeypatch):
        """A file that already has the canonical name stays untouched."""
        canonical_name = "Fc.De.Kampioenen.S01E12.1080p.WEB-DL.AAC.x264.mp4"
        f = tmp_path / canonical_name
        _touch(f)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        _assert_exists(f)


# ===================================================================
# Collision detection
# ===================================================================


class TestCollisionDetection:
    """When two files would map to the same new name, warn and skip."""

    def test_collision_warning(self, tmp_path, monkeypatch, capsys):
        """Two different files that would produce the same name → warning."""
        # Two files that differ but the mock resolve returns the same title
        _touch(tmp_path / "show1.s01e12.1080p.mp4")
        _touch(tmp_path / "show2.s01e12.1080p.mp4")

        # Both slugs resolve to the same title → same new filename
        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({
                "show1": "SameShow",
                "show2": "SameShow",
            }),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        captured = capsys.readouterr()
        assert "WAARSCHUWING" in captured.out

    def test_no_collision_diff_episode(self, tmp_path, monkeypatch):
        """Two files with different episodes → both renamed, no collision."""
        _touch(tmp_path / "show.s01e01.1080p.mp4")
        _touch(tmp_path / "show.s01e02.1080p.mp4")

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"show": "Show"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        _assert_exists(tmp_path / "Show.S01E01.1080p.WEB-DL.AAC.x264.mp4")
        _assert_exists(tmp_path / "Show.S01E02.1080p.WEB-DL.AAC.x264.mp4")


# ===================================================================
# Cleanup — stale .part files
# ===================================================================


class TestCleanupPartFiles:
    """Stale ``.part`` files (>24 h) should be removed; fresh ones kept."""

    def test_stale_part_removed(self, tmp_path, monkeypatch):
        """A ``.part`` file older than 24 h is removed when cleanup=True."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        part = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4.part"
        old_mtime = time.time() - 48 * 3600  # 48 hours ago
        _touch(part, mtime=old_mtime)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=True)

        _assert_not_exists(part)

    def test_fresh_part_kept(self, tmp_path, monkeypatch):
        """A recent ``.part`` file (<24 h) is kept when cleanup=True."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        part = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4.part"
        _touch(part)  # current time

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=True)

        _assert_exists(part)

    def test_cleanup_false_keeps_stale_part(self, tmp_path, monkeypatch):
        """Stale .part file is NOT removed when cleanup=False."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        part = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4.part"
        old_mtime = time.time() - 48 * 3600
        _touch(part, mtime=old_mtime)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=False)

        _assert_exists(part)


# ===================================================================
# Cleanup — _1 duplicates
# ===================================================================


class TestCleanupDuplicates:
    """``_1`` duplicate files should be removed when the original exists."""

    def test_duplicate_removed_when_original_processed(self, tmp_path, monkeypatch):
        """Normal file processed, duplicate identity in processed_ids → removed."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        dup = tmp_path / "fc.de.kampioenen.s01e12.1080p_1.mp4"
        _touch(dup)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=True)

        _assert_not_exists(dup)

    def test_duplicate_kept_when_original_missing(self, tmp_path, monkeypatch):
        """Only a _1 file exists (no original) → duplicate kept."""
        dup = tmp_path / "fc.de.kampioenen.s01e12.1080p_1.mp4"
        _touch(dup)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=True)

        _assert_exists(dup)

    def test_duplicate_not_removed_without_cleanup_flag(self, tmp_path, monkeypatch):
        """Even if original is processed, dup kept when cleanup=False."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        dup = tmp_path / "fc.de.kampioenen.s01e12.1080p_1.mp4"
        _touch(dup)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=False)

        _assert_exists(dup)


# ===================================================================
# No media files
# ===================================================================


class TestNoMediaFiles:
    """Directory with no matching files prints a message and returns."""

    def test_empty_directory(self, tmp_path, monkeypatch, capsys):
        """Empty dir → 'Geen media-bestanden gevonden' printed."""
        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        captured = capsys.readouterr()
        assert "Geen media-bestanden gevonden" in captured.out

    def test_non_media_files_ignored(self, tmp_path, monkeypatch, capsys):
        """Files that are not mp4/mp4.part/part are ignored."""
        _touch(tmp_path / "readme.txt")
        _touch(tmp_path / "data.bin")

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False)

        captured = capsys.readouterr()
        assert "Geen media-bestanden gevonden" in captured.out


# ===================================================================
# Report output
# ===================================================================


class TestReportOutput:
    """Check summary line contains correct counts."""

    def test_report_counts(self, tmp_path, monkeypatch, capsys):
        """Summary shows 1 hernoemd, 1 verwijderd, 1 opgeruimd."""
        _touch(tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4")
        dup = tmp_path / "fc.de.kampioenen.s01e12.1080p_1.mp4"
        _touch(dup)
        part = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4.part"
        _touch(part, mtime=time.time() - 48 * 3600)

        monkeypatch.setattr(
            "thuis.normalizer.resolve_show_title",
            _make_mock_resolve({"fc.de.kampioenen": "Fc.De.Kampioenen"}),
        )
        monkeypatch.setattr(
            "thuis.normalizer.detect_codecs",
            lambda p: ("mp4a", "avc1"),
        )

        run_normalize(tmp_path, dry_run=False, cleanup=True)

        captured = capsys.readouterr()
        assert "1 bestanden hernoemd" in captured.out
        assert "1 duplicates verwijderd" in captured.out
        assert "1 part files opgeruimd" in captured.out
