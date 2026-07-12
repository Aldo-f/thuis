"""Unit tests for thuis.filename_parser.parse_filename.

Tests cover scene-style naming, duplicate markers (``_1``), partial
download markers (``.part``), specials, date-based episodes, fallback
parsing, and rejection of non-media filenames.
"""

from pathlib import Path

import pytest
from thuis.filename_parser import parse_filename


# ===================================================================
# Scene-style primary regex matches
# ===================================================================


class TestStandardParsing:
    """Primary regex ``_RE_STANDARD`` — scene-style ``sXXeYY``."""

    def test_basic(self):
        """fc.de.kampioenen.s01e12.1080p.mp4 → correct fields."""
        p = parse_filename(Path("fc.de.kampioenen.s01e12.1080p.mp4"))
        assert p is not None
        assert p.show_slug == "fc.de.kampioenen"
        assert p.season == 1
        assert p.episode == 12
        assert p.resolution == "1080"
        assert not p.is_duplicate
        assert not p.is_part

    def test_uppercase_scene_style(self):
        """Show.Name.S21E12.1080p.WEB-DL.AAC.x264.mp4 → lowercased slug."""
        p = parse_filename(Path("Show.Name.S21E12.1080p.WEB-DL.AAC.x264.mp4"))
        assert p is not None
        assert p.show_slug == "show.name"
        assert p.season == 21
        assert p.episode == 12
        assert p.resolution == "1080"

    def test_special_no_episode(self):
        """Show.Name.Special.1080p.mp4 → episode=0, no season."""
        p = parse_filename(Path("Show.Name.Special.1080p.mp4"))
        assert p is not None
        assert p.show_slug == "show.name"
        assert p.season == 0
        assert p.episode == 0
        assert p.resolution == "1080"

    def test_date_based(self):
        """Show.Name.D20260706.1080p.mp4 → episode=0 (date-based)."""
        p = parse_filename(Path("Show.Name.D20260706.1080p.mp4"))
        assert p is not None
        assert p.show_slug == "show.name"
        assert p.season == 0
        assert p.episode == 0
        assert p.resolution == "1080"

    def test_no_resolution(self):
        """show.name.s01e02.mp4 → resolution is None."""
        p = parse_filename(Path("show.name.s01e02.mp4"))
        assert p is not None
        assert p.show_slug == "show.name"
        assert p.season == 1
        assert p.episode == 2
        assert p.resolution is None

    def test_lowercase_season_episode(self):
        """Lowercase sXXeYY is also matched."""
        p = parse_filename(Path("series.name.s03e04.720p.mp4"))
        assert p is not None
        assert p.show_slug == "series.name"
        assert p.season == 3
        assert p.episode == 4
        assert p.resolution == "720"


# ===================================================================
# Suffix markers: _1 duplicate and .part
# ===================================================================


class TestSuffixMarkers:
    """Trailing ``_1`` (duplicate) and ``.part`` (partial) markers."""

    def test_duplicate_marker(self):
        """File ending in ``_1`` before extension → is_duplicate=True."""
        p = parse_filename(Path("fc.de.kampioenen.s01e12.1080p_1.mp4"))
        assert p is not None
        assert p.show_slug == "fc.de.kampioenen"
        assert p.season == 1
        assert p.episode == 12
        assert p.resolution == "1080"
        assert p.is_duplicate is True

    def test_part_suffix(self):
        """File ending in ``.part`` → is_part=True."""
        p = parse_filename(Path("fc.de.kampioenen.s01e12.1080p.mp4.part"))
        assert p is not None
        assert p.show_slug == "fc.de.kampioenen"
        assert p.season == 1
        assert p.episode == 12
        assert p.resolution == "1080"
        assert p.is_part is True

    def test_both_duplicate_and_part(self):
        """Both ``_1`` and ``.part`` markers are detected together."""
        p = parse_filename(Path("show.s01e01_1.mp4.part"))
        assert p is not None
        assert p.is_duplicate is True
        assert p.is_part is True
        assert p.show_slug == "show"
        assert p.season == 1
        assert p.episode == 1

    def test_part_no_dot_extension_loses_season_episode(self):
        """A bare ``.part`` file without a preceding extension — after
        stripping ``.part``, the season/episode segment becomes the file
        extension and is lost from parseable content."""
        p = parse_filename(Path("show.s01e01.part"))
        assert p is not None
        # After stripping .part → "show.s01e01", the last dot is before
        # "s01e01", so stem="show" and "s01e01" is treated as extension.
        # The stem alone has no season/episode → show_slug="" (fallback
        # returns with show_slug empty for unparseable .part files).
        assert p.show_slug == ""
        assert p.season == 0
        assert p.episode == 0
        assert p.resolution is None
        assert p.is_part is True

    def test_only_part_no_stem(self):
        """A file named exactly ``.part`` with no stem → returns part-entry."""
        p = parse_filename(Path(".part"))
        assert p is not None
        assert p.show_slug == ""
        assert p.is_part is True

    def test_duplicate_on_fallback(self):
        """Fallback path also recognises ``_1`` marker."""
        p = parse_filename(Path("s01e02_1.mp4"))
        assert p is not None
        assert p.show_slug == ""
        assert p.is_duplicate is True


# ===================================================================
# Fallback parsing (dot-split sXXeYY)
# ===================================================================


class TestFallbackParsing:
    """Fallback ``_RE_FALLBACK`` — no dot between show and sXXeYY."""

    def test_bare_season_episode_no_show(self):
        """``s01e02.mp4`` → only season & episode, no show_slug."""
        p = parse_filename(Path("s01e02.mp4"))
        assert p is not None
        assert p.show_slug == ""
        assert p.season == 1
        assert p.episode == 2

    def test_fallback_with_resolution_after(self):
        """``series.name.s01e02.1080p.mp4`` → this actually hits primary,
        but verify it works. Use a case where primary fails, e.g.
        a show segment containing a character not in ``[\\w.]``."""
        p = parse_filename(Path("name.with-hyphen.s01e02.1080p.mp4"))
        # The primary regex will match up to "name.with" (dots are in [\w.]),
        # then "hyphen" won't be consumed. So show="name.with", then
        # no season/episode after the dot before "hyphen".
        # Actually [\w.]+? is lazy, so "name" is show, then dot, then
        # "with-hyphen" doesn't match sXXeYY... Hmm, let me check.
        # "name.with-hyphen.s01e02.1080p.mp4"
        # show = "name.with" ([\w.]+?), then dot, "hyphen" doesn't start
        # with s/S. So backtrack, show = "name", then dot, "with" doesn't
        # start with s/S. Continue: show = "name.with-hyphen", then dot,
        # s01e02 matches. Wait, hyphens are not in [\w.] so show = "name.with"
        # and the remaining is "-hyphen.s01e02.1080p". The regex expects
        # \.(?:[sS]...) but gets "-". So primary fails.
        # Fallback: parts = ["name", "with-hyphen", "s01e02", "1080p"]
        # The "s01e02" part matches _RE_FALLBACK.
        # show_slug = "name.with-hyphen", season=1, episode=2
        # resolution = "1080" (from index 3 after s01e02)
        assert p is not None
        assert p.show_slug == "name.with-hyphen"
        assert p.season == 1
        assert p.episode == 2
        assert p.resolution == "1080"

    def test_fallback_with_dotted_show(self):
        """``dotted.show.name.s01e02.mp4`` via primary, but also
        exercises the path."""
        p = parse_filename(Path("dotted.show.name.s01e02.mp4"))
        assert p is not None
        assert p.show_slug == "dotted.show.name"
        assert p.season == 1
        assert p.episode == 2

    def test_fallback_resolution_before_marker(self):
        """When resolution appears before sXXeYY and the primary regex
        cannot match (due to characters outside ``[\\w.]`` in the show
        slug), the fallback finds the resolution via its before-marker
        search."""
        p = parse_filename(Path("1080p.show-name.s01e02.mp4"))
        assert p is not None
        # The primary regex fails because `-` is not in [\w.],
        # so the fallback splits on dots and finds "1080p" as resolution.
        assert p.resolution == "1080"
        assert p.show_slug == "1080p.show-name"
        assert p.season == 1
        assert p.episode == 2

    def test_fallback_resolution_after_marker(self):
        """When resolution part appears after sXXeYY, it is found."""
        p = parse_filename(Path("show.s01e02.1080p.mp4"))
        assert p is not None
        assert p.resolution == "1080"


# ===================================================================
# Non-media / unrecognisable
# ===================================================================


class TestNonMedia:
    """Filenames that should return ``None``."""

    def test_readme_txt(self):
        """``readme.txt`` is not a media file → None."""
        assert parse_filename(Path("readme.txt")) is None

    def test_no_extension_no_pattern(self):
        """File with no extension and no recognisable pattern → None."""
        assert parse_filename(Path("randomfile")) is None

    def test_hidden_file(self):
        """Dotfile with no pattern → None."""
        assert parse_filename(Path(".hidden")) is None

    def test_empty_name(self):
        """Empty filename → None."""
        assert parse_filename(Path("")) is None


# ===================================================================
# original_path is preserved
# ===================================================================


class TestOriginalPath:
    """ParsedFilename.original_path must match the input Path."""

    def test_original_path_matches(self):
        """The original Path is stored unchanged."""
        path = Path("/some/dir/Show.Name.S01E02.mp4")
        p = parse_filename(path)
        assert p is not None
        assert p.original_path == path


# ===================================================================
# Temp file integration
# ===================================================================


class TestWithTempFiles:
    """Verify parse_filename works on real files via tmp_path."""

    def test_real_file_on_disk(self, tmp_path):
        """Create an actual file, pass its Path to parse_filename."""
        f = tmp_path / "fc.de.kampioenen.s01e12.1080p.mp4"
        f.write_text("dummy content")
        p = parse_filename(f)
        assert p is not None
        assert p.show_slug == "fc.de.kampioenen"
        assert p.season == 1
        assert p.episode == 12
        assert p.resolution == "1080"
        assert p.original_path == f

    def test_real_part_file(self, tmp_path):
        """Create an actual .part file and verify parsing."""
        f = tmp_path / "show.s01e02.mp4.part"
        f.write_text("dummy")
        p = parse_filename(f)
        assert p is not None
        assert p.show_slug == "show"
        assert p.is_part is True

    def test_non_media_in_directory(self, tmp_path):
        """Non-media files in a dir return None from parse_filename."""
        f = tmp_path / "readme.txt"
        f.write_text("hello")
        p = parse_filename(f)
        assert p is None
