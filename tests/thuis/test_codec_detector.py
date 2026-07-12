"""Unit tests for thuis.codec_detector.detect_codecs.

Tests cover the real subprocess path (non-existent file → (None, None)),
subprocess exception handling, and simulated ffprobe output via
monkeypatch.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from thuis.codec_detector import detect_codecs


# ===================================================================
# Real subprocess (no mocking) — error paths
# ===================================================================


class TestNonExistentFile:
    """Calling detect_codecs on a path that does not exist."""

    def test_non_existent_file_returns_none(self):
        """Non-existent file → (None, None) (ffprobe returns non-zero)."""
        audio, video = detect_codecs(Path("/tmp/nonexistent_video_file.mp4"))
        assert audio is None
        assert video is None

    def test_non_media_file_returns_none(self, tmp_path):
        """A plain text file is not valid media → (None, None)."""
        f = tmp_path / "readme.txt"
        f.write_text("hello world")
        audio, video = detect_codecs(f)
        assert audio is None
        assert video is None


# ===================================================================
# Simulated ffprobe via monkeypatch
# ===================================================================


class TestMockedFfprobe:
    """Monkeypatch ``subprocess.run`` to simulate ffprobe output."""

    def _make_mock_run(self, returncode: int = 0, stdout: str = "{}"):
        """Factory for a mock ``subprocess.run``."""

        def mock_run(*args, **kwargs):
            mr = MagicMock()
            mr.returncode = returncode
            mr.stdout = stdout
            return mr

        return mock_run

    def test_both_codecs_detected(self, monkeypatch):
        """Simulate ffprobe returning video=h264 and audio=aac."""
        payload = json.dumps({
            "streams": [
                {"codec_type": "video", "codec_name": "h264"},
                {"codec_type": "audio", "codec_name": "aac"},
            ]
        })
        monkeypatch.setattr(subprocess, "run", self._make_mock_run(stdout=payload))
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio == "aac"
        assert video == "h264"

    def test_video_only(self, monkeypatch):
        """Only a video stream present → audio is None."""
        payload = json.dumps({
            "streams": [
                {"codec_type": "video", "codec_name": "hevc"},
            ]
        })
        monkeypatch.setattr(subprocess, "run", self._make_mock_run(stdout=payload))
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video == "hevc"

    def test_audio_only(self, monkeypatch):
        """Only an audio stream present → video is None."""
        payload = json.dumps({
            "streams": [
                {"codec_type": "audio", "codec_name": "mp4a"},
            ]
        })
        monkeypatch.setattr(subprocess, "run", self._make_mock_run(stdout=payload))
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio == "mp4a"
        assert video is None

    def test_no_streams(self, monkeypatch):
        """Empty streams list → (None, None)."""
        payload = json.dumps({"streams": []})
        monkeypatch.setattr(subprocess, "run", self._make_mock_run(stdout=payload))
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    def test_only_first_stream_is_taken(self, monkeypatch):
        """Multiple video/audio streams — only first of each type."""
        payload = json.dumps({
            "streams": [
                {"codec_type": "video", "codec_name": "h264"},
                {"codec_type": "video", "codec_name": "hevc"},
                {"codec_type": "audio", "codec_name": "aac"},
                {"codec_type": "audio", "codec_name": "ac3"},
            ]
        })
        monkeypatch.setattr(subprocess, "run", self._make_mock_run(stdout=payload))
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio == "aac"  # first audio
        assert video == "h264"  # first video


# ===================================================================
# Error conditions via monkeypatch
# ===================================================================


class TestMockedErrors:
    """Subprocess exceptions / non-zero returncode / bad JSON."""

    def test_ffprobe_not_found(self, monkeypatch):
        """FileNotFoundError → (None, None)."""

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("ffprobe not found")

        monkeypatch.setattr(subprocess, "run", mock_run)
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    def test_timeout(self, monkeypatch):
        """TimeoutExpired → (None, None)."""

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="ffprobe", timeout=15)

        monkeypatch.setattr(subprocess, "run", mock_run)
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    def test_non_zero_returncode(self, monkeypatch):
        """ffprobe returns non-zero (e.g. non-media file) → (None, None)."""
        monkeypatch.setattr(
            subprocess, "run",
            self._make_mock_run(returncode=1, stdout=""),
        )
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    def test_invalid_json(self, monkeypatch):
        """ffprobe returns non-JSON output → (None, None)."""
        monkeypatch.setattr(
            subprocess, "run",
            self._make_mock_run(returncode=0, stdout="not json"),
        )
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    def test_missing_streams_key(self, monkeypatch):
        """JSON missing the ``streams`` key → (None, None)."""
        monkeypatch.setattr(
            subprocess, "run",
            self._make_mock_run(returncode=0, stdout=json.dumps({})),
        )
        audio, video = detect_codecs(Path("dummy.mp4"))
        assert audio is None
        assert video is None

    # Helper shared across multiple tests in this class
    @staticmethod
    def _make_mock_run(returncode: int = 0, stdout: str = "{}"):
        def mock_run(*args, **kwargs):
            mr = MagicMock()
            mr.returncode = returncode
            mr.stdout = stdout
            return mr
        return mock_run
