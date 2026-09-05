"""
Unit tests for the doctor command (src/thuis/doctor.py).

Tests cover:
- TestDoctorChecks: All health check methods (pass/fail scenarios)
- TestDoctorFormat: Report formatting with ANSI colors and fix hints
- TestDoctorAutoFix: Auto-fix functionality for fixable checks
"""

import os
import sys
import subprocess
import builtins
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Ensure src is on path (handled by conftest.py)
from thuis.doctor import Doctor, CheckResult, Colors, run_doctor


# =============================================================================
# TestDoctorChecks - Unit tests for each check method
# =============================================================================


class TestDoctorChecks:
    """Tests for individual health check methods in Doctor class."""

    @pytest.fixture
    def doctor(self):
        """Create a Doctor instance for testing."""
        return Doctor(verbose=False)

    # -------------------------------------------------------------------------
    # check_python_deps tests
    # -------------------------------------------------------------------------

    def test_check_python_deps_all_present(self, doctor, monkeypatch):
        """Test check_python_deps passes when all required modules are importable."""
        # Mock all required modules as importable
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name in ("yt_dlp", "pywidevine", "pymp4", "dotenv"):
                return MagicMock()
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = doctor.check_python_deps()

        assert result.name == "Python Dependencies"
        assert result.passed is True
        assert "All required packages available" in result.message
        assert result.fixable is False

    def test_check_python_deps_missing(self, doctor, monkeypatch):
        """Test check_python_deps fails when a required module is missing."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pywidevine":
                raise ImportError("No module named 'pywidevine'")
            if name in ("yt_dlp", "pymp4", "dotenv"):
                return MagicMock()
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = doctor.check_python_deps()

        assert result.name == "Python Dependencies"
        assert result.passed is False
        assert "pywidevine" in result.message.lower()
        assert result.fixable is True
        assert "uv pip install" in result.fix_hint or "pip install" in result.fix_hint

    # -------------------------------------------------------------------------
    # check_decryption_engines tests
    # -------------------------------------------------------------------------

    def test_check_decryption_engines_found(self, doctor, monkeypatch):
        """Test check_decryption_engines passes when at least one engine is found."""
        # Mock find_binary to return a path for mp4decrypt
        mock_find_binary = MagicMock(side_effect=lambda name: "/usr/bin/mp4decrypt" if name == "mp4decrypt" else None)
        monkeypatch.setattr("thuis.doctor.find_binary", mock_find_binary)

        result = doctor.check_decryption_engines()

        assert result.name == "Decryption Engines"
        assert result.passed is True
        assert "mp4decrypt" in result.message
        assert result.fixable is False

    def test_check_decryption_engines_missing(self, doctor, monkeypatch):
        """Test check_decryption_engines fails when no engines are found."""
        # Mock find_binary to return None for all engines
        mock_find_binary = MagicMock(return_value=None)
        monkeypatch.setattr("thuis.doctor.find_binary", mock_find_binary)

        result = doctor.check_decryption_engines()

        assert result.name == "Decryption Engines"
        assert result.passed is False
        assert "No engine found" in result.message
        assert result.fixable is True
        assert "mp4decrypt" in result.fix_hint or "shaka-packager" in result.fix_hint or "ffmpeg" in result.fix_hint

    # -------------------------------------------------------------------------
    # check_n_m3u8dl_re tests
    # -------------------------------------------------------------------------

    def test_check_n_m3u8dl_re_found(self, doctor, monkeypatch):
        """Test check_n_m3u8dl_re passes when binary is found in PATH."""
        mock_find_binary = MagicMock(return_value="/usr/local/bin/N_m3u8DL-RE")
        monkeypatch.setattr("thuis.doctor.find_binary", mock_find_binary)

        result = doctor.check_n_m3u8dl_re()

        assert result.name == "N_m3u8DL-RE"
        assert result.passed is True
        assert "/usr/local/bin/N_m3u8DL-RE" in result.message
        assert result.fixable is False

    def test_check_n_m3u8dl_re_missing(self, doctor, monkeypatch):
        """Test check_n_m3u8dl_re fails when binary is not in PATH."""
        mock_find_binary = MagicMock(return_value=None)
        monkeypatch.setattr("thuis.doctor.find_binary", mock_find_binary)

        result = doctor.check_n_m3u8dl_re()

        assert result.name == "N_m3u8DL-RE"
        assert result.passed is False
        assert "Not found in PATH" in result.message
        assert result.fixable is True
        assert "GitHub releases" in result.fix_hint or "N_m3u8DL-RE/releases" in result.fix_hint

    # -------------------------------------------------------------------------
    # check_cdm tests
    # -------------------------------------------------------------------------

    def test_check_cdm_not_found(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm fails when no .wvd file exists."""
        # Mock get_cdm_cache_dir to return a temp directory without .wvd
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        result = doctor.check_cdm()

        assert result.name == "Widevine CDM"
        assert result.passed is False
        assert "Not found" in result.message
        assert result.fixable is False  # CDM extraction cannot be auto-fixed
        assert "extract_cdm.py" in result.fix_hint

    def test_check_cdm_wrong_type(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm fails when CDM has wrong device type."""
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        cdm_path = mock_cache_dir / "widevine_l3_android.wvd"
        cdm_path.write_text("fake cdm content")

        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        # Mock pywidevine.Device.load to return a device with wrong type
        mock_device = MagicMock()
        mock_device.type = "CHROME"  # Wrong type
        mock_device.security_level = 3

        mock_pywidevine = MagicMock()
        mock_pywidevine.device.Device.load.return_value = mock_device
        mock_pywidevine.device.DeviceTypes.ANDROID = "ANDROID"

        monkeypatch.setitem(sys.modules, "pywidevine", mock_pywidevine)
        monkeypatch.setitem(sys.modules, "pywidevine.device", mock_pywidevine.device)

        result = doctor.check_cdm()

        assert result.name == "Widevine CDM"
        assert result.passed is False
        assert "Wrong device type" in result.message
        assert result.fixable is False

    def test_check_cdm_wrong_security_level(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm fails when CDM has wrong security level."""
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        cdm_path = mock_cache_dir / "widevine_l3_android.wvd"
        cdm_path.write_text("fake cdm content")

        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        mock_device = MagicMock()
        mock_device.type = "ANDROID"
        mock_device.security_level = 1  # Wrong level (should be 3/L3)

        mock_pywidevine = MagicMock()
        mock_pywidevine.device.Device.load.return_value = mock_device
        mock_pywidevine.device.DeviceTypes.ANDROID = "ANDROID"

        monkeypatch.setitem(sys.modules, "pywidevine", mock_pywidevine)
        monkeypatch.setitem(sys.modules, "pywidevine.device", mock_pywidevine.device)

        result = doctor.check_cdm()

        assert result.name == "Widevine CDM"
        assert result.passed is False
        assert "Wrong security level" in result.message
        assert result.fixable is False

    def test_check_cdm_valid(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm passes when valid L3 ANDROID CDM is found."""
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        cdm_path = mock_cache_dir / "widevine_l3_android.wvd"
        cdm_path.write_text("fake cdm content")

        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        mock_device = MagicMock()
        mock_device.type = "ANDROID"
        mock_device.security_level = 3

        mock_pywidevine = MagicMock()
        mock_pywidevine.device.Device.load.return_value = mock_device
        mock_pywidevine.device.DeviceTypes.ANDROID = "ANDROID"

        monkeypatch.setitem(sys.modules, "pywidevine", mock_pywidevine)
        monkeypatch.setitem(sys.modules, "pywidevine.device", mock_pywidevine.device)

        result = doctor.check_cdm()

        assert result.name == "Widevine CDM"
        assert result.passed is True
        assert "Valid L3 ANDROID CDM" in result.message
        assert result.fixable is False

    def test_check_cdm_validation_exception(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm fails gracefully when pywidevine validation raises exception."""
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        cdm_path = mock_cache_dir / "widevine_l3_android.wvd"
        cdm_path.write_text("fake cdm content")

        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        mock_pywidevine = MagicMock()
        mock_pywidevine.device.Device.load.side_effect = Exception("Invalid CDM format")
        mock_pywidevine.device.DeviceTypes.ANDROID = "ANDROID"

        monkeypatch.setitem(sys.modules, "pywidevine", mock_pywidevine)
        monkeypatch.setitem(sys.modules, "pywidevine.device", mock_pywidevine.device)

        result = doctor.check_cdm()

        assert result.name == "Widevine CDM"
        assert result.passed is False
        assert "Validation failed" in result.message
        assert result.fixable is False

    def test_check_cdm_handles_pywidevine_not_installed(self, doctor, monkeypatch, tmp_path):
        """Test check_cdm handles pywidevine not being installed."""
        mock_cache_dir = tmp_path / "wvd"
        mock_cache_dir.mkdir()
        cdm_path = mock_cache_dir / "widevine_l3_android.wvd"
        cdm_path.write_text("fake")

        monkeypatch.setattr("thuis.doctor.get_cdm_cache_dir", lambda: mock_cache_dir)

        # Remove pywidevine from sys.modules to simulate not installed
        monkeypatch.delitem(sys.modules, "pywidevine", raising=False)
        monkeypatch.delitem(sys.modules, "pywidevine.device", raising=False)

        # Mock import to raise ImportError for pywidevine
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("pywidevine"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = doctor.check_cdm()

        assert result.passed is False
        assert "Validation failed" in result.message

    # -------------------------------------------------------------------------
    # check_env_vars tests
    # -------------------------------------------------------------------------

    def test_check_env_vars_enabled(self, doctor, monkeypatch):
        """Test check_env_vars passes when DECRYPT_DRM=yes and vars configured."""
        monkeypatch.setenv("VRT_EMAIL", "test@example.com")
        monkeypatch.setenv("VRT_PASSWORD", "secret")
        monkeypatch.setenv("DECRYPT_DRM", "yes")
        monkeypatch.setenv("WVD_CDM_PATH", "/valid/path.wvd")

        # Mock Path.exists for WVD_CDM_PATH
        monkeypatch.setattr(Path, "exists", lambda self: True)

        result = doctor.check_env_vars()

        assert result.name == "Environment Variables"
        assert result.passed is True
        assert "All DRM env vars configured" in result.message

    def test_check_env_vars_disabled(self, doctor, monkeypatch):
        """Test check_env_vars fails when DECRYPT_DRM=no."""
        monkeypatch.setenv("DECRYPT_DRM", "no")
        monkeypatch.delenv("VRT_EMAIL", raising=False)
        monkeypatch.delenv("VRT_PASSWORD", raising=False)

        result = doctor.check_env_vars()

        assert result.name == "Environment Variables"
        assert result.passed is False
        assert "DECRYPT_DRM=no" in result.message
        assert result.fixable is True

    def test_check_env_vars_missing_vrt_creds(self, doctor, monkeypatch):
        """Test check_env_vars warns when VRT_EMAIL/VRT_PASSWORD not set."""
        monkeypatch.setenv("DECRYPT_DRM", "yes")
        monkeypatch.delenv("VRT_EMAIL", raising=False)
        monkeypatch.delenv("VRT_PASSWORD", raising=False)

        result = doctor.check_env_vars()

        assert result.name == "Environment Variables"
        assert result.passed is False
        assert "VRT_EMAIL/VRT_PASSWORD not set" in result.message
        assert result.fixable is True

    def test_check_env_vars_invalid_wvd_path(self, doctor, monkeypatch):
        """Test check_env_vars fails when WVD_CDM_PATH points to non-existent file."""
        monkeypatch.setenv("DECRYPT_DRM", "yes")
        monkeypatch.setenv("VRT_EMAIL", "test@example.com")
        monkeypatch.setenv("VRT_PASSWORD", "secret")
        monkeypatch.setenv("WVD_CDM_PATH", "/nonexistent/path.wvd")

        monkeypatch.setattr(Path, "exists", lambda self: False)

        result = doctor.check_env_vars()

        assert result.name == "Environment Variables"
        assert result.passed is False
        assert "non-existent file" in result.message
        assert result.fixable is True

    # -------------------------------------------------------------------------
    # check_env_file tests
    # -------------------------------------------------------------------------

    def test_check_env_file_exists(self, doctor, monkeypatch, tmp_path):
        """Test check_env_file passes when .env exists with all expected keys."""
        env_content = "VRT_EMAIL=test@example.com\nVRT_PASSWORD=secret\nDECRYPT_DRM=yes\nWVD_CDM_PATH=/path.wvd\n"
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)

        # Change to tmp_path for the test
        monkeypatch.chdir(tmp_path)

        result = doctor.check_env_file()

        assert result.name == ".env File"
        assert result.passed is True
        assert "All expected keys present" in result.message

    def test_check_env_file_missing(self, doctor, monkeypatch, tmp_path):
        """Test check_env_file fails when no .env file exists."""
        monkeypatch.chdir(tmp_path)
        # Ensure no .env exists
        env_path = tmp_path / ".env"
        if env_path.exists():
            env_path.unlink()

        result = doctor.check_env_file()

        assert result.name == ".env File"
        assert result.passed is False
        assert "No .env file found" in result.message
        assert result.fixable is True
        assert ".env.template" in result.fix_hint

    def test_check_env_file_missing_keys(self, doctor, monkeypatch, tmp_path):
        """Test check_env_file fails when .env exists but missing expected keys."""
        env_content = "VRT_EMAIL=test@example.com\n# Only email, missing others\n"
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)

        monkeypatch.chdir(tmp_path)

        result = doctor.check_env_file()

        assert result.name == ".env File"
        assert result.passed is False
        assert "Missing keys" in result.message
        assert "VRT_PASSWORD" in result.message
        assert "DECRYPT_DRM" in result.message
        assert "WVD_CDM_PATH" in result.message
        assert result.fixable is True

    def test_check_env_file_read_error(self, doctor, monkeypatch, tmp_path):
        """Test check_env_file fails gracefully when .env cannot be read."""
        env_path = tmp_path / ".env"
        env_path.write_text("VRT_EMAIL=test\n")

        monkeypatch.chdir(tmp_path)

        # Mock read_text to raise exception
        def mock_read_text(self):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        result = doctor.check_env_file()

        assert result.name == ".env File"
        assert result.passed is False
        assert "Failed to read .env" in result.message
        assert result.fixable is False


# =============================================================================
# TestDoctorFormat - Unit tests for format_report
# =============================================================================


class TestDoctorFormat:
    """Tests for the format_report method."""

    @pytest.fixture
    def doctor(self):
        """Create a Doctor instance for testing."""
        return Doctor(verbose=False)

    def test_format_report_shows_pass_icon(self, doctor):
        """Test format_report shows ✓ PASS for passing checks."""
        results = [
            CheckResult(name="Test Check", passed=True, message="All good"),
        ]

        report = doctor.format_report(results)

        assert "✓ PASS" in report
        assert "Test Check" in report
        assert "All good" in report
        assert Colors.GREEN in report
        assert Colors.RESET in report

    def test_format_report_shows_fail_icon(self, doctor):
        """Test format_report shows ✗ FAIL for failing checks."""
        results = [
            CheckResult(name="Test Check", passed=False, message="Something wrong"),
        ]

        report = doctor.format_report(results)

        assert "✗ FAIL" in report
        assert "Test Check" in report
        assert "Something wrong" in report
        assert Colors.RED in report

    def test_format_report_shows_fix_hint(self, doctor):
        """Test format_report shows fix hint for failed fixable checks."""
        results = [
            CheckResult(
                name="Test Check",
                passed=False,
                message="Something wrong",
                fixable=True,
                fix_hint="Run: fix-command"
            ),
        ]

        report = doctor.format_report(results)

        assert "✗ FAIL" in report
        assert "(fixable)" in report
        assert "→ Fix: Run: fix-command" in report
        assert Colors.BLUE in report
        assert Colors.YELLOW in report

    def test_format_report_no_fix_hint_for_non_fixable(self, doctor):
        """Test format_report shows fix hint for any failed check with fix_hint."""
        results = [
            CheckResult(
                name="Test Check",
                passed=False,
                message="Something wrong",
                fixable=False,
                fix_hint="This should appear since fix_hint is set"
            ),
        ]

        report = doctor.format_report(results)

        assert "✗ FAIL" in report
        assert "(fixable)" not in report  # No (fixable) label since fixable=False
        assert "→ Fix:" in report  # But fix hint is still shown

    def test_format_report_summary_all_passed(self, doctor):
        """Test format_report summary shows all checks passed."""
        results = [
            CheckResult(name="Check 1", passed=True, message="OK"),
            CheckResult(name="Check 2", passed=True, message="OK"),
        ]

        report = doctor.format_report(results)

        assert "All checks passed!" in report
        assert "System ready for DRM decryption" in report
        assert Colors.GREEN in report
        assert Colors.BOLD in report

    def test_format_report_summary_some_failed(self, doctor):
        """Test format_report summary shows failed count and fixable count."""
        results = [
            CheckResult(name="Check 1", passed=True, message="OK"),
            CheckResult(name="Check 2", passed=False, message="Failed", fixable=True, fix_hint="Fix it"),
            CheckResult(name="Check 3", passed=False, message="Failed", fixable=False),
        ]

        report = doctor.format_report(results)

        assert "2/3 checks failed" in report
        assert "1 can be auto-fixed" in report
        assert Colors.RED in report
        assert Colors.YELLOW in report

    def test_format_report_handles_empty_results(self, doctor):
        """Test format_report handles empty results list."""
        report = doctor.format_report([])

        assert "=== thuis Doctor Report ===" in report
        assert "0/0 checks failed" in report or "All checks passed" in report


# =============================================================================
# TestDoctorAutoFix - Unit tests for auto_fix methods
# =============================================================================


class TestDoctorAutoFix:
    """Tests for auto-fix functionality."""

    @pytest.fixture
    def doctor(self):
        """Create a Doctor instance for testing."""
        return Doctor(verbose=False)

    # -------------------------------------------------------------------------
    # _fix_python_deps tests
    # -------------------------------------------------------------------------

    def test_fix_python_deps_no_requirements(self, doctor, monkeypatch, tmp_path):
        """Test _fix_python_deps fails when requirements.txt not found."""
        monkeypatch.chdir(tmp_path)
        # No requirements.txt in tmp_path

        result = doctor._fix_python_deps()

        assert result is False

    def test_fix_python_deps_uv_success(self, doctor, monkeypatch, tmp_path):
        """Test _fix_python_deps succeeds with uv."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("yt-dlp\npywidevine\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/uv" if x == "uv" else None)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        mock_run = MagicMock(return_value=mock_result)
        monkeypatch.setattr("subprocess.run", mock_run)

        result = doctor._fix_python_deps()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert "pip" in args
        assert "install" in args

    def test_fix_python_deps_uv_fails_fallback_pip(self, doctor, monkeypatch, tmp_path):
        """Test _fix_python_deps falls back to pip when uv fails."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("yt-dlp\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/uv" if x == "uv" else None)

        # First call (uv) fails, second call (pip) succeeds
        mock_run = MagicMock()
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="uv error"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        monkeypatch.setattr("subprocess.run", mock_run)

        result = doctor._fix_python_deps()

        assert result is True
        assert mock_run.call_count == 2
        # Second call should be pip
        pip_call = mock_run.call_args_list[1][0][0]
        assert sys.executable in pip_call[0]
        assert "pip" in pip_call

    # -------------------------------------------------------------------------
    # _fix_decrypt_drm tests
    # -------------------------------------------------------------------------

    def test_auto_fix_creates_env_file(self, doctor, monkeypatch, tmp_path):
        """Test _fix_decrypt_drm creates .env with DECRYPT_DRM=yes when no .env exists."""
        monkeypatch.chdir(tmp_path)
        # No .env.template, no .env

        result = doctor._fix_decrypt_drm()

        assert result is True
        env_path = tmp_path / ".env"
        assert env_path.exists()
        content = env_path.read_text()
        assert "DECRYPT_DRM=yes" in content

    def test_auto_fix_updates_env_file(self, doctor, monkeypatch, tmp_path):
        """Test _fix_decrypt_drm updates existing .env file."""
        env_content = "VRT_EMAIL=test\nDECRYPT_DRM=no\n"
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)

        monkeypatch.chdir(tmp_path)

        result = doctor._fix_decrypt_drm()

        assert result is True
        content = env_path.read_text()
        assert "DECRYPT_DRM=yes" in content
        assert "DECRYPT_DRM=no" not in content

    def test_auto_fix_preserves_other_env_vars(self, doctor, monkeypatch, tmp_path):
        """Test _fix_decrypt_drm preserves other variables in .env."""
        env_content = "VRT_EMAIL=test@example.com\nVRT_PASSWORD=secret\nDECRYPT_DRM=no\nWVD_CDM_PATH=/path.wvd\n"
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)

        monkeypatch.chdir(tmp_path)

        result = doctor._fix_decrypt_drm()

        assert result is True
        content = env_path.read_text()
        assert "VRT_EMAIL=test@example.com" in content
        assert "VRT_PASSWORD=secret" in content
        assert "DECRYPT_DRM=yes" in content
        assert "WVD_CDM_PATH=/path.wvd" in content

    def test_auto_fix_uses_template_when_exists(self, doctor, monkeypatch, tmp_path):
        """Test _fix_decrypt_drm uses .env.template when creating new .env."""
        template_content = "VRT_EMAIL=\nVRT_PASSWORD=\nDECRYPT_DRM=no\nWVD_CDM_PATH=\n"
        template_path = tmp_path / ".env.template"
        template_path.write_text(template_content)

        monkeypatch.chdir(tmp_path)

        result = doctor._fix_decrypt_drm()

        assert result is True
        env_path = tmp_path / ".env"
        assert env_path.exists()
        content = env_path.read_text()
        assert "DECRYPT_DRM=yes" in content
        assert "VRT_EMAIL=" in content
        assert "VRT_PASSWORD=" in content

    # -------------------------------------------------------------------------
    # _fix_env_file tests
    # -------------------------------------------------------------------------

    def test_fix_env_file_creates_from_template(self, doctor, monkeypatch, tmp_path):
        """Test _fix_env_file creates .env from .env.template."""
        template_content = "VRT_EMAIL=\nVRT_PASSWORD=\nDECRYPT_DRM=no\nWVD_CDM_PATH=\n"
        template_path = tmp_path / ".env.template"
        template_path.write_text(template_content)

        monkeypatch.chdir(tmp_path)

        result = doctor._fix_env_file()

        assert result is True
        env_path = tmp_path / ".env"
        assert env_path.exists()
        content = env_path.read_text()
        assert content == template_content

    def test_fix_env_file_creates_minimal_when_no_template(self, doctor, monkeypatch, tmp_path):
        """Test _fix_env_file creates minimal .env when no template exists."""
        monkeypatch.chdir(tmp_path)

        result = doctor._fix_env_file()

        assert result is True
        env_path = tmp_path / ".env"
        assert env_path.exists()
        content = env_path.read_text()
        assert "VRT_EMAIL=" in content
        assert "VRT_PASSWORD=" in content
        assert "DECRYPT_DRM=yes" in content
        assert "WVD_CDM_PATH=" in content

    def test_fix_env_file_noop_when_exists(self, doctor, monkeypatch, tmp_path):
        """Test _fix_env_file returns True without changes when .env already exists."""
        env_content = "VRT_EMAIL=existing\n"
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)

        monkeypatch.chdir(tmp_path)

        result = doctor._fix_env_file()

        assert result is True
        content = env_path.read_text()
        assert content == env_content  # Unchanged

    # -------------------------------------------------------------------------
    # _fix_decryption_engine tests
    # -------------------------------------------------------------------------

    def test_fix_decryption_engine_no_pkg_mgr(self, doctor, monkeypatch):
        """Test _fix_decryption_engine fails when no package manager found."""
        monkeypatch.setattr("shutil.which", lambda x: None)

        result = doctor._fix_decryption_engine()

        assert result is False

    def test_fix_decryption_engine_apt_success(self, doctor, monkeypatch):
        """Test _fix_decryption_engine succeeds with apt."""
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/apt" if x == "apt" else None)

        mock_run = MagicMock()
        mock_run.returncode = 0
        monkeypatch.setattr("subprocess.run", mock_run)

        # Mock _run_with_sudo to return True
        monkeypatch.setattr(doctor, "_run_with_sudo", lambda cmd: True)

        result = doctor._fix_decryption_engine()

        assert result is True

    # -------------------------------------------------------------------------
    # _fix_n_m3u8dl_re tests
    # -------------------------------------------------------------------------

    def test_fix_n_m3u8dl_re_always_false(self, doctor):
        """Test _fix_n_m3u8dl_re always returns False (manual download required)."""
        result = doctor._fix_n_m3u8dl_re()
        assert result is False

    # -------------------------------------------------------------------------
    # auto_fix integration tests
    # -------------------------------------------------------------------------

    def test_auto_fix_fixes_multiple_checks(self, doctor, monkeypatch, tmp_path):
        """Test auto_fix processes multiple fixable failed checks."""
        monkeypatch.chdir(tmp_path)

        results = [
            CheckResult(
                name=".env File",
                passed=False,
                message="No .env file found",
                fixable=True,
                fix_hint="Create .env"
            ),
            CheckResult(
                name=".env File",
                passed=False,
                message="No .env file found",
                fixable=True,
                fix_hint="Create .env"
            ),
        ]

        monkeypatch.setattr(doctor, "_fix_env_file", lambda: True)

        fixed, failed = doctor.auto_fix(results)

        assert fixed == 2
        assert failed == 0

    def test_auto_fix_skips_passed_checks(self, doctor, monkeypatch):
        """Test auto_fix skips checks that already passed."""
        results = [
            CheckResult(name="Python Dependencies", passed=True, message="OK"),
            CheckResult(name=".env File", passed=False, message="Failed", fixable=True, fix_hint="Fix"),
        ]

        monkeypatch.setattr(doctor, "_fix_env_file", lambda: True)

        fixed, failed = doctor.auto_fix(results)

        assert fixed == 1
        assert failed == 0

    def test_auto_fix_skips_non_fixable(self, doctor):
        """Test auto_fix skips non-fixable failed checks."""
        results = [
            CheckResult(name="Widevine CDM", passed=False, message="Failed", fixable=False),
        ]

        fixed, failed = doctor.auto_fix(results)

        assert fixed == 0
        assert failed == 0  # Non-fixable checks are skipped entirely

    def test_auto_fix_handles_fix_method_exception(self, doctor, monkeypatch):
        """Test auto_fix handles exceptions in fix methods gracefully."""
        results = [
            CheckResult(name="N_m3u8DL-RE", passed=False, message="Failed", fixable=True, fix_hint="Fix"),
        ]

        def failing_fix():
            raise RuntimeError("Fix failed")

        monkeypatch.setattr(doctor, "_fix_n_m3u8dl_re", failing_fix)

        fixed, failed = doctor.auto_fix(results)

        assert fixed == 0
        assert failed == 1


# =============================================================================
# TestRunDoctor - Integration tests for run_doctor entry point
# =============================================================================


class TestRunDoctor:
    """Integration tests for the run_doctor main entry point."""

    def test_run_doctor_all_passed(self, monkeypatch, tmp_path, capsys):
        """Test run_doctor returns 0 when all checks pass."""
        # Mock all checks to pass
        mock_doctor = MagicMock()
        mock_results = [
            CheckResult(name="Python Dependencies", passed=True, message="OK"),
            CheckResult(name="Decryption Engines", passed=True, message="OK"),
            CheckResult(name="N_m3u8DL-RE", passed=True, message="OK"),
            CheckResult(name="Widevine CDM", passed=True, message="OK"),
            CheckResult(name="Environment Variables", passed=True, message="OK"),
            CheckResult(name=".env File", passed=True, message="OK"),
        ]
        mock_doctor.run_all_checks.return_value = mock_results
        mock_doctor.format_report.return_value = "All good"

        monkeypatch.setattr("thuis.doctor.Doctor", lambda verbose: mock_doctor)

        exit_code = run_doctor(fix_mode=False, verbose=False)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "All good" in captured.out

    def test_run_doctor_some_failed_no_fix(self, monkeypatch, tmp_path, capsys):
        """Test run_doctor returns 1 when checks fail and fix_mode=False."""
        mock_doctor = MagicMock()
        mock_results = [
            CheckResult(name="Python Dependencies", passed=True, message="OK"),
            CheckResult(name="Decryption Engines", passed=False, message="Missing", fixable=True, fix_hint="Install"),
        ]
        mock_doctor.run_all_checks.return_value = mock_results
        mock_doctor.format_report.return_value = "Some failed"

        monkeypatch.setattr("thuis.doctor.Doctor", lambda verbose: mock_doctor)

        exit_code = run_doctor(fix_mode=False, verbose=False)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Some failed" in captured.out

    def test_run_doctor_fix_mode_success(self, monkeypatch, tmp_path, capsys):
        """Test run_doctor with fix_mode=True returns 0 after successful fix."""
        mock_doctor = MagicMock()

        # First run: some failed
        failed_results = [
            CheckResult(name="Python Dependencies", passed=True, message="OK"),
            CheckResult(name="Decryption Engines", passed=False, message="Missing", fixable=True, fix_hint="Install"),
        ]
        # Second run (after fix): all pass
        fixed_results = [
            CheckResult(name="Python Dependencies", passed=True, message="OK"),
            CheckResult(name="Decryption Engines", passed=True, message="Fixed!"),
        ]

        mock_doctor.run_all_checks.side_effect = [failed_results, fixed_results]
        mock_doctor.format_report.side_effect = ["Failed report", "Fixed report"]
        mock_doctor.auto_fix.return_value = (1, 0)  # 1 fixed, 0 failed

        monkeypatch.setattr("thuis.doctor.Doctor", lambda verbose: mock_doctor)

        exit_code = run_doctor(fix_mode=True, verbose=False)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Auto-fix: 1 fixed, 0 failed" in captured.out
        assert "Fixed report" in captured.out

    def test_run_doctor_fix_mode_partial_failure(self, monkeypatch, tmp_path, capsys):
        """Test run_doctor with fix_mode=True returns 1 when some fixes fail."""
        mock_doctor = MagicMock()

        failed_results = [
            CheckResult(name="Check 1", passed=False, message="Failed", fixable=True, fix_hint="Fix"),
            CheckResult(name="Check 2", passed=False, message="Failed", fixable=True, fix_hint="Fix"),
        ]
        still_failed_results = [
            CheckResult(name="Check 1", passed=True, message="Fixed"),
            CheckResult(name="Check 2", passed=False, message="Still failed", fixable=True, fix_hint="Fix"),
        ]

        mock_doctor.run_all_checks.side_effect = [failed_results, still_failed_results]
        mock_doctor.format_report.side_effect = ["Failed report", "Still failed report"]
        mock_doctor.auto_fix.return_value = (1, 1)  # 1 fixed, 1 failed

        monkeypatch.setattr("thuis.doctor.Doctor", lambda verbose: mock_doctor)

        exit_code = run_doctor(fix_mode=True, verbose=False)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Auto-fix: 1 fixed, 1 failed" in captured.out