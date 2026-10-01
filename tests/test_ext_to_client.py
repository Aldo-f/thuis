"""Tests for ext_to_client — uploads .torrent files to ext.to."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from thuis.plugins.ext_to_client import ExtToClient


class TestExtToClient:
    """ExtToClient logs in and uploads torrent files."""

    def test_init_with_credentials(self):
        """Client stores credentials from config."""
        client = ExtToClient(
            username="testuser",
            password="testpass",
        )
        assert client._username == "testuser"
        assert client._password == "testpass"

    def test_login_makes_post_request(self):
        """login() sends POST to ext.to with username/password."""
        with patch("thuis.plugins.ext_to_client.requests.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html>logout</html>"
            mock_response.cookies = {"session_id": "abc123"}
            mock_session.get.return_value = mock_response
            mock_session.post.return_value = mock_response
            client = ExtToClient(username="testuser", password="testpass")
            client.login()
            # Verify POST was called with login URL
            assert mock_session.post.called
            call_args = mock_session.post.call_args
            assert "login" in call_args[0][0].lower() or "login" in str(call_args).lower()

    def test_upload_torrent_requires_login(self):
        """upload_torrent raises if not logged in."""
        client = ExtToClient(username="testuser", password="testpass")
        client._logged_in = False
        with pytest.raises(RuntimeError, match="Not logged in"):
            client.upload_torrent(
                torrent_path=Path("/tmp/fake.torrent"),
                title="Test",
                category="TV",
                description="Test desc",
            )
