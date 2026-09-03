"""Tests for DRM decrypt worker (C4)."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, PropertyMock, call

import pytest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thuis.drm_decrypt import (
    find_binary,
    get_available_decryption_engine,
    download_init_segment,
    extract_pssh_from_mp4,
    extract_pssh_from_init,
    acquire_license,
    build_n_m3u8dl_re_cmd,
    run_n_m3u8dl_re,
    decrypt_drm_content,
    PsshExtractionError,
    LicenseAcquisitionError,
    DecryptionEngineError,
    N_m3u8DL_RE_Error,
    WIDEVINE_SYSTEM_ID_BYTES,
)


class TestFindBinary:
    """Tests for find_binary()."""

    def test_finds_binary_in_path(self, monkeypatch):
        """Returns path when binary is in PATH."""
        with patch("shutil.which", return_value="/usr/bin/mp4decrypt"):
            result = find_binary("mp4decrypt")
            assert result == "/usr/bin/mp4decrypt"

    def test_returns_none_when_not_found(self, monkeypatch):
        """Returns None when binary not in PATH or common locations."""
        with patch("shutil.which", return_value=None):
            with patch("pathlib.Path.exists", return_value=False):
                result = find_binary("nonexistent_binary_xyz")
                assert result is None


class TestGetAvailableDecryptionEngine:
    """Tests for get_available_decryption_engine()."""

    def test_returns_first_available_engine(self, monkeypatch):
        """Returns first engine found in fallback chain."""
        with patch("thuis.drm_decrypt.find_binary", side_effect=[None, "/usr/bin/shaka-packager", None]):
            engine, path = get_available_decryption_engine()
            assert engine == "SHAKA_PACKAGER"
            assert path == "/usr/bin/shaka-packager"

    def test_returns_mp4decrypt_when_available(self, monkeypatch):
        """Returns MP4DECRYPT as first preference."""
        with patch("thuis.drm_decrypt.find_binary", return_value="/usr/bin/mp4decrypt"):
            engine, path = get_available_decryption_engine()
            assert engine == "MP4DECRYPT"
            assert path == "/usr/bin/mp4decrypt"

    def test_raises_when_no_engine_found(self, monkeypatch):
        """Raises DecryptionEngineError when no engine available."""
        with patch("thuis.drm_decrypt.find_binary", return_value=None):
            with pytest.raises(DecryptionEngineError) as exc_info:
                get_available_decryption_engine()
            assert "No decryption engine found" in str(exc_info.value)
            assert "mp4decrypt" in str(exc_info.value)
            assert "shaka-packager" in str(exc_info.value)
            assert "ffmpeg" in str(exc_info.value)


class TestDownloadInitSegment:
    """Tests for download_init_segment()."""

    def test_downloads_successfully(self):
        """Downloads and returns init segment bytes."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"fake init segment data"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("thuis.drm_decrypt.urlopen", return_value=mock_response):
            result = download_init_segment("https://example.com/init.mp4")
            assert result == b"fake init segment data"

    def test_raises_on_http_error(self):
        """Raises PsshExtractionError on non-200 status."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("thuis.drm_decrypt.urlopen", return_value=mock_response):
            with pytest.raises(PsshExtractionError) as exc_info:
                download_init_segment("https://example.com/init.mp4")
            assert "HTTP 404" in str(exc_info.value)

    def test_raises_on_network_error(self):
        """Raises PsshExtractionError on network failure."""
        from urllib.error import URLError
        with patch("urllib.request.urlopen", side_effect=URLError("connection failed")):
            with pytest.raises(PsshExtractionError) as exc_info:
                download_init_segment("https://example.com/init.mp4")
            assert "Failed to download init segment" in str(exc_info.value)


class TestExtractPsshFromMp4:
    """Tests for extract_pssh_from_mp4()."""

    def test_extracts_widevine_pssh(self):
        """Extracts Widevine PSSH from parsed MP4."""
        # Create mock pssh box with Widevine system ID
        mock_pssh = MagicMock()
        mock_pssh.type = b'pssh'
        mock_pssh.system_id = WIDEVINE_SYSTEM_ID_BYTES
        mock_pssh.data = b"pssh box data"

        mock_box = MagicMock()
        mock_box.children = [mock_pssh]

        import thuis.drm_decrypt as drm_module
        with patch.object(drm_module.pymp4_parser, "MP4") as mock_mp4:
            mock_mp4.parse.return_value = [mock_box]
            result = extract_pssh_from_mp4(b"fake mp4 data")
            assert result == b"pssh box data"

    def test_raises_when_no_widevine_pssh(self):
        """Raises PsshExtractionError when no Widevine PSSH found."""
        # Non-Widevine PSSH
        mock_pssh = MagicMock()
        mock_pssh.type = b'pssh'
        mock_pssh.system_id = b"different-system-id"

        mock_box = MagicMock()
        mock_box.children = [mock_pssh]

        import thuis.drm_decrypt as drm_module
        with patch.object(drm_module.pymp4_parser, "MP4") as mock_mp4:
            mock_mp4.parse.return_value = [mock_box]
            with pytest.raises(PsshExtractionError) as exc_info:
                extract_pssh_from_mp4(b"fake mp4 data")
            assert "No Widevine PSSH found" in str(exc_info.value)

    def test_raises_on_parse_failure(self):
        """Raises PsshExtractionError on MP4 parse failure."""
        import thuis.drm_decrypt as drm_module
        with patch.object(drm_module.pymp4_parser, "MP4") as mock_mp4:
            mock_mp4.parse.side_effect = Exception("parse error")
            with pytest.raises(PsshExtractionError) as exc_info:
                extract_pssh_from_mp4(b"invalid mp4")
            assert "Failed to parse MP4 init segment" in str(exc_info.value)

    def test_raises_when_pymp4_not_available(self):
        """Raises PsshExtractionError when pymp4 not installed."""
        import thuis.drm_decrypt as drm_module
        original_parser = drm_module.pymp4_parser
        try:
            drm_module.pymp4_parser = None
            with pytest.raises(PsshExtractionError) as exc_info:
                extract_pssh_from_mp4(b"fake mp4 data")
            assert "pymp4 not available" in str(exc_info.value)
        finally:
            drm_module.pymp4_parser = original_parser


class TestExtractPsshFromInit:
    """Tests for extract_pssh_from_init()."""

    def test_downloads_and_extracts(self):
        """Downloads init segment and extracts PSSH."""
        with patch("thuis.drm_decrypt.download_init_segment", return_value=b"init data"):
            with patch("thuis.drm_decrypt.extract_pssh_from_mp4", return_value=b"extracted pssh") as mock_extract:
                result = extract_pssh_from_init("https://example.com/init.mp4")
                assert result == b"extracted pssh"
                mock_extract.assert_called_once_with(b"init data")


class TestAcquireLicense:
    """Tests for acquire_license()."""

    def test_full_license_flow(self, tmp_path):
        """Tests complete license acquisition flow with mocked pywidevine."""
        # Mock PSSH
        mock_pssh = MagicMock()
        mock_pssh.system_id = "test-system-id"
        mock_pssh.key_ids = ["key1", "key2"]

        # Mock CDM
        mock_cdm = MagicMock()
        mock_cdm.open.return_value = "session123"
        mock_cdm.get_license_challenge.return_value = b"challenge_data"
        mock_cdm.get_keys.return_value = [
            MagicMock(kid=bytes.fromhex("abcdef1234567890"), key=bytes.fromhex("1122334455667788")),
            MagicMock(kid=bytes.fromhex("fedcba0987654321"), key=bytes.fromhex("8877665544332211")),
        ]

        mock_device = MagicMock()
        mock_device.type = "ANDROID"

        # Mock network calls
        mock_cert_resp = MagicMock()
        mock_cert_resp.status = 200
        mock_cert_resp.read.return_value = b"service_cert"
        mock_cert_resp.__enter__ = MagicMock(return_value=mock_cert_resp)
        mock_cert_resp.__exit__ = MagicMock(return_value=False)

        mock_license_resp = MagicMock()
        mock_license_resp.status = 200
        mock_license_resp.read.return_value = b"license_response"
        mock_license_resp.__enter__ = MagicMock(return_value=mock_license_resp)
        mock_license_resp.__exit__ = MagicMock(return_value=False)

        with patch("pywidevine.pssh.PSSH", return_value=mock_pssh):
            with patch("pywidevine.device.Device.load", return_value=mock_device):
                with patch("pywidevine.cdm.Cdm.from_device", return_value=mock_cdm):
                    with patch("thuis.drm_decrypt.urlopen") as mock_urlopen:
                        # First call = cert, second = license
                        mock_urlopen.side_effect = [mock_cert_resp, mock_license_resp]

                        # Create fake .wvd file
                        wvd_path = tmp_path / "test.wvd"
                        wvd_path.write_bytes(b"fake")

                        result = acquire_license("test_token", b"pssh_data", str(wvd_path))

                        # Verify result
                        assert len(result) == 2
                        assert "abcdef1234567890" in result
                        assert "fedcba0987654321" in result
                        assert result["abcdef1234567890"] == "1122334455667788"
                        assert result["fedcba0987654321"] == "8877665544332211"

                        # Verify calls
                        mock_cdm.set_service_certificate.assert_called_once_with("session123", b"service_cert")
                        mock_cdm.get_license_challenge.assert_called_once_with(
                            "session123", mock_pssh, license_type="STREAMING", privacy_mode=True
                        )
                        mock_cdm.parse_license.assert_called_once_with("session123", b"license_response")
                        mock_cdm.close.assert_called_once_with("session123")

    def test_raises_on_pyam_widevine_import_error(self):
        """Raises LicenseAcquisitionError when pywidevine not available."""
        with patch.dict(sys.modules, {"pywidevine": None, "pywidevine.pssh": None, "pywidevine.device": None, "pywidevine.cdm": None}):
            with pytest.raises(LicenseAcquisitionError) as exc_info:
                acquire_license("token", b"pssh", "/path/to.wvd")
            assert "pywidevine not available" in str(exc_info.value)

    def test_raises_on_cert_request_failure(self):
        """Raises LicenseAcquisitionError when cert request fails."""
        mock_pssh = MagicMock()
        mock_cdm = MagicMock()
        mock_cdm.open.return_value = "session123"

        with patch("pywidevine.pssh.PSSH", return_value=mock_pssh):
            with patch("pywidevine.device.Device.load"):
                with patch("pywidevine.cdm.Cdm.from_device", return_value=mock_cdm):
                    from urllib.error import URLError
                    with patch("thuis.drm_decrypt.urlopen", side_effect=URLError("network error")):
                        with pytest.raises(LicenseAcquisitionError) as exc_info:
                            acquire_license("token", b"pssh", "/path/to.wvd")
                        assert "Service certificate request failed" in str(exc_info.value)

    def test_raises_on_license_request_failure(self):
        """Raises LicenseAcquisitionError when license request fails."""
        mock_pssh = MagicMock()
        mock_cdm = MagicMock()
        mock_cdm.open.return_value = "session123"
        mock_cdm.get_license_challenge.return_value = b"challenge"

        mock_cert_resp = MagicMock()
        mock_cert_resp.status = 200
        mock_cert_resp.read.return_value = b"cert"
        mock_cert_resp.__enter__ = MagicMock(return_value=mock_cert_resp)
        mock_cert_resp.__exit__ = MagicMock(return_value=False)

        from urllib.error import URLError
        with patch("pywidevine.pssh.PSSH", return_value=mock_pssh):
            with patch("pywidevine.device.Device.load"):
                with patch("pywidevine.cdm.Cdm.from_device", return_value=mock_cdm):
                    with patch("thuis.drm_decrypt.urlopen") as mock_urlopen:
                        mock_urlopen.side_effect = [
                            mock_cert_resp,
                            URLError("license server down")
                        ]
                        with pytest.raises(LicenseAcquisitionError) as exc_info:
                            acquire_license("token", b"pssh", "/path/to.wvd")
                        assert "License request failed" in str(exc_info.value)

    def test_raises_when_no_keys_returned(self):
        """Raises LicenseAcquisitionError when no CONTENT keys returned."""
        mock_pssh = MagicMock()
        mock_cdm = MagicMock()
        mock_cdm.open.return_value = "session123"
        mock_cdm.get_license_challenge.return_value = b"challenge"
        mock_cdm.get_keys.return_value = []  # No keys!

        mock_cert_resp = MagicMock()
        mock_cert_resp.status = 200
        mock_cert_resp.read.return_value = b"cert"
        mock_cert_resp.__enter__ = MagicMock(return_value=mock_cert_resp)
        mock_cert_resp.__exit__ = MagicMock(return_value=False)

        mock_license_resp = MagicMock()
        mock_license_resp.status = 200
        mock_license_resp.read.return_value = b"license"
        mock_license_resp.__enter__ = MagicMock(return_value=mock_license_resp)
        mock_license_resp.__exit__ = MagicMock(return_value=False)

        with patch("pywidevine.pssh.PSSH", return_value=mock_pssh):
            with patch("pywidevine.device.Device.load"):
                with patch("pywidevine.cdm.Cdm.from_device", return_value=mock_cdm):
                    with patch("thuis.drm_decrypt.urlopen") as mock_urlopen:
                        mock_urlopen.side_effect = [mock_cert_resp, mock_license_resp]
                        with pytest.raises(LicenseAcquisitionError) as exc_info:
                            acquire_license("token", b"pssh", "/path/to.wvd")
                        assert "No CONTENT keys returned" in str(exc_info.value)

    def test_closes_session_on_exception(self):
        """Ensures session is closed even on exception."""
        mock_pssh = MagicMock()
        mock_cdm = MagicMock()
        mock_cdm.open.return_value = "session123"
        mock_cdm.get_license_challenge.side_effect = Exception("challenge failed")

        mock_cert_resp = MagicMock()
        mock_cert_resp.status = 200
        mock_cert_resp.read.return_value = b"cert"
        mock_cert_resp.__enter__ = MagicMock(return_value=mock_cert_resp)
        mock_cert_resp.__exit__ = MagicMock(return_value=False)

        with patch("pywidevine.pssh.PSSH", return_value=mock_pssh):
            with patch("pywidevine.device.Device.load"):
                with patch("pywidevine.cdm.Cdm.from_device", return_value=mock_cdm):
                    with patch("urllib.request.urlopen", return_value=mock_cert_resp):
                        with pytest.raises(LicenseAcquisitionError):
                            acquire_license("token", b"pssh", "/path/to.wvd")
                        mock_cdm.close.assert_called_once_with("session123")


class TestBuildNM3u8dlReCmd:
    """Tests for build_n_m3u8dl_re_cmd()."""

    def test_builds_command_with_keys(self):
        """Builds correct command with multiple keys."""
        keys = {
            "kid1": "key1",
            "kid2": "key2",
        }
        cmd = build_n_m3u8dl_re_cmd(
            mpd_url="https://example.com/manifest.mpd",
            keys=keys,
            output_dir=Path("/tmp/out"),
            output_name="test_video",
            engine="MP4DECRYPT",
        )

        assert cmd[0] == "N_m3u8DL-RE"
        assert cmd[1] == "https://example.com/manifest.mpd"
        assert "--key" in cmd
        assert "kid1:key1" in cmd
        assert "kid2:key2" in cmd
        assert "--save-dir" in cmd
        assert "/tmp/out" in cmd
        assert "--save-name" in cmd
        assert "test_video" in cmd
        assert "--decryption-engine" in cmd
        assert "MP4DECRYPT" in cmd


class TestRunNM3u8dlRe:
    """Tests for run_n_m3u8dl_re()."""

    def test_returns_output_file_on_success(self, tmp_path):
        """Returns Path to output file on successful run."""
        # Create a fake output file
        output_file = tmp_path / "test_video.mp4"
        output_file.write_bytes(b"fake video content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = run_n_m3u8dl_re([
                "N_m3u8DL-RE", "https://example.com/manifest.mpd",
                "--save-dir", str(tmp_path),
                "--save-name", "test_video",
                "--decryption-engine", "MP4DECRYPT"
            ])
            assert result == output_file

    def test_raises_on_nonzero_exit(self):
        """Raises N_m3u8DL_RE_Error on non-zero exit."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="error output",
                stderr="error details"
            )
            with pytest.raises(N_m3u8DL_RE_Error) as exc_info:
                run_n_m3u8dl_re(["N_m3u8DL-RE", "url"])
            assert "exited with code 1" in str(exc_info.value)

    def test_raises_on_timeout(self):
        """Raises N_m3u8DL_RE_Error on timeout."""
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 600)):
            with pytest.raises(N_m3u8DL_RE_Error) as exc_info:
                run_n_m3u8dl_re(["N_m3u8DL-RE", "url"])
            assert "timed out" in str(exc_info.value)

    def test_raises_on_not_found(self):
        """Raises N_m3u8DL_RE_Error when binary not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            with pytest.raises(N_m3u8DL_RE_Error) as exc_info:
                run_n_m3u8dl_re(["N_m3u8DL-RE", "url"])
            assert "not found in PATH" in str(exc_info.value)


class TestDecryptDrmContent:
    """Integration tests for decrypt_drm_content()."""

    def test_policy_no_skip(self, tmp_path, monkeypatch):
        """Test that policy=no is handled upstream (not in this module)."""
        # This test is conceptual - policy check happens in main.py
        # The decrypt worker is only called when policy=yes
        pass

    def test_returns_none_when_no_cdm(self, tmp_path):
        """Returns None when CDM unavailable."""
        with patch("thuis.cdm.ensure_cdm", return_value=None):
            result = decrypt_drm_content(
                vudrm_token="test_token",
                mpd_url="https://example.com/manifest.mpd",
                init_url="https://example.com/init.mp4",
                output_dir=tmp_path,
                output_name="test",
            )
            assert result is None

    def test_returns_none_on_pssh_extraction_failure(self, tmp_path):
        """Returns None when PSSH extraction fails."""
        with patch("thuis.cdm.ensure_cdm", return_value="/fake/wvd"):
            with patch("thuis.drm_decrypt.extract_pssh_from_init", side_effect=PsshExtractionError("no pssh")):
                result = decrypt_drm_content(
                    vudrm_token="test_token",
                    mpd_url="https://example.com/manifest.mpd",
                    init_url="https://example.com/init.mp4",
                    output_dir=tmp_path,
                    output_name="test",
                )
                assert result is None

    def test_returns_none_on_license_failure(self, tmp_path):
        """Returns None when license acquisition fails."""
        with patch("thuis.cdm.ensure_cdm", return_value="/fake/wvd"):
            with patch("thuis.drm_decrypt.extract_pssh_from_init", return_value=b"pssh"):
                with patch("thuis.drm_decrypt.acquire_license", side_effect=LicenseAcquisitionError("license failed")):
                    result = decrypt_drm_content(
                        vudrm_token="test_token",
                        mpd_url="https://example.com/manifest.mpd",
                        init_url="https://example.com/init.mp4",
                        output_dir=tmp_path,
                        output_name="test",
                    )
                    assert result is None

    def test_returns_none_on_no_engine(self, tmp_path):
        """Returns None when no decryption engine available."""
        with patch("thuis.cdm.ensure_cdm", return_value="/fake/wvd"):
            with patch("thuis.drm_decrypt.extract_pssh_from_init", return_value=b"pssh"):
                with patch("thuis.drm_decrypt.acquire_license", return_value={"kid1": "key1"}):
                    with patch("thuis.drm_decrypt.get_available_decryption_engine", side_effect=DecryptionEngineError("no engine")):
                        result = decrypt_drm_content(
                            vudrm_token="test_token",
                            mpd_url="https://example.com/manifest.mpd",
                            init_url="https://example.com/init.mp4",
                            output_dir=tmp_path,
                            output_name="test",
                        )
                        assert result is None

    def test_successful_decryption(self, tmp_path):
        """Returns output file path on successful decryption."""
        output_file = tmp_path / "test.mp4"
        output_file.write_bytes(b"decrypted video")

        with patch("thuis.cdm.ensure_cdm", return_value="/fake/wvd"):
            with patch("thuis.drm_decrypt.extract_pssh_from_init", return_value=b"pssh"):
                with patch("thuis.drm_decrypt.acquire_license", return_value={"kid1": "key1"}):
                    with patch("thuis.drm_decrypt.get_available_decryption_engine", return_value=("MP4DECRYPT", "/usr/bin/mp4decrypt")):
                        with patch("thuis.drm_decrypt.run_n_m3u8dl_re", return_value=output_file):
                            with patch("shutil.move") as mock_move:
                                result = decrypt_drm_content(
                                    vudrm_token="test_token",
                                    mpd_url="https://example.com/manifest.mpd",
                                    init_url="https://example.com/init.mp4",
                                    output_dir=tmp_path,
                                    output_name="test",
                                )
                                assert result == tmp_path / "test.mp4"
                                mock_move.assert_called_once()


class TestIntegrationWithMocks:
    """Higher-level integration tests with full mocking."""

    def test_full_pipeline_mocked(self, tmp_path):
        """Tests full pipeline with all external calls mocked."""
        # Setup
        final_output = tmp_path / "flikken_maastricht_s17e02.mp4"
        final_output.write_bytes(b"final video")

        with patch("thuis.cdm.ensure_cdm", return_value="/fake/wvd"):
            with patch("thuis.drm_decrypt.extract_pssh_from_init", return_value=b"pssh_data"):
                with patch("thuis.drm_decrypt.acquire_license", return_value={
                    "abcdef1234567890": "1122334455667788",
                    "fedcba0987654321": "8877665544332211",
                }):
                    with patch("thuis.drm_decrypt.get_available_decryption_engine", return_value=("MP4DECRYPT", "/usr/bin/mp4decrypt")):
                        with patch("thuis.drm_decrypt.run_n_m3u8dl_re", return_value=final_output):
                            with patch("shutil.move") as mock_move:
                                result = decrypt_drm_content(
                                    vudrm_token="vrt|2026-09-02T18:41:10Z|v2|fake_token",
                                    mpd_url="https://vod.vrtcdn.be/.../manifest.mpd",
                                    init_url="https://vod.vrtcdn.be/.../init.m3u8",
                                    output_dir=tmp_path,
                                    output_name="flikken_maastricht_s17e02",
                                )
                                assert result == final_output
                                mock_move.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])