"""Tests for thuis.downloader_yt — yt-dlp downloader wrapper."""
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root (parent of tests) to sys.path so we can import thuis
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from subprocess import TimeoutExpired

# Import the module under test
from thuis.downloader_yt import find_yt_dlp, download_with_yt_dlp


def test_find_yt_dlp_when_binary_exists():
    """Test find_yt_dlp returns the path when yt-dlp is found."""
    with patch("thuis.downloader_yt.os.path.exists") as mock_exists:
        # Make the first candidate path exist
        mock_exists.side_effect = lambda path: path == "/usr/local/bin/yt-dlp"
        with patch("thuis.downloader_yt.shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/yt-dlp"
            # We also need to mock the version check to avoid calling subprocess
            with patch("thuis.downloader_yt.subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.communicate.return_value = ("2026.06.09", "")
                mock_popen.return_value = mock_proc
                path = find_yt_dlp()
                assert path == ["/usr/local/bin/yt-dlp"]


def test_find_yt_dlp_when_binary_missing_downloads_success():
    """Test find_yt_dlp downloads yt-dlp when not found."""
    with patch("thuis.downloader_yt.os.path.exists") as mock_exists:
        mock_exists.return_value = False  # Nothing exists initially
        with patch("thuis.downloader_yt.shutil.which") as mock_which:
            mock_which.return_value = None  # Not in PATH
            # Mock the locations we check (isfile checks for existing binary)
            with patch("thuis.downloader_yt.os.path.isfile") as mock_isfile:
                mock_isfile.return_value = False
                with patch("thuis.downloader_yt.os.environ") as mock_environ:
                    mock_environ.get.return_value = None
                    # Mock the download and chmod
                    with patch("thuis.downloader_yt.requests.get") as mock_get:
                        mock_response = MagicMock()
                        mock_response.content = b"fake binary"
                        mock_response.raise_for_status.return_value = None
                        mock_get.return_value = mock_response
                        with patch("thuis.downloader_yt.open") as mock_open:
                            mock_file = MagicMock()
                            mock_open.return_value.__enter__.return_value = mock_file
                            with patch("thuis.downloader_yt.os.chmod") as mock_chmod:
                                path = find_yt_dlp()
                                # We expect the path to be the one we constructed
                                # In the actual function, it might be .venv/bin/yt-dlp or similar
                                # We'll just check that it returned a list with one string ending in yt-dlp
                                assert isinstance(path, list)
                                assert len(path) == 1
                                assert path[0].endswith("yt-dlp")
                                # Verify that we attempted to download and set executable
                                mock_get.assert_called_once()
                                mock_chmod.assert_called_once()


def test_download_with_yt_dlp_success():
    """Test download_with_yt_dlp when subprocess succeeds."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.return_value = ["/fake/path/yt-dlp"]
        with patch("thuis.downloader_yt.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = download_with_yt_dlp(
                url="https://example.com/video",
                output_path="/tmp/output",
                quality="best",
                cookies="/tmp/cookies.txt",
                simulate=True,
            )

            assert result is True
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            cmd = args[0]
            assert "/fake/path/yt-dlp" in cmd
            assert "--simulate" in cmd
            assert "-f" in cmd
            assert "best" in cmd
            assert "--cookies" in cmd
            assert "/tmp/cookies.txt" in cmd
            assert "-o" in cmd
            # The output template is built in the function; we can check for the output path
            assert any("/tmp/output" in arg for arg in cmd)


def test_download_with_yt_dlp_failure_nonzero_returncode():
    """Test download_with_yt_dlp when subprocess returns non-zero."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.return_value = ["/fake/path/yt-dlp"]
        with patch("thuis.downloader_yt.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = download_with_yt_dlp(url="https://example.com/video")
            assert result is False


def test_download_with_yt_dlp_file_not_found():
    """Test download_with_yt_dlp when yt-dlp file is not found."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.side_effect = FileNotFoundError("yt-dlp not found")
        with pytest.raises(FileNotFoundError):
            download_with_yt_dlp(url="https://example.com/video")


def test_download_with_yt_dlp_timeout():
    """Test download_with_yt_dlp when subprocess times out."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.return_value = ["/fake/path/yt-dlp"]
        with patch("thuis.downloader_yt.subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutExpired("yt-dlp", 30)

            result = download_with_yt_dlp(url="https://example.com/video", timeout=30)
            # Assuming the function returns False on timeout
            assert result is False


def test_download_with_yt_dlp_file_not_found():
    """Test download_with_yt_dlp when yt-dlp file is not found."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.side_effect = FileNotFoundError("yt-dlp not found")
        with pytest.raises(FileNotFoundError):
            download_with_yt_dlp(url="https://example.com/video")


def test_download_with_yt_dlp_timeout():
    """Test download_with_yt_dlp when subprocess times out."""
    with patch("thuis.downloader_yt.find_yt_dlp") as mock_find:
        mock_find.return_value = ["/fake/path/yt-dlp"]
        with patch("thuis.downloader_yt.subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutExpired("yt-dlp", 30)

            result = download_with_yt_dlp(url="https://example.com/video", timeout=30)
            # Assuming the function returns False on timeout
            assert result is False