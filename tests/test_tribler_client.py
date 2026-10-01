"""Tests for tribler_client — submits torrents to Tribler for anonymous seeding."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from thuis.plugins.tribler_client import TriblerClient


class TestTriblerClient:
    """TriblerClient submits torrents to Tribler REST API."""

    def test_init_with_defaults(self):
        """Client uses default port 8085 and hops=3."""
        client = TriblerClient()
        assert client._api_port == 8085
        assert client._anon_hops == 3

    def test_init_with_custom_config(self):
        """Client accepts custom port, key, hops."""
        client = TriblerClient(
            api_port=9090,
            api_key="secret",
            anon_hops=2,
            safe_seeding=False,
        )
        assert client._api_port == 9090
        assert client._api_key == "secret"
        assert client._anon_hops == 2
        assert client._safe_seeding is False

    def test_add_torrent_makes_put_request(self, tmp_path):
        """add_torrent sends PUT to /downloads with torrent data."""
        # Create a real temp file so the torrent_path.exists() check passes
        torrent_file = tmp_path / "fake.torrent"
        torrent_file.write_bytes(b"d4:infod6:lengthi0e4:name8:fake.txteee")
        client = TriblerClient()
        with patch("thuis.plugins.tribler_client.requests.put") as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"started": True}
            mock_put.return_value = mock_response
            result = client.add_torrent(torrent_file)
            assert result is True
            assert mock_put.called
            call_kwargs = mock_put.call_args
            assert "downloads" in call_kwargs[0][0]

    def test_add_torrent_returns_false_on_error(self, tmp_path):
        """add_torrent returns False on HTTP error."""
        torrent_file = tmp_path / "fake.torrent"
        torrent_file.write_bytes(b"d4:infod6:lengthi0e4:name8:fake.txteee")
        client = TriblerClient()
        with patch("thuis.plugins.tribler_client.requests.put") as mock_put:
            mock_put.side_effect = Exception("Connection refused")
            result = client.add_torrent(torrent_file)
            assert result is False
