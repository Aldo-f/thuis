"""Tests for TMDBClient metadata enrichment plugin."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from unittest.mock import patch, MagicMock

from thuis.plugins.metadata_enricher import TMDBClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client() -> TMDBClient:
    """Create a client whose _get_json is fully mocked to return None."""
    client = TMDBClient(api_key="test-key")
    client._get_json = MagicMock(return_value=None)  # type: ignore[method-assign]
    return client


# ---------------------------------------------------------------------------
# _parse_year (static helper)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("date_str", "expected"),
    [
        ("2012-01-01", 2012),
        ("1999-12-31", 1999),
        (None, None),
        ("", None),
        ("not-a-date", None),
        ("201", 201),
    ],
)
def test_parse_year(date_str: str | None, expected: int | None) -> None:
    """_parse_year extracts a 4-digit year or returns None."""
    assert TMDBClient._parse_year(date_str) == expected


# ---------------------------------------------------------------------------
# lookup_show — baseline: network error
# ---------------------------------------------------------------------------

def test_lookup_show_network_error() -> None:
    """lookup_show returns None when any internal call raises."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=Exception("boom")):
        result = client.lookup_show("Thuis")
    assert result is None


# ---------------------------------------------------------------------------
# lookup_show — happy path (no episode)
# ---------------------------------------------------------------------------

def test_lookup_show_success() -> None:
    """A successful show lookup returns the expected metadata dict."""
    search_resp = {"results": [{"id": 123, "name": "Thuis"}]}
    tv_resp = {
        "name": "Thuis",
        "first_air_date": "2012-01-01",
        "overview": "A Belgian soap opera.",
        "poster_path": "/abc123.jpg",
        "seasons": [{"season_number": 1}, {"season_number": 2}],
    }

    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, tv_resp]):
        result = client.lookup_show("Thuis")

    assert result is not None
    assert result["title"] == "Thuis"
    assert result["year"] == 2012
    assert result["overview"] == "A Belgian soap opera."
    assert result["poster_path"] == "/abc123.jpg"
    assert result["seasons"] == 2
    assert "episodes" not in result


# ---------------------------------------------------------------------------
# lookup_show — with episode
# ---------------------------------------------------------------------------

def test_lookup_show_with_episode() -> None:
    """When episode is given, the result includes episode detail(s)."""
    search_resp = {"results": [{"id": 123}]}
    tv_resp = {
        "name": "Thuis",
        "first_air_date": "2012-01-01",
        "overview": "Overview.",
        "poster_path": "/p.jpg",
        "seasons": [],
    }
    ep_resp = {
        "episode_number": 6108,
        "name": "De politie krijgt een kans",
        "overview": "Episode overview.",
        "season_number": 31,
    }

    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, tv_resp, ep_resp]):
        result = client.lookup_show("Thuis", 31, 6108)

    assert result is not None
    assert result["title"] == "Thuis"
    assert result["seasons"] == 0
    assert "episodes" in result
    assert len(result["episodes"]) == 1
    assert result["episodes"][0]["name"] == "De politie krijgt een kans"


def test_lookup_show_episode_fallback_to_season() -> None:
    """Single-episode endpoint fails → falls back to season and filters."""
    search_resp = {"results": [{"id": 123}]}
    tv_resp = {
        "name": "Thuis",
        "first_air_date": "2012-01-01",
        "overview": "O.",
        "poster_path": "/p.jpg",
        "seasons": [],
    }
    ep_fail = None  # simulates 404 on single-episode endpoint
    season_resp = {
        "episodes": [
            {"episode_number": 6107, "name": "Ep 6107"},
            {"episode_number": 6108, "name": "Ep 6108"},
            {"episode_number": 6109, "name": "Ep 6109"},
        ]
    }

    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, tv_resp, ep_fail, season_resp]):
        result = client.lookup_show("Thuis", 31, 6108)

    assert result is not None
    assert "episodes" in result
    assert len(result["episodes"]) == 1
    assert result["episodes"][0]["name"] == "Ep 6108"


def test_lookup_show_episode_fallback_no_match() -> None:
    """Fallback season fetch returns no matching episode → no episodes key."""
    search_resp = {"results": [{"id": 123}]}
    tv_resp = {
        "name": "Thuis",
        "first_air_date": "2012-01-01",
        "overview": "O.",
        "poster_path": "/p.jpg",
        "seasons": [],
    }
    ep_fail = None
    season_resp = {"episodes": [{"episode_number": 6107, "name": "Ep 6107"}]}

    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, tv_resp, ep_fail, season_resp]):
        result = client.lookup_show("Thuis", 31, 6108)

    assert result is not None
    assert "episodes" not in result


# ---------------------------------------------------------------------------
# lookup_show — error cases
# ---------------------------------------------------------------------------

def test_lookup_show_not_found() -> None:
    """Search returns empty results → None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", return_value={"results": []}):
        assert client.lookup_show("NonExistentShow999") is None


def test_lookup_show_401_unauthorized() -> None:
    """HTTP 401 on the search call returns None."""
    client = _mock_client()
    # _get_json already returns None on any exception; a 401 raises
    # HTTPError which _get_json swallows and returns None.
    with patch.object(client, "_get_json", return_value=None):
        assert client.lookup_show("Thuis") is None


def test_lookup_show_malformed_response() -> None:
    """A non-dict response from the API is treated as an error."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", return_value="not-json"):
        # _get_json swallows JSON decode errors internally;
        # but resp.json() would raise — here we mock _get_json
        # returning a string directly (simulating a bug/edge case).
        # Since our code checks `results = data.get("results", [])`,
        # a string would raise AttributeError, which is caught.
        assert client.lookup_show("Thuis") is None


def test_lookup_show_tv_details_missing() -> None:
    """Search succeeds but TV details endpoint fails → None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[{"results": [{"id": 123}]}, None]):
        assert client.lookup_show("Thuis") is None


def test_lookup_show_missing_show_id() -> None:
    """Search result has no 'id' field → None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", return_value={"results": [{"name": "Thuis"}]}):
        assert client.lookup_show("Thuis") is None


# ---------------------------------------------------------------------------
# lookup_movie
# ---------------------------------------------------------------------------

def test_lookup_movie_success() -> None:
    """A successful movie lookup returns the expected metadata."""
    search_resp = {"results": [{"id": 456}]}
    movie_resp = {
        "title": "Inception",
        "release_date": "2010-07-16",
        "overview": "A thief who steals corporate secrets.",
        "poster_path": "/xyz.jpg",
    }

    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, movie_resp]):
        result = client.lookup_movie("Inception")

    assert result is not None
    assert result["title"] == "Inception"
    assert result["year"] == 2010
    assert result["seasons"] == 0


def test_lookup_movie_with_year_filter() -> None:
    """The year parameter is forwarded to the search API."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json") as mock_get:
        mock_get.side_effect = [
            {"results": []},  # search returns nothing
        ]
        client.lookup_movie("Inception", year=2010)

    # Verify the search call included the year parameter
    calls = mock_get.call_args_list
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["params"]["query"] == "Inception"
    assert kwargs["params"]["year"] == 2010


def test_lookup_movie_not_found() -> None:
    """Empty search results → None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", return_value={"results": []}):
        assert client.lookup_movie("Neverheardof") is None


def test_lookup_movie_network_error() -> None:
    """Any exception during lookup_movie returns None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client, "_get_json", side_effect=Exception("timeout")):
        assert client.lookup_movie("Inception") is None


# ---------------------------------------------------------------------------
# fetch_poster_image
# ---------------------------------------------------------------------------

_JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100


def test_fetch_poster_image_success() -> None:
    """Successful image fetch returns raw bytes."""
    client = TMDBClient(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.content = _JPEG_BYTES

    with patch.object(client._session, "get", return_value=mock_resp) as mock_get:
        result = client.fetch_poster_image("/abc123.jpg", width=300)

    assert result == _JPEG_BYTES
    mock_get.assert_called_once_with("https://image.tmdb.org/t/p/w300/abc123.jpg")


def test_fetch_poster_image_default_width() -> None:
    """Default width is 500."""
    client = TMDBClient(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.content = _JPEG_BYTES

    with patch.object(client._session, "get", return_value=mock_resp) as mock_get:
        client.fetch_poster_image("/abc.jpg")

    call_url = mock_get.call_args[0][0]
    assert "w500" in call_url


def test_fetch_poster_image_empty_path() -> None:
    """An empty poster_path returns None without making a request."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client._session, "get") as mock_get:
        result = client.fetch_poster_image("")

    assert result is None
    mock_get.assert_not_called()


def test_fetch_poster_image_none_path() -> None:
    """A None poster_path returns None."""
    client = TMDBClient(api_key="test-key")
    with patch.object(client._session, "get") as mock_get:
        result = client.fetch_poster_image(None)  # type: ignore[arg-type]

    assert result is None
    mock_get.assert_not_called()


def test_fetch_poster_image_network_error() -> None:
    """HTTP error or timeout returns None."""
    client = TMDBClient(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("404")

    with patch.object(client._session, "get", return_value=mock_resp):
        result = client.fetch_poster_image("/missing.jpg")

    assert result is None


# ---------------------------------------------------------------------------
# Integration-style: full happy path with real-looking data
# ---------------------------------------------------------------------------

def test_full_show_lookup_with_episode_chain() -> None:
    """End-to-end happy path: search → TV details → episode detail."""
    search_resp = {"results": [{"id": 12345, "name": "Thuis"}]}
    tv_resp = {
        "name": "Thuis",
        "first_air_date": "2012-10-01",
        "overview": "日常生活 drama.",
        "poster_path": "/thuis-poster.jpg",
        "seasons": [{"season_number": i} for i in range(1, 33)],
    }
    ep_resp = {
        "episode_number": 6108,
        "name": "De politie krijgt een kans",
        "overview": "Politieshow overzicht.",
        "season_number": 31,
        "air_date": "2023-05-15",
    }

    client = TMDBClient(api_key="real-key")
    with patch.object(client, "_get_json", side_effect=[search_resp, tv_resp, ep_resp]):
        result = client.lookup_show("Thuis", season=31, episode=6108)

    assert result is not None
    assert result["title"] == "Thuis"
    assert result["year"] == 2012
    assert result["seasons"] == 32
    assert result["poster_path"] == "/thuis-poster.jpg"
    assert result["overview"] == "日常生活 drama."
    assert len(result["episodes"]) == 1
    assert result["episodes"][0]["episode_number"] == 6108
