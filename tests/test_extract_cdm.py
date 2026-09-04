"""Tests for extract_cdm.py helper script (C3)."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

import pytest

# Ensure scripts directory is on path for importing extract_cdm
repo_root = Path(__file__).parent.parent
scripts_path = repo_root / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from extract_cdm import (
    print_extraction_guide,
    validate_cache,
    get_cdm_cache_dir,
    find_wvd_files,
    validate_wvd,
    main,
    DEFAULT_CDM_CACHE,
    DEFAULT_CDM_FILENAME,
    PYWIDEVINE_AVAILABLE,
)


class TestPrintExtractionGuide:
    """Tests for print_extraction_guide()."""

    def test_prints_extraction_steps(self, capsys):
        """Running print_extraction_guide outputs guide with key tokens."""
        print_extraction_guide()
        captured = capsys.readouterr()
        output = captured.out

        # Assert key tokens from the guide are present
        assert "wvdumper" in output.lower()
        assert "frida" in output.lower()
        assert "adb" in output.lower()
        assert "libwidevine" in output.lower() or "widevine" in output.lower()
        assert ".wvd" in output
        assert "legal notice" in output.lower() or "legal" in output.lower()


class TestFindWvdFiles:
    """Tests for find_wvd_files()."""

    def test_returns_empty_list_when_dir_does_not_exist(self, tmp_path):
        """Non-existent directory returns empty list."""
        cache_dir = tmp_path / "nonexistent"
        result = find_wvd_files(cache_dir)
        assert result == []

    def test_returns_wvd_files_when_present(self, tmp_path):
        """Returns list of .wvd files in directory."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        (cache_dir / "device.wvd").write_bytes(b"fake")
        (cache_dir / "other.wvd").write_bytes(b"fake2")
        (cache_dir / "not_wvd.txt").write_text("ignore")

        result = find_wvd_files(cache_dir)
        assert len(result) == 2
        assert all(f.suffix == ".wvd" for f in result)


class TestValidateWvd:
    """Tests for validate_wvd()."""

    def test_returns_false_when_pywidevine_unavailable(self, tmp_path, monkeypatch):
        """Returns False with message when pywidevine not installed."""
        # Simulate pywidevine not being available
        import extract_cdm
        monkeypatch.setattr(extract_cdm, "PYWIDEVINE_AVAILABLE", False)

        wvd_path = tmp_path / "test.wvd"
        wvd_path.write_bytes(b"fake")

        is_valid, details = validate_wvd(wvd_path)
        assert is_valid is False
        assert "pywidevine not installed" in details

    def test_returns_true_for_valid_l3_android(self, tmp_path):
        """Returns True for valid L3 ANDROID device."""
        if not PYWIDEVINE_AVAILABLE:
            pytest.skip("pywidevine not installed")

        wvd_path = tmp_path / "valid.wvd"
        wvd_path.write_bytes(b"fake")

        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.ANDROID
        mock_device.security_level = 3
        mock_device.system_id = 15071
        mock_device.client_id = b"x" * 32

        with patch("pywidevine.device.Device.load", return_value=mock_device):
            is_valid, details = validate_wvd(wvd_path)
            assert is_valid is True
            assert "Valid L3 ANDROID CDM" in details
            assert "ANDROID" in details
            assert "3" in details

    def test_returns_false_for_wrong_device_type(self, tmp_path):
        """Returns False for non-ANDROID device type."""
        if not PYWIDEVINE_AVAILABLE:
            pytest.skip("pywidevine not installed")

        wvd_path = tmp_path / "wrong.wvd"
        wvd_path.write_bytes(b"fake")

        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.CHROME
        mock_device.security_level = 3

        with patch("pywidevine.device.Device.load", return_value=mock_device):
            is_valid, details = validate_wvd(wvd_path)
            assert is_valid is False
            assert "expected ANDROID" in details

    def test_returns_false_for_wrong_security_level(self, tmp_path):
        """Returns False for non-L3 security level."""
        if not PYWIDEVINE_AVAILABLE:
            pytest.skip("pywidevine not installed")

        wvd_path = tmp_path / "wrong_level.wvd"
        wvd_path.write_bytes(b"fake")

        from pywidevine.device import DeviceTypes
        mock_device = MagicMock()
        mock_device.type = DeviceTypes.ANDROID
        mock_device.security_level = 1  # L1

        with patch("pywidevine.device.Device.load", return_value=mock_device):
            is_valid, details = validate_wvd(wvd_path)
            assert is_valid is False
            assert "expected 3" in details

    def test_returns_false_on_load_exception(self, tmp_path):
        """Returns False when Device.load raises exception."""
        if not PYWIDEVINE_AVAILABLE:
            pytest.skip("pywidevine not installed")

        wvd_path = tmp_path / "bad.wvd"
        wvd_path.write_bytes(b"corrupted")

        with patch("pywidevine.device.Device.load", side_effect=Exception("load failed")):
            is_valid, details = validate_wvd(wvd_path)
            assert is_valid is False
            assert "Validation error" in details


class TestValidateCache:
    """Tests for validate_cache()."""

    def test_returns_1_when_no_wvd_files(self, tmp_path, capsys):
        """Empty cache returns exit code 1."""
        cache_dir = tmp_path / "empty_cdm"
        cache_dir.mkdir()

        exit_code, valid_wvd = validate_cache(cache_dir, verbose=True)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert valid_wvd is None
        assert "No .wvd files found" in captured.out

    def test_returns_0_when_valid_wvd_found(self, tmp_path, capsys, monkeypatch):
        """Valid .wvd in cache returns exit code 0."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        wvd_file = cache_dir / "device.wvd"
        wvd_file.write_bytes(b"valid")

        # Mock validate_wvd to return valid
        monkeypatch.setattr("extract_cdm.validate_wvd", lambda p: (True, "Valid L3 ANDROID CDM"))

        exit_code, valid_wvd = validate_cache(cache_dir, verbose=True)
        captured = capsys.readouterr()

        assert exit_code == 0
        assert valid_wvd == wvd_file
        assert "VALID" in captured.out or "Valid CDM found" in captured.out

    def test_returns_1_when_wvd_invalid(self, tmp_path, capsys, monkeypatch):
        """Invalid .wvd returns exit code 1."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        wvd_file = cache_dir / "invalid.wvd"
        wvd_file.write_bytes(b"invalid")

        # Mock validate_wvd to return invalid
        monkeypatch.setattr("extract_cdm.validate_wvd", lambda p: (False, "Validation error: corrupt"))

        exit_code, valid_wvd = validate_cache(cache_dir, verbose=True)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert valid_wvd is None
        assert "INVALID" in captured.out or "No valid L3" in captured.out


class TestMain:
    """Integration tests for main()."""

    def test_guide_flag_prints_guide_and_exits_0(self, capsys):
        """--guide flag prints extraction guide and exits 0."""
        with patch.object(sys, "argv", ["extract_cdm.py", "--guide"]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "wvdumper" in captured.out.lower()
        assert "LEGAL NOTICE" in captured.out

    def test_valid_cdm_returns_0(self, tmp_path, capsys, monkeypatch):
        """Valid CDM in cache returns exit code 0."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        wvd_file = cache_dir / DEFAULT_CDM_FILENAME
        wvd_file.write_bytes(b"valid")

        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        monkeypatch.setattr("extract_cdm.validate_wvd", lambda p: (True, "Valid L3 ANDROID CDM"))

        with patch.object(sys, "argv", ["extract_cdm.py"]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Valid CDM found" in captured.out

    def test_no_cdm_returns_1_and_prints_guide(self, tmp_path, capsys, monkeypatch):
        """Empty cache returns exit code 1 and prints guide."""
        cache_dir = tmp_path / "empty_cdm"
        cache_dir.mkdir()

        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))

        with patch.object(sys, "argv", ["extract_cdm.py"]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No .wvd files found" in captured.out
        assert "wvdumper" in captured.out.lower()  # Guide printed

    def test_invalid_cdm_returns_1_and_prints_guide(self, tmp_path, capsys, monkeypatch):
        """Invalid CDM returns exit code 1 and prints guide."""
        cache_dir = tmp_path / "cdm"
        cache_dir.mkdir()
        wvd_file = cache_dir / DEFAULT_CDM_FILENAME
        wvd_file.write_bytes(b"invalid")

        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))
        monkeypatch.setattr("extract_cdm.validate_wvd", lambda p: (False, "Validation error"))

        with patch.object(sys, "argv", ["extract_cdm.py"]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "INVALID" in captured.out or "No valid L3" in captured.out
        assert "wvdumper" in captured.out.lower()  # Guide printed

    def test_quiet_flag_suppresses_output(self, tmp_path, capsys, monkeypatch):
        """-q flag suppresses verbose output but still returns exit code."""
        cache_dir = tmp_path / "empty_cdm"
        cache_dir.mkdir()

        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir))

        with patch.object(sys, "argv", ["extract_cdm.py", "-q"]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        # In quiet mode, no output unless --guide
        assert captured.out == ""

    def test_cache_dir_override(self, tmp_path, capsys, monkeypatch):
        """--cache-dir overrides WVD_CDM_PATH."""
        cache_dir1 = tmp_path / "cdm1"
        cache_dir1.mkdir()
        (cache_dir1 / DEFAULT_CDM_FILENAME).write_bytes(b"invalid")

        cache_dir2 = tmp_path / "cdm2"
        cache_dir2.mkdir()
        (cache_dir2 / DEFAULT_CDM_FILENAME).write_bytes(b"valid")

        monkeypatch.setenv("WVD_CDM_PATH", str(cache_dir1))
        monkeypatch.setattr("extract_cdm.validate_wvd", lambda p: (True, "Valid L3 ANDROID CDM") if "cdm2" in str(p) else (False, "Invalid"))

        with patch.object(sys, "argv", ["extract_cdm.py", "--cache-dir", str(cache_dir2)]):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Valid CDM found" in captured.out


class TestGetCdmCacheDir:
    """Tests for get_cdm_cache_dir()."""

    def test_default_cache_dir(self, monkeypatch):
        """Default cache dir when WVD_CDM_PATH not set."""
        monkeypatch.delenv("WVD_CDM_PATH", raising=False)
        result = get_cdm_cache_dir()
        assert result == DEFAULT_CDM_CACHE

    def test_env_var_override(self, monkeypatch, tmp_path):
        """WVD_CDM_PATH env var is respected."""
        custom_path = tmp_path / "custom_cdm"
        monkeypatch.setenv("WVD_CDM_PATH", str(custom_path))
        result = get_cdm_cache_dir()
        assert result == custom_path.resolve()

    def test_tilde_expansion(self, monkeypatch):
        """Tilde in WVD_CDM_PATH is expanded."""
        monkeypatch.setenv("WVD_CDM_PATH", "~/my_cdm")
        with patch.object(Path, "mkdir"):
            result = get_cdm_cache_dir()
            assert str(result).startswith(str(Path.home()))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])