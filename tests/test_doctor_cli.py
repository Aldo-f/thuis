"""
Integration tests for the doctor CLI invocation via main.py.

Tests cover:
- Running `python src/thuis/main.py doctor` via subprocess
- Help text for doctor subcommand
"""

import sys
import subprocess
from pathlib import Path

import pytest


# Project root for running main.py
PROJECT_ROOT = Path(__file__).parent.parent
MAIN_PY = PROJECT_ROOT / "src" / "thuis" / "main.py"


def _run_doctor_cli(args: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run the doctor CLI via main.py and return the completed process."""
    if cwd is None:
        cwd = PROJECT_ROOT
    cmd = [sys.executable, str(MAIN_PY), "doctor"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


class TestDoctorCLI:
    """Integration tests for the doctor subcommand via main.py."""

    def test_doctor_subcommand_runs(self):
        """Test that `python src/thuis/main.py doctor` runs and returns exit code 0 or 1."""
        result = _run_doctor_cli([])
        
        # Should exit with 0 (all checks pass) or 1 (issues found)
        assert result.returncode in (0, 1), (
            f"Expected exit code 0 or 1, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        
        # Should produce the colored doctor report
        assert "=== thuis Doctor Report ===" in result.stdout
        assert "✓ PASS" in result.stdout or "✗ FAIL" in result.stdout

    def test_doctor_help_shows_usage(self):
        """Test that `python src/thuis/main.py doctor --help` shows usage with 'doctor'."""
        result = _run_doctor_cli(["--help"])
        
        # Help should exit with 0
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        
        # Usage text should mention doctor subcommand options
        assert "--fix" in result.stdout
        assert "--verbose" in result.stdout or "-v" in result.stdout
        assert "auto-fix" in result.stdout.lower() or "fix" in result.stdout.lower()

    def test_doctor_fix_flag_accepted(self):
        """Test that --fix flag is accepted (may return 0 or 1 depending on issues)."""
        result = _run_doctor_cli(["--fix"])
        
        # Should exit with 0 (fixed) or 1 (issues remain)
        assert result.returncode in (0, 1), (
            f"Expected exit code 0 or 1, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        
        # Should show auto-fix attempt
        assert "=== Attempting Auto-Fix ===" in result.stdout or "Auto-fix:" in result.stdout

    def test_doctor_verbose_flag_accepted(self):
        """Test that -v/--verbose flag is accepted."""
        result = _run_doctor_cli(["-v"])
        
        # Should exit with 0 or 1
        assert result.returncode in (0, 1), (
            f"Expected exit code 0 or 1, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        
        # Should produce the colored doctor report
        assert "=== thuis Doctor Report ===" in result.stdout

    def test_doctor_report_contains_all_checks(self):
        """Test that the doctor report includes all expected check categories."""
        result = _run_doctor_cli([])
        
        assert result.returncode in (0, 1)
        
        # Check all 6 check categories appear in output
        expected_checks = [
            "Python Dependencies",
            "Decryption Engines",
            "N_m3u8DL-RE",
            "Widevine CDM",
            "Environment Variables",
            ".env File",
        ]
        
        for check in expected_checks:
            assert check in result.stdout, f"Check '{check}' not found in output"

    def test_doctor_output_has_ansi_colors(self):
        """Test that the doctor output contains ANSI color codes."""
        result = _run_doctor_cli([])
        
        assert result.returncode in (0, 1)
        
        # ANSI color codes should be present (GREEN, RED, YELLOW, BLUE, CYAN, BOLD, RESET)
        assert "\033[92m" in result.stdout or "\033[32m" in result.stdout  # GREEN
        assert "\033[91m" in result.stdout or "\033[31m" in result.stdout  # RED
        assert "\033[0m" in result.stdout  # RESET