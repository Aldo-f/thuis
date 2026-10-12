"""Tests for the qBittorrent client: add_torrent forwards category + tags."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from thuis.plugins.qbittorrent_client import QBittorrentClient


class TestAddTorrentTags:
    """add_torrent must pass ``tags`` (comma-separated) to the API."""

    def _make_client(self):
        client = QBittorrentClient(
            host="torrent.aldof.duckdns.org",
            username="aldo",
            password="secret",
            api_key="",
            socks5_proxy=None,
        )
        client._auth_headers = {"Cookie": "SID=abc"}
        return client

    def test_add_torrent_passes_tags(self, tmp_path):
        """tags= is forwarded to the /api/v2/torrents/add POST body."""
        torrent = tmp_path / "show.torrent"
        torrent.write_bytes(b"\x00")

        client = self._make_client()
        with patch.object(client, "auth_log_in", return_value=True):
            with patch.object(client.session, "post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.text = "Ok."
                mock_resp.raise_for_status = MagicMock()
                mock_post.return_value = mock_resp

                result = client.add_torrent(
                    torrent_file=torrent,
                    save_path="/downloads/Media/tv",
                    category="Media/Tv",
                    tags="Thuis",
                )

        assert result is True
        assert mock_post.call_count == 1
        _, kwargs = mock_post.call_args
        assert kwargs["data"]["tags"] == "Thuis"
        assert kwargs["data"]["category"] == "Media/Tv"
        assert kwargs["data"]["savepath"] == "/downloads/Media/tv"

    def test_add_torrent_empty_tags_means_no_tag(self, tmp_path):
        """An empty/falsy default_tag must send an empty tags string (no tag)."""
        torrent = tmp_path / "show.torrent"
        torrent.write_bytes(b"\x00")

        client = self._make_client()
        with patch.object(client, "auth_log_in", return_value=True):
            with patch.object(client.session, "post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.text = "Ok."
                mock_resp.raise_for_status = MagicMock()
                mock_post.return_value = mock_resp

                client.add_torrent(
                    torrent_file=torrent,
                    save_path="/downloads/Media/tv",
                    category="",
                    tags="",
                )

        _, kwargs = mock_post.call_args
        assert kwargs["data"]["tags"] == ""

    def test_add_torrent_multiple_tags_comma_separated(self, tmp_path):
        """Multiple tags are joined with commas, as qBittorrent expects."""
        torrent = tmp_path / "show.torrent"
        torrent.write_bytes(b"\x00")

        client = self._make_client()
        with patch.object(client, "auth_log_in", return_value=True):
            with patch.object(client.session, "post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.text = "Ok."
                mock_resp.raise_for_status = MagicMock()
                mock_post.return_value = mock_resp

                client.add_torrent(
                    torrent_file=torrent,
                    save_path="/downloads/Media/tv",
                    category="",
                    tags="Thuis,4k",
                )

        _, kwargs = mock_post.call_args
        assert kwargs["data"]["tags"] == "Thuis,4k"