"""Tests for thuis.url_parser — VRT MAX URL parser."""

import sys
import os

# Add the repository src directory to sys.path so we can import thuis.url_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from thuis.url_parser import parse_vrt_url, VrtUrlInfo


def test_parse_standard_tv():
    """Standard TV episode URL extracts season + episode correctly."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"
    )
    assert result.show_slug == "thuis"
    assert result.season == 31
    assert result.episode == 6108
    assert result.path == "/vrtmax/a-z/thuis/31/thuis-s31a6108"
    assert result.url == "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"


def test_parse_special():
    """URL with /extra-s/ in path returns season=0, episode=0."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/extra-s/thuis-wat-vindt-judith/"
    )
    assert result.show_slug == "thuis"
    assert result.season == 0
    assert result.episode == 0


def test_parse_trailer():
    """URL with /trailer/ in path returns season=0, episode=0."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/"
    )
    assert result.show_slug == "ket-doc"
    assert result.season == 0
    assert result.episode == 0


def test_normalize_slug():
    """Triple hyphens in slug are normalized to single hyphen."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/"
    )
    assert result.show_slug == "ket-doc"


def test_invalid_url():
    """Garbage input raises ValueError."""
    with pytest.raises(ValueError, match="Could not parse VRT URL"):
        parse_vrt_url("not-a-url")


def test_no_season_episode_pattern():
    """URL without s(\\d+)a(\\d+) in last segment returns episode=0."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/random-segment/"
    )
    assert result.show_slug == "thuis"
    assert result.season == 31
    assert result.episode == 0


def test_double_slash_normalization():
    """Double slashes in path are collapsed."""
    result = parse_vrt_url(
        "https://www.vrt.be//vrtmax//a-z//thuis//31//thuis-s31a6108/"
    )
    assert result.show_slug == "thuis"
    assert result.season == 31
    assert result.episode == 6108


def test_url_does_not_require_trailing_slash():
    """URL without trailing slash still parses correctly."""
    result = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108"
    )
    assert result.show_slug == "thuis"
    assert result.season == 31
    assert result.episode == 6108


def test_vrt_info_dataclass_fields():
    """VrtUrlInfo dataclass has the expected fields."""
    info = VrtUrlInfo(
        show_slug="test", season=1, episode=2, path="/test/", url="https://example.com/"
    )
    assert info.show_slug == "test"
    assert info.season == 1
    assert info.episode == 2
    assert info.path == "/test/"
    assert info.url == "https://example.com/"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
