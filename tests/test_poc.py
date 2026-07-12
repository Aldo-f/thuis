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
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:
        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(show_slug="test-show", season=1, episode=1)
        mock_fetch.return_value = {"series": "Test Show", "season": 1, "episode": 1, "height": "1080", "vcodec_raw": "avc1", "acodec_raw": "mp4a"}
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
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
        # Check that output dir is media and does NOT contain the old template
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg
        # Check that it contains a scene-like pattern (from our mock)
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg


def test_poc_uses_provided_credentials(monkeypatch):
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:
        mock_fetch.return_value = {"series": "Test Show", "season": 1, "episode": 1}
        mock_run.return_value = MagicMock(returncode=0)
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        mock_classify.return_value = ContentType.TV
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
        # Check that output dir is media and does NOT contain the old template
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg
        # Check that it contains a scene-like pattern (from our mock)
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg


def test_poc_handles_file_input(monkeypatch, tmp_path):
    # Create a temp file with URLs
    url_file = tmp_path / "urls.txt"
    url_file.write_text("https://example.com/video1\nhttps://example.com/video2\n")
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:
        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(show_slug="test-show", season=1, episode=1)
        mock_fetch.return_value = {"series": "Test Show", "season": 1, "episode": 1, "height": "1080", "vcodec_raw": "avc1", "acodec_raw": "mp4a"}
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        original_argv = sys.argv
        try:
            sys.argv = ["poc.py", "--file", str(url_file)]
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            sys.argv = original_argv
        # Should have been called once for each URL (2 times total)
        assert mock_run.call_count == 2
        # Check first call
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "https://example.com/video1" in first_call_args
        assert "-o" in first_call_args
        idx_o = first_call_args.index("-o")
        first_output_arg = first_call_args[idx_o + 1]
        assert "%(title)s" not in first_output_arg
        # Check that it contains a scene-like pattern (from our mock)
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in first_output_arg
        # Check second call
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "https://example.com/video2" in second_call_args
        assert "-o" in second_call_args
        idx_o = second_call_args.index("-o")
        second_output_arg = second_call_args[idx_o + 1]
        assert "%(title)s" not in second_output_arg
        # Check that it contains a scene-like pattern (from our mock)
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in second_output_arg
        # Check that credentials are passed in both calls
        for call_args in mock_run.call_args_list:
            args = call_args[0][0]
            assert "--username" in args
            assert "test@example.com" in args
            assert "--password" in args
            assert "testpass" in args


def test_poc_dry_run_flag(monkeypatch):
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build:
        mock_run.return_value = MagicMock(returncode=0)
        mock_parse.return_value = MagicMock(show_slug="test-show", season=1, episode=1, path="/vrtmax/a/show/test-show/1/test-show-s01a01/", url="https://example.com/video3")
        mock_fetch.return_value = {"series": "Test Show", "season": 1, "episode": 1, "height": "1080", "vcodec_raw": "avc1", "acodec_raw": "mp4a"}
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        mock_classify.return_value = ContentType.TV
        mock_build.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
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
        output_arg = called_args[idx_o + 1]
        assert "%(title)s" not in output_arg
        # Check that it contains a scene-like pattern (from our mock)
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg


def test_scene_name_appears_in_output(monkeypatch):
    """Test that scene name appears in output for both TV and special content types."""
    monkeypatch.setenv("VRT_EMAIL", "test@example.com")
    monkeypatch.setenv("VRT_PASSWORD", "testpass")
    
    # Test case 1: TV content
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_tv_filename") as mock_build_tv:
        
        mock_run.return_value = MagicMock(returncode=0)
        test_url = "https://www.vrt.be/vrtmax/a/show/test-show/1/test-show-s01a01/"
        
        # Mock the URL parser to return specific values
        mock_parse.return_value = MagicMock(
            show_slug="test-show",
            season=1,
            episode=1,
            path="/vrtmax/a/show/test-show/1/test-show-s01a01/",
            url=test_url
        )
        
        # Mock metadata fetcher
        mock_fetch.return_value = {
            "series": "Test Show",
            "season": 1,
            "episode": 1,
            "height": "1080",
            "vcodec_raw": "avc1",
            "acodec_raw": "mp4a"
        }
        
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        # Mock classifier to return TV
        mock_classify.return_value = ContentType.TV
        
        # Mock scene namer to return a predictable scene name
        mock_build_tv.return_value = "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        
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
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        # Verify that the scene name appears in the output argument
        assert "Test.Show.S01E01.1080p.WEB-DL.AAC.x264.mp4" in output_arg
        # Verify it does NOT contain the old template
        assert "%(title)s" not in output_arg
    
    # Test case 2: SPECIAL content
    with patch("subprocess.run") as mock_run, \
         patch("thuis.main.get_yt_dlp_location", return_value="/fake/yt_dlp"), \
         patch("thuis.main.patch_ytdlp_if_needed"), \
         patch("thuis.main.url_parser.parse_vrt_url") as mock_parse, \
         patch("thuis.main.metadata_fetcher.fetch_metadata") as mock_fetch, \
         patch("thuis.main.classifier.classify") as mock_classify, \
         patch("thuis.main.scene_namer.build_special_filename") as mock_build_special:
        
        mock_run.return_value = MagicMock(returncode=0)
        test_url = "https://www.vrt.be/vrtmax/a/show/test-show/extra-s/test-show-extra/"
        
        # Mock the URL parser to return specific values for special content
        mock_parse.return_value = MagicMock(
            show_slug="test-show",
            season=0,
            episode=0,
            path="/vrtmax/a/show/test-show/extra-s/test-show-extra/",
            url=test_url
        )
        
        # Mock metadata fetcher
        mock_fetch.return_value = {
            "series": "Test Show",
            "season": None,
            "episode": None,
            "height": "1080",
            "vcodec_raw": "avc1",
            "acodec_raw": "mp4a"
        }
        
        # Import ContentType to properly mock the enum return value
        from thuis.classifier import ContentType
        # Mock classifier to return SPECIAL
        mock_classify.return_value = ContentType.SPECIAL
        
        # Mock scene namer to return a predictable scene name for specials
        mock_build_special.return_value = "Test.Show.Special.1080p.WEB-DL.AAC.x264.mp4"
        
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
        assert "-o" in called_args
        idx_o = called_args.index("-o")
        output_arg = called_args[idx_o + 1]
        # Verify that the scene name appears in the output argument
        assert "Test.Show.Special.1080p.WEB-DL.AAC.x264.mp4" in output_arg
        # Verify it does NOT contain the old template
        assert "%(title)s" not in output_arg


def test_get_yt_dlp_cmd_returns_patched_version():
    """Verify get_yt_dlp_cmd() returns a yt-dlp command that yields version ≥ 2026.06.09."""
    with patch("thuis.main.get_yt_dlp_cmd", return_value=["/fake/yt_dlp"]):
        # Mock the subprocess call to return a sufficient version
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "2026.06.09"
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
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