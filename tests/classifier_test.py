"""Tests for thuis.classifier — TV/movie/special content type classifier."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from thuis.classifier import ContentType, classify
from thuis.url_parser import parse_vrt_url


# ---------------------------------------------------------------------------
# Rule 2 — TV from URL structure (season > 0 AND episode > 0)
# ---------------------------------------------------------------------------

def test_standard_tv():
    """Standard TV episode URL with both season and episode → TV."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"
    )
    result = classify(info)
    assert result == ContentType.TV


def test_tv_no_metadata():
    """TV classified from URL structure alone, without yt-dlp metadata."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/5/thuis-s5a1000/"
    )
    result = classify(info, ytdlp_meta=None)
    assert result == ContentType.TV


# ---------------------------------------------------------------------------
# Rule 1 — SPECIAL from URL patterns
# ---------------------------------------------------------------------------

def test_special_url():
    """URL containing /extra-s/ in path → SPECIAL."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/extra-s/thuis-wat-vindt-judith/"
    )
    result = classify(info)
    assert result == ContentType.SPECIAL


def test_trailer_url():
    """URL containing /trailer/ in path → SPECIAL."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/ket-doc/trailer/ket-doc-trailer-s6/"
    )
    result = classify(info)
    assert result == ContentType.SPECIAL


# ---------------------------------------------------------------------------
# Rule 3 — TV from yt-dlp metadata (series field)
# ---------------------------------------------------------------------------

def test_tv_with_ytdlp_series():
    """No season/episode in URL, but yt-dlp metadata has series → TV."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/random-segment/"
    )
    # season=31, episode=0 — rule 2 does NOT match
    meta = {"series": "Thuis", "title": "Thuis S31 Deel 1"}
    result = classify(info, ytdlp_meta=meta)
    assert result == ContentType.TV


# ---------------------------------------------------------------------------
# Rule 4 — MOVIE from yt-dlp metadata (no episode, no season)
# ---------------------------------------------------------------------------

def test_movie_with_ytdlp():
    """No episode in metadata and no season from URL → MOVIE."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/de-zaak-mental/"
    )
    # season=0, episode=0, not a special/trailer
    meta = {"title": "De Zaak Mental", "episode": None, "season": None}
    result = classify(info, ytdlp_meta=meta)
    assert result == ContentType.MOVIE


# ---------------------------------------------------------------------------
# Rule 5 — UNKNOWN fallback
# ---------------------------------------------------------------------------

def test_unknown_fallback():
    """No season/episode in URL and no metadata → UNKNOWN."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/random-segment/"
    )
    # season=31, episode=0 — rule 2 does NOT match, no ytdlp_meta
    result = classify(info)
    assert result == ContentType.UNKNOWN


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_classify_requires_vrt_info():
    """classify() fails gracefully when given a non-VRT URL."""
    with pytest.raises(ValueError, match="Could not parse VRT URL"):
        parse_vrt_url("not-a-url")


def test_classify_none_meta():
    """classify() works when ytdlp_meta is explicitly None."""
    info = parse_vrt_url(
        "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"
    )
    result = classify(info, ytdlp_meta=None)
    assert result == ContentType.TV


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
