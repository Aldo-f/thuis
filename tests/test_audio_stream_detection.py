"""Tests for the is_audio_only_stream helper.

We mock ``urllib.request.urlopen`` to return a small HLS manifest containing
a single ``#EXT-X-STREAM-INF`` line with either an audio or video codec.
"""
import io
import types
import unittest
from unittest.mock import patch, MagicMock

# Import the function from the module under test
from thuis.main import is_audio_only_stream

class TestAudioOnlyStreamDetection(unittest.TestCase):
    def make_response(self, manifest: str):
        """Create a mock response object that mimics ``urllib.request.urlopen``.
        ``read`` returns the manifest bytes and ``status`` is set to 200.
        """
        mock = MagicMock()
        mock.read.return_value = manifest.encode('utf-8')
        mock.__enter__.return_value = mock
        mock.status = 200
        return mock

    @patch('urllib.request.urlopen')
    def test_audio_only_manifest(self, mock_urlopen):
        manifest = """#EXTM3U\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS=\"mp4a.40.2\"\naudio.m3u8"""
        mock_urlopen.return_value = self.make_response(manifest)
        self.assertTrue(is_audio_only_stream('http://example.com/playlist.m3u8'))

    @patch('urllib.request.urlopen')
    def test_video_manifest(self, mock_urlopen):
        manifest = """#EXTM3U\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2000000,CODECS=\"avc1.4d401f,mp4a.40.2\"\nvideo.m3u8"""
        mock_urlopen.return_value = self.make_response(manifest)
        self.assertFalse(is_audio_only_stream('http://example.com/playlist.m3u8'))

    @patch('urllib.request.urlopen', side_effect=Exception('network error'))
    def test_network_error_fallback(self, mock_urlopen):
        # On any error we conservatively treat as not audio‑only
        self.assertFalse(is_audio_only_stream('http://example.com/playlist.m3u8'))

if __name__ == '__main__':
    unittest.main()
