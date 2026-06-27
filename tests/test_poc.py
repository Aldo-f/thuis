import sys
import os
# Add the repository root to sys.path so we can import thuis.main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import subprocess
from unittest.mock import patch, MagicMock

from thuis.main import get_credentials, build_yt_dlp_args, get_yt_dlp_location, patch_ytdlp_if_needed, main, get_yt_dlp_cmd


def test_poc_uses_default_credentials_when_env_missing(monkeypatch):
    # Ensure env vars are not set
    monkeypatch.delenv("VRT_EMAIL", raising=False)
    monkeypatch.delenv("VRT_PASSWORD", raising=False)
    # Mock subprocess.run to capture the actual yt-dlp call
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"):
        mock_run.return_value = MagicMock(returncode=0)
        test_url = "https://example.com/video"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                # Expect exit code 0 (success)
                assert e.code == 0
        finally:
            sys.argv = original_argv
        # Ensure subprocess.run was called at least once (the yt-dlv call)
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        # Check that the command includes --username and --password with defaults
        assert "--username" in called_args
        assert "--password" in called_args
        idx_user = called_args.index("--username")
        idx_pass = called_args.index("--password")
        assert called_args[idx_user + 1] == "kuxelu@ipdeer.com"
        assert called_args[idx_pass + 1] == "Els123456"
        # Check that output dir is media
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        assert called_args[idx_o + 1] == "media/%(title)s.%(ext)s"


def test_poc_uses_provided_credentials(monkeypatch):
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"):
        mock_run.return_value = MagicMock(returncode=0)
        test_url = "https://example.com/video2"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        assert "--username" in called_args
        assert "--password" in called_args
        idx_user = called_args.index("--username")
        idx_pass = called_args.index("--password")
        assert called_args[idx_user + 1] == "test@example.com"
        assert called_args[idx_pass + 1] == "testpass"
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        assert called_args[idx_o + 1] == "media/%(title)s.%(ext)s"


def test_poc_handles_file_input(monkeypatch, tmp_path):
    # Create a temp file with URLs
    url_file = tmp_path / "urls.txt"
    url_file.write_text("https://example.com/video1\nhttps://example.com/video2\n")
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"):
        mock_run.return_value = MagicMock(returncode=0)
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--file", str(url_file)]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv
        # Should have been called once with both URLs
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        # Check that both URLs are present in the arguments
        assert "https://example.com/video1" in called_args
        assert "https://example.com/video2" in called_args
        # Output dir default
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        assert called_args[idx_o + 1] == "media/%(title)s.%(ext)s"


def test_poc_dry_run_flag(monkeypatch):
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"):
        mock_run.return_value = MagicMock(returncode=0)
        test_url = "https://example.com/video3"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--dry-run", test_url]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        assert "--simulate" in called_args
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        assert called_args[idx_o + 1] == "media/%(title)s.%(ext)s"


def test_get_yt_dlp_cmd_returns_patched_version():
    """Verify get_yt_dlp_cmd() returns a yt-dlp command that yields version ≥ 2026.06.09."""
    cmd = get_yt_dlp_cmd()
    result = subprocess.run(cmd + ['--version'], capture_output=True, text=True)
    version = result.stdout.strip()
    assert version >= '2026.06.09', f"Expected yt-dlp >= 2026.06.09, got '{version}' (cmd: {cmd})"


if __name__ == "__main__":
    # Simple runner for debugging. If pytest isn't available, exit gracefully.
    try:
        import pytest
    except Exception:
        print("pytest not available; skipping test runner")
    else:
        pytest.main([__file__, "-v"])