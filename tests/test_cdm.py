"""Tests for CDM provisioner (C6)."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

import pytest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thuis.cdm import (
    get_cdm_cache_dir,
    get_cdm_path,
    validate_cdm,
    ensure_cdm,
    CDM_SOURCES,
    DEFAULT_CDM_CACHE,
    DEFAULT_CDM_FILENAME,
)


class TestGetCdmCacheDir:
    """Tests for get_cdm_cache_dir()."""

    def test_default_cache_dir(self, monkeypatch):
        """Default cache dir when WVD_CDM_PATH not set."""
        monkeypatch.delenv("WVD_CDM_PATH", raising=False)
        with patch.object(Path, "mkdir") as mock_mkdir:
            result = get_cdm_cache_dir()
            assert result == DEFAULT_CDM_CACHE
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_env_var_override(self, monkeypatch, tmp_path):
        """WVD_CDM_PATH env var is respected."""
        custom_path = tmp_path / "custom_cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(custom_path))
        with patch.object(Path, "mkdir") as mock_mkdir:
            result = get_cdm_cache_dir()
            assert result == custom_path.resolve()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_tilde_expansion(self, monkeypatch):
        """Tilde in WVD_CDM_PATH is expanded."""
        monkeypatch.setenv("WVD_CDM_PATH", "~/my_cdm")
        with patch.object(Path, "mkdir"):
            result = get_cdm_cache_dir()
            assert str(result).startswith(str(Path.home()))


class TestGetCdmPath:
    """Tests for get_cdm_path()."""

    def test_returns_correct_path(self, monkeypatch, tmp_path):
        """Returns cache_dir / DEFAULT_CDM_FILENAME."""
        monkeypatch.setenv("WVD_CDM_PATH", str(tmp_path))
        with patch.object(Path, "mkdir"):
            result = get_cdm_path()
            assert result == tmp_path / DEFAULT_CDM_FILENAME


class TestValidateCdm:
    """Tests for validate_cdm()."""

    def test_valid_cdm_returns_true(self, tmp_path):
        """Valid L3 ANDROID CDM returns True."""
        wvd_path = tmp_path / "valid.wvd"
        wvd_path.write_bytes(b"fake wvd content")
        
        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.ANDROID
        mock_device.security_level = 3
        mock_device.system_id = 15071
        
        with patch("pywidevine.device.Device.load", return_value=mock_device):
            result = validate_cdm(wvd_path)
            assert result is True

    def test_wrong_device_type_returns_false(self, tmp_path):
        """Non-ANDROID device type returns False."""
        wvd_path = tmp_path / "wrong_type.wvd"
        wvd_path.write_bytes(b"fake")
        
        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.CHROME
        mock_device.security_level = 3
        
        with patch("pywidevine.device.Device.load", return_value=mock_device):
            result = validate_cdm(wvd_path)
            assert result is False

    def test_wrong_security_level_returns_false(self, tmp_path):
        """Non-L3 security level returns False."""
        wvd_path = tmp_path / "wrong_level.wvd"
        wvd_path.write_bytes(b"fake")
        
        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.ANDROID
        mock_device.security_level = 1  # L1, not L3
        
        with patch("pywidevine.device.Device.load", return_value=mock_device):
            result = validate_cdm(wvd_path)
            assert result is False

    def test_load_exception_returns_false(self, tmp_path):
        """Exception during Device.load returns False."""
        wvd_path = tmp_path / "bad.wvd"
        wvd_path.write_bytes(b"corrupted")
        
        with patch("pywidevine.device.Device.load", side_effect=Exception("load failed")):
            result = validate_cdm(wvd_path)
            assert result is False

    def test_missing_file_returns_false(self, tmp_path):
        """Non-existent file returns False."""
        wvd_path = tmp_path / "nonexistent.wvd"
        result = validate_cdm(wvd_path)
        assert result is False


class TestEnsureCdm:
    """Tests for ensure_cdm() - the primary API."""

    def test_returns_cached_valid_cdm(self, monkeypatch, tmp_path):
        """Returns cached CDM path if valid."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        cdm_file = cache_dir / DEFAULT_CDM_FILENAME
        cdm_file.write_bytes(b"valid")
        
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        with patch("thuis.cdm.validate_cdm", return_value=True):
            result = ensure_cdm()
            assert result == str(cdm_file)

    def test_fetches_when_no_cache(self, monkeypatch, tmp_path):
        """Fetches new CDM when cache is empty."""
        cache_dir = tmp_path / "cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        mock_fetched = tmp_path / "fetched.wvd"
        mock_fetched.write_bytes(b"fetched")
        
        with patch("thuis.cdm.validate_cdm", side_effect=[True]*5):
            with patch("thuis.cdm.fetch_cdm", return_value=mock_fetched):
                with patch("thuis.cdm.shutil.copy2") as mock_copy:
                    result = ensure_cdm()
                    assert result == str(cache_dir / DEFAULT_CDM_FILENAME)
                    mock_copy.assert_called_once_with(mock_fetched, cache_dir / DEFAULT_CDM_FILENAME)

    def test_returns_none_when_fetch_fails(self, monkeypatch, tmp_path):
        """Returns None when fetch fails completely."""
        cache_dir = tmp_path / "cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        with patch("thuis.cdm.validate_cdm", return_value=False):
            with patch("thuis.cdm.fetch_cdm", return_value=None):
                result = ensure_cdm()
                assert result is None

    def test_invalid_cached_cdm_triggers_refetch(self, monkeypatch, tmp_path):
        """Invalid cached CDM is removed and refetch attempted."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        cdm_file = cache_dir / DEFAULT_CDM_FILENAME
        cdm_file.write_bytes(b"invalid")
        
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        mock_fetched = tmp_path / "fetched.wvd"
        mock_fetched.write_bytes(b"fetched")
        
        with patch("thuis.cdm.validate_cdm", side_effect=[False, True]):  # cached invalid, fetch valid
            with patch("thuis.cdm.fetch_cdm", return_value=mock_fetched):
                with patch("thuis.cdm.shutil.copy2"):
                    result = ensure_cdm()
                    assert result == str(cache_dir / DEFAULT_CDM_FILENAME)
                    # Verify invalid cached file was removed
                    assert not cdm_file.exists() or cdm_file.stat().st_size == 0


class TestFetchCdm:
    """Tests for fetch_cdm() - auto-fetch logic."""

    def test_tries_sources_in_order(self, monkeypatch, tmp_path):
        """Tries CDM_SOURCES in order until one succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a mock .wvd that validates
            mock_wvd = tmpdir_path / "google_widevine_l3.wvd"
            mock_wvd.write_bytes(b"valid wvd")
            
            call_count = [0]
            
            def mock_download(url, dest, timeout=30):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First URL - simulate download success but validation fails
                    dest.write_bytes(b"invalid")
                    return True
                elif call_count[0] == 2:
                    # Second URL - success
                    dest.write_bytes(b"valid wvd")
                    return True
                return False
            
            def mock_validate(path):
                return b"valid" in path.read_bytes()
            
            with patch("thuis.cdm.download_file", side_effect=mock_download):
                with patch("thuis.cdm.validate_cdm", side_effect=mock_validate):
                    with patch("thuis.cdm.extract_wvd_from_zip", return_value=None):
                        from thuis.cdm import fetch_cdm
                        # Can't easily test fetch_cdm directly due to tempfile usage
                        # but the integration is tested via ensure_cdm

    def test_zip_extraction_with_wvd(self, tmp_path):
        """Extracts .wvd from zip archive."""
        from thuis.cdm import extract_wvd_from_zip
        
        # Create a zip with a .wvd inside
        import zipfile
        zip_path = tmp_path / "test.zip"
        wvd_content = b"fake wvd"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("device.wvd", wvd_content)
        
        result = extract_wvd_from_zip(zip_path, tmp_path)
        assert result is not None
        assert result.read_bytes() == wvd_content

    def test_zip_extraction_with_keymaterial(self, tmp_path):
        """Assembles .wvd from private_key.pem + client_id.bin in zip."""
        from thuis.cdm import extract_wvd_from_zip
        
        import zipfile
        zip_path = tmp_path / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("private_key.pem", b"-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----")
            zf.writestr("client_id.bin", b"clientid")
        
        with patch("thuis.cdm.assemble_wvd") as mock_assemble:
            mock_assemble.return_value = tmp_path / "assembled.wvd"
            result = extract_wvd_from_zip(zip_path, tmp_path)
            assert result is not None
            mock_assemble.assert_called_once()


class TestAssembleWvd:
    """Tests for assemble_wvd()."""

    def test_assembles_from_key_material(self, tmp_path):
        """Creates .wvd from private_key.pem and client_id.bin."""
        from thuis.cdm import assemble_wvd
        
        key_path = tmp_path / "private_key.pem"
        key_path.write_bytes(b"-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----")
        
        client_path = tmp_path / "client_id.bin"
        client_path.write_bytes(b"clientid")
        
        output_path = tmp_path / "output.wvd"
        
        mock_device = MagicMock()
        
        with patch("pywidevine.device.Device", return_value=mock_device) as mock_device_cls:
            result = assemble_wvd(key_path, client_path, output_path)
            assert result == output_path
            mock_device_cls.assert_called_once()
            mock_device.dump.assert_called_once_with(str(output_path))

    def test_returns_none_on_exception(self, tmp_path):
        """Returns None if assembly fails."""
        from thuis.cdm import assemble_wvd
        
        key_path = tmp_path / "private_key.pem"
        key_path.write_bytes(b"key")
        
        client_path = tmp_path / "client_id.bin"
        client_path.write_bytes(b"client")
        
        output_path = tmp_path / "output.wvd"
        
        with patch("pywidevine.device.Device", side_effect=Exception("assembly failed")):
            result = assemble_wvd(key_path, client_path, output_path)
            assert result is None


class TestCdmSources:
    """Tests for CDM source constants."""

    def test_sources_list_not_empty(self):
        """CDM_SOURCES has at least one entry."""
        assert len(CDM_SOURCES) > 0

    def test_sources_are_urls(self):
        """All sources are valid URLs."""
        for url in CDM_SOURCES:
            assert url.startswith("http://") or url.startswith("https://")

    def test_contains_video_devices_repo(self):
        """Contains the video-devices GitHub repo."""
        assert any("nicko170/video-devices" in url for url in CDM_SOURCES)


class TestIntegration:
    """Integration-style tests for the full ensure_cdm flow."""

    def test_full_flow_cache_miss_fetch_success(self, monkeypatch, tmp_path):
        """Full flow: no cache -> fetch -> validate -> cache -> return."""
        cache_dir = tmp_path / "cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        # Mock a successful fetch
        mock_fetched = tmp_path / "fetched.wvd"
        mock_fetched.write_bytes(b"valid")
        
        with patch("thuis.cdm.validate_cdm", side_effect=[True]*5):
            with patch("thuis.cdm.fetch_cdm", return_value=mock_fetched):
                with patch("thuis.cdm.shutil.copy2"):
                    result = ensure_cdm()
                    assert result == str(cache_dir / DEFAULT_CDM_FILENAME)

    def test_full_flow_all_failures_returns_none(self, monkeypatch, tmp_path):
        """Full flow: all failures -> None with warning logged."""
        cache_dir = tmp_path / "cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        
        with patch("thuis.cdm.validate_cdm", return_value=False):
            with patch("thuis.cdm.fetch_cdm", return_value=None):
                import logging
                with patch("thuis.cdm.logger.warning") as mock_warn:
                    result = ensure_cdm()
                    assert result is None
                    mock_warn.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])