"""Tests for thuis.metadata_fetcher — yt-dlp metadata wrapper."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from unittest.mock import patch, MagicMock

from thuis.metadata_fetcher import (
    CODEC_MAP,
    lookup_codec,
    parse_resolution,
    fetch_metadata,
)


# ---------------------------------------------------------------------------
# lookup_codec
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("avc1.64002A", "x264"),
        ("hev1.1.6.L150.90", "x265"),
        ("hvc1.1.6.L150.90", "x265"),
        ("vp09.00.10.08", "VP9"),
        ("av01.0.05M.08", "AV1"),
        ("mp4a.40.2", "AAC"),
        ("ac-3", "AC3"),
        ("ec-3", "EAC3"),
        ("opus", "Opus"),
        ("dts", "DTS"),
    ],
)
def test_lookup_codec_all(raw: str, expected: str) -> None:
    """All ten codecs in CODEC_MAP are correctly resolved."""
    assert lookup_codec(raw) == expected


def test_lookup_codec_unknown() -> None:
    """Unmapped codec string is returned unchanged."""
    assert lookup_codec("unknown.codec") == "unknown.codec"


def test_lookup_codec_empty() -> None:
    """Empty string returns empty string (no crash)."""
    assert lookup_codec("") == ""


# ---------------------------------------------------------------------------
# parse_resolution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1080", "1080p"),
        ("720", "720p"),
        ("480", "480p"),
        ("2160", "2160p"),
    ],
)
def test_parse_resolution_valid(raw: str, expected: str) -> None:
    """Numeric height string gets a ``p`` suffix."""
    assert parse_resolution(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [None, "", "NA"],
)
def test_parse_resolution_none(raw: str | None) -> None:
    """None / empty / ``'NA'`` all map to None."""
    assert parse_resolution(raw) is None


# ---------------------------------------------------------------------------
# fetch_metadata — mocked subprocess
# ---------------------------------------------------------------------------

_REAL_OUTPUT = (
    "Thuis|NA|6108|1080|avc1.64002A|mp4a.40.2|mp4|De politie krijgt een kans"
)


def _mock_run_ok(**kwargs):
    """Return a MagicMock that looks like a successful subprocess result."""
    out = kwargs.pop("stdout", _REAL_OUTPUT)
    m = MagicMock()
    m.returncode = 0
    m.stdout = out
    m.stderr = ""
    return m


def test_fetch_metadata_parses_correctly() -> None:
    """Successful yt-dlp output is parsed and codecs are mapped."""
    with patch("thuis.metadata_fetcher.subprocess.run", return_value=_mock_run_ok()):
        meta = fetch_metadata("https://example.com/video")

    assert meta["series"] == "Thuis"
    assert meta["season"] is None  # NA
    assert meta["episode"] == "6108"
    assert meta["height"] == "1080p"
    assert meta["vcodec_raw"] == "avc1.64002A"
    assert meta["vcodec_label"] == "x264"
    assert meta["acodec_raw"] == "mp4a.40.2"
    assert meta["acodec_label"] == "AAC"
    assert meta["ext"] == "mp4"
    assert meta["title"] == "De politie krijgt een kans"


def test_fetch_metadata_all_na() -> None:
    """When every field is NA they are all returned as None."""
    all_na = "NA|NA|NA|NA|NA|NA|NA|NA"
    with patch(
        "thuis.metadata_fetcher.subprocess.run",
        return_value=_mock_run_ok(stdout=all_na),
    ):
        meta = fetch_metadata("https://example.com/video")

    assert meta["series"] is None
    assert meta["season"] is None
    assert meta["episode"] is None
    assert meta["height"] is None
    assert meta["vcodec_label"] == "NA"  # not in CODEC_MAP → fallback
    assert meta["acodec_label"] == "NA"
    assert meta["title"] is None


def test_fetch_metadata_subprocess_failure() -> None:
    """A subprocess that fails (non-zero exit) returns an empty dict."""
    fail = MagicMock()
    fail.returncode = 1
    fail.stdout = ""
    fail.stderr = "error"

    with patch("thuis.metadata_fetcher.subprocess.run", return_value=fail):
        meta = fetch_metadata("https://example.com/video")

    assert meta == {}


def test_fetch_metadata_subprocess_exception() -> None:
    """A subprocess that raises an exception returns an empty dict."""
    with patch(
        "thuis.metadata_fetcher.subprocess.run",
        side_effect=RuntimeError("boom"),
    ):
        meta = fetch_metadata("https://example.com/video")

    assert meta == {}


def test_fetch_metadata_empty_output() -> None:
    """Empty stdout (empty string) returns an empty dict."""
    empty = MagicMock()
    empty.returncode = 0
    empty.stdout = ""
    empty.stderr = ""

    with patch("thuis.metadata_fetcher.subprocess.run", return_value=empty):
        meta = fetch_metadata("https://example.com/video")

    assert meta == {}


def test_fetch_metadata_credentials_passed() -> None:
    """When credentials are provided they are included in the command."""
    with patch("thuis.metadata_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = _mock_run_ok()
        fetch_metadata(
            "https://example.com/video",
            credentials=("user@example.com", "s3cret"),
        )

    args, _ = mock_run.call_args
    # args[0] is the command list
    cmd = args[0]
    assert "--username" in cmd
    assert "user@example.com" in cmd
    assert "--password" in cmd
    assert "s3cret" in cmd


# ---------------------------------------------------------------------------
# CODEC_MAP itself — simple sanity
# ---------------------------------------------------------------------------

def test_codec_map_entries() -> None:
    """CODEC_MAP contains the expected 10 entries."""
    assert len(CODEC_MAP) == 10
    assert CODEC_MAP["avc1"] == "x264"
    assert CODEC_MAP["mp4a"] == "AAC"
    assert CODEC_MAP["opus"] == "Opus"


# ---------------------------------------------------------------------------
# fetch_preview_height
# ---------------------------------------------------------------------------


def test_fetch_preview_height_returns_int() -> None:
    """fetch_preview_height returns the parsed height as int."""
    from thuis.metadata_fetcher import fetch_preview_height

    with patch("thuis.metadata_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="1080\n", stderr="")

        result = fetch_preview_height("https://example.com/video")

        assert result == 1080
        mock_run.assert_called_once()


def test_fetch_preview_height_na_returns_none() -> None:
    """When yt-dlp returns 'NA' for height, returns None."""
    from thuis.metadata_fetcher import fetch_preview_height

    with patch("thuis.metadata_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="NA\n", stderr="")

        result = fetch_preview_height("https://example.com/video")

        assert result is None


def test_fetch_preview_height_failure_returns_none() -> None:
    """When subprocess fails, returns None."""
    from thuis.metadata_fetcher import fetch_preview_height

    with patch("thuis.metadata_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        result = fetch_preview_height("https://example.com/video")

        assert result is None


def test_fetch_preview_height_passes_credentials() -> None:
    """When credentials provided, --username and --password are passed."""
    from thuis.metadata_fetcher import fetch_preview_height

    with patch("thuis.metadata_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="720\n", stderr="")

        result = fetch_preview_height(
            "https://example.com/video",
            credentials=("user@test.com", "secret"),
        )

        assert result == 720
        args_list = mock_run.call_args[0][0]
        assert "--username" in args_list
        assert "user@test.com" in args_list
        assert "--password" in args_list
        assert "secret" in args_list


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
