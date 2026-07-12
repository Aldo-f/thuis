"""Tests for thuis.scene_namer — scene-compliant filename builder."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from thuis.scene_namer import (
    CODEC_MAP,
    lookup_codec,
    normalize_show_name,
    build_tv_filename,
    build_movie_filename,
    build_special_filename,
)


# ---------------------------------------------------------------------------
# lookup_codec
# ---------------------------------------------------------------------------

class TestLookupCodec:
    def test_all_codec_map_entries(self):
        """Every key in CODEC_MAP maps to its expected label."""
        for key, expected_label in CODEC_MAP.items():
            assert lookup_codec(key) == expected_label

    def test_prefix_matching(self):
        """Prefix matching works — extra suffix after codec key is ignored."""
        assert lookup_codec("avc1.64002A") == "x264"
        assert lookup_codec("mp4a.40.2") == "AAC"
        assert lookup_codec("hev1.1.6.L150") == "x265"
        assert lookup_codec("hvc1.1.6.L150") == "x265"

    def test_no_match_returns_original(self):
        """Unmapped codec string is returned unchanged."""
        assert lookup_codec("v_vp9") == "v_vp9"
        assert lookup_codec("theora") == "theora"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert lookup_codec("") == ""


# ---------------------------------------------------------------------------
# normalize_show_name
# ---------------------------------------------------------------------------

class TestNormalizeShowName:
    def test_spaces_become_dots(self):
        """Spaces are replaced with dots."""
        assert normalize_show_name("The Wire") == "The.Wire"

    def test_ampersand_becomes_and(self):
        """& is replaced with And."""
        assert normalize_show_name("Law & Order") == "Law.And.Order"

    def test_special_chars_removed(self):
        """Non-alphanumeric, non-dot characters are stripped."""
        assert normalize_show_name("Doctor Who? (2005)") == "Doctor.Who.2005"

    def test_collapses_multiple_dots(self):
        """Multiple consecutive dots are collapsed into one."""
        assert normalize_show_name("Foo...Bar") == "Foo.Bar"

    def test_strips_leading_trailing_dots(self):
        """Leading and trailing dots are removed."""
        assert normalize_show_name(".Foo.Bar.") == "Foo.Bar"

    def test_preserves_case(self):
        """Case is preserved, not lowercased."""
        assert normalize_show_name("The Expanse") == "The.Expanse"


# ---------------------------------------------------------------------------
# build_tv_filename
# ---------------------------------------------------------------------------

class TestBuildTvFilename:
    def test_standard(self):
        """Standard TV episode with all tags."""
        result = build_tv_filename(
            "Thuis", 31, 6108, "1080", "mp4a", "avc1"
        )
        assert result == "Thuis.S31E6108.1080p.WEB-DL.AAC.x264.mp4"

    def test_high_episode_no_zeropad(self):
        """Episode > 99 uses variable width (no zero-padding)."""
        result = build_tv_filename(
            "Thuis", 1, 6108, "1080", "mp4a", "avc1"
        )
        assert result == "Thuis.S01E6108.1080p.WEB-DL.AAC.x264.mp4"

    def test_two_digit_episode(self):
        """Episode 01-99 uses zero-padded 2-digit format."""
        result = build_tv_filename(
            "Thuis", 1, 12, "720", "mp4a", "avc1"
        )
        assert result == "Thuis.S01E12.720p.WEB-DL.AAC.x264.mp4"

    def test_episode_zero(self):
        """Episode 0 becomes E00."""
        result = build_tv_filename(
            "Thuis", 1, 0, "1080", "mp4a", "avc1"
        )
        assert result == "Thuis.S01E00.1080p.WEB-DL.AAC.x264.mp4"

    def test_no_codecs(self):
        """None codec tags are skipped entirely."""
        result = build_tv_filename("Thuis", 1, 1)
        assert result == "Thuis.S01E01.WEB-DL.mp4"

    def test_some_codecs(self):
        """Partial codec tags produce correct partial output."""
        result = build_tv_filename(
            "Thuis", 2, 3, resolution="1080", audio_codec="mp4a"
        )
        assert result == "Thuis.S02E03.1080p.WEB-DL.AAC.mp4"

    def test_long_show_name_gets_normalized(self):
        """Show name goes through normalize_show_name."""
        result = build_tv_filename(
            "Law & Order: Special Victims Unit", 1, 1, "720"
        )
        assert result == "Law.And.Order.Special.Victims.Unit.S01E01.720p.WEB-DL.mp4"


# ---------------------------------------------------------------------------
# build_movie_filename
# ---------------------------------------------------------------------------

class TestBuildMovieFilename:
    def test_standard_movie(self):
        """Movie filename with all tags including year."""
        result = build_movie_filename("The Matrix", 1999, "1080", "mp4a", "avc1")
        assert result == "The.Matrix.1999.1080p.WEB-DL.AAC.x264.mp4"

    def test_movie_without_year(self):
        """Movie filename omits year tag when year is None."""
        result = build_movie_filename("The Matrix", None, "1080")
        assert result == "The.Matrix.1080p.WEB-DL.mp4"

    def test_movie_with_year_zero(self):
        """Movie filename omits year tag when year is 0."""
        result = build_movie_filename("Unknown", 0, "1080")
        assert result == "Unknown.1080p.WEB-DL.mp4"

    def test_movie_no_tags(self):
        """Movie filename with no optional tags at all."""
        result = build_movie_filename("Alien")
        assert result == "Alien.WEB-DL.mp4"


# ---------------------------------------------------------------------------
# build_special_filename
# ---------------------------------------------------------------------------

class TestBuildSpecialFilename:
    def test_standard_special(self):
        """Special filename with all tags."""
        result = build_special_filename("Thuis", "1080", "mp4a", "avc1")
        assert result == "Thuis.Special.1080p.WEB-DL.AAC.x264.mp4"

    def test_special_no_tags(self):
        """Special filename without any optional tags."""
        result = build_special_filename("Thuis")
        assert result == "Thuis.Special.WEB-DL.mp4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
