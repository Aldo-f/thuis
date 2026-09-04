---
slug: thuis-doctor
status: approved
intent: clear
review_required: false
approach: Add a `doctor` and `doctor --fix` CLI subcommand that diagnoses DRM pipeline readiness, reports issues with doc links, and auto-fixes installable dependencies
---

# Plan: thuis doctor / doctor --fix CLI Subcommand

## Objective
Add a self-diagnosing `doctor` command to the thuis CLI that checks all DRM pipeline dependencies, reports issues with actionable guidance and documentation links, and optionally auto-fixes installable components (system packages, env vars). This addresses the user pain point: when DRM download fails, users don't know what's missing or how to fix it.

## Context / Why
- DRM pipeline requires: decryption engine (mp4decrypt/shaka-packager/ffmpeg), N_m3u8DL-RE, valid CDM (.wvd), pywidevine, pymp4, DECRYPT_DRM=yes
- Current failure mode: cryptic errors ("No decryption engine found", "CDM unavailable") with no guidance
- Existing helpers: `find_binary()` (drm_decrypt.py:76), `ensure_cdm()` (cdm.py:237), `get_decrypt_policy()` (main.py), `scripts/extract_cdm.py`
- User must install system packages manually (apt/brew/scoop) — tool can automate this with `--fix`
- CDM extraction requires physical hardware → cannot auto-fix, must guide to `scripts/extract_cdm.py`

## Deliverables
| id | File | Change |
|----|------|--------|
| C1 | `src/thuis/doctor.py` **(new)** | Check functions for each DRM pipeline component + report formatter |
| C2 | `src/thuis/main.py` | Register `doctor` / `doctor --fix` subcommands |
| C3 | `src/thuis/doctor.py` | Check functions reusing: `find_binary()`, `ensure_cdm()`, `get_decrypt_policy()`, pywidevine/pymp4 imports |
| C4 | `src/thuis/doctor.py` | Report formatter: colored output, pass/fail, docs links, hints |
| C5 | `src/thuis/doctor.py` | Auto-fix logic: package installs (apt/brew/scoop), DECRYPT_DRM=yes in .env |
| C6 | `tests/test_doctor.py` **(new)** | Unit tests for check functions + integration test for CLI |

## Steps

### 1. Create `src/thuis/doctor.py` — Core Module
```python
#!/usr/bin/env python3
"""
Doctor command: diagnose DRM pipeline readiness and auto-fix installable issues.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

# Reuse existing detection
from thuis.drm_decrypt import find_binary, DECRYPTION_ENGINES, REQUIRED_BINARIES
from thuis.cdm import ensure_cdm, get_cdm_cache_dir
from thuis.main import get_decrypt_policy  # or inline the logic

# ANSI colors (no external deps)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class CheckResult:
    name: str
    status: bool  # True = pass, False = fail
    message: str
    fix_hint: Optional[str] = None
    doc_link: Optional[str] = None
    auto_fixable: bool = False


class Doctor:
    def __init__(self, fix_mode: bool = False):
        self.fix_mode = fix_mode
        self.results: List[CheckResult] = []
    
    def run_all_checks(self) -> List[CheckResult]:
        """Run all diagnostic checks."""
        self.results = [
            self.check_python_deps(),
            self.check_decrpytion_engines(),
            self.check_n_m3u8dl_re(),
            self.check_cdm(),
            self.check_env_vars(),
            self.check_env_file(),
        ]
        return self.results
    
    def check_python_deps(self) -> CheckResult:
        """Check pywidevine and pymp4 are importable."""
        missing = []
        for dep in ("pywidevine", "pymp4"):
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        if missing:
            return CheckResult(
                name="Python dependencies",
                status=False,
                message=f"Missing: {', '.join(missing)}",
                fix_hint="Run: uv pip install -r requirements.txt --python .venv/bin/python",
                doc_link="docs/REQUIREMENTS.md §5",
                auto_fixable=True,
            )
        return CheckResult(
            name="Python dependencies",
            status=True,
            message="pywidevine, pymp4 available",
        )
    
    def check_decrpytion_engines(self) -> CheckResult:
        """Check at least one decryption engine is available."""
        found = []
        for engine in DECRYPTION_ENGINES:
            binary = REQUIRED_BINARIES.get(engine, engine.lower())
            path = find_binary(binary)
            if path:
                found.append(f"{engine} ({path})")
        
        if not found:
            return CheckResult(
                name="Decryption engine",
                status=False,
                message="None found (mp4decrypt, shaka-packager, ffmpeg)",
                fix_hint="Install mp4decrypt (Bento4): see auto-fix or docs/REQUIREMENTS.md §2.1",
                doc_link="docs/REQUIREMENTS.md §2",
                auto_fixable=True,
            )
        return CheckResult(
            name="Decryption engine",
            status=True,
            message=f"Found: {', '.join(found)}",
        )
    
    def check_n_m3u8dl_re(self) -> CheckResult:
        """Check N_m3u8DL-RE is installed."""
        path = find_binary("N_m3u8DL-RE") or find_binary("N_m3u8DL-RE.exe")
        if not path:
            return CheckResult(
                name="N_m3u8DL-RE",
                status=False,
                message="Not in PATH",
                fix_hint="Install from GitHub Releases or via package manager (see auto-fix)",
                doc_link="docs/REQUIREMENTS.md §2.1, §4",
                auto_fixable=True,
            )
        return CheckResult(
            name="N_m3u8DL-RE",
            status=True,
            message=f"Found at {path}",
        )
    
    def check_cdm(self) -> CheckResult:
        """Check Widevine L3 CDM is available and valid."""
        # Try to get CDM path (this will auto-fetch if enabled)
        cdm_path = ensure_cdm()
        if cdm_path:
            return CheckResult(
                name="Widevine CDM (.wvd)",
                status=True,
                message=f"Valid CDM at {cdm_path}",
            )
        # Check if cache exists but invalid
        cache_dir = get_cdm_cache_dir()
        wvd_files = list(cache_dir.glob("*.wvd"))
        if wvd_files:
            return CheckResult(
                name="Widevine CDM (.wvd)",
                status=False,
                message=f"Found {len(wvd_files)} file(s) but invalid/revoked",
                fix_hint="Delete ~/.thuis/cdm/ and re-run, or extract fresh CDM",
                doc_link="docs/REQUIREMENTS.md §3.3; run: python scripts/extract_cdm.py",
                auto_fixable=False,  # Requires physical device
            )
        return CheckResult(
            name="Widevine CDM (.wvd)",
            status=False,
            message="No CDM found in cache",
            fix_hint="Extract from rooted Android device",
            doc_link="docs/REQUIREMENTS.md §3.3; run: python scripts/extract_cdm.py",
            auto_fixable=False,
        )
    
    def check_env_vars(self) -> CheckResult:
        """Check DECRYPT_DRM is enabled."""
        policy = get_decrypt_policy()
        if policy == "yes":
            return CheckResult(
                name="DECRYPT_DRM env var",
                status=True,
                message="Enabled (yes)",
            )
        return CheckResult(
            name="DECRYPT_DRM env var",
            status=False,
            message=f"Disabled ({policy})",
            fix_hint="Set DECRYPT_DRM=yes in .env or export in shell",
            doc_link="docs/REQUIREMENTS.md §6",
            auto_fixable=True,
        )
    
    def check_env_file(self) -> CheckResult:
        """Check .env file exists and has required vars."""
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return CheckResult(
                name=".env file",
                status=False,
                message="Not found (using defaults)",
                fix_hint="Create .env from .env.example or run auto-fix",
                doc_link="docs/REQUIREMENTS.md §6",
                auto_fixable=True,
            )
        # Check for DECRYPT_DRM in .env
        content = env_path.read_text()
        if "DECRYPT_DRM" not in content:
            return CheckResult(
                name=".env file",
                status=False,
                message="Exists but missing DECRYPT_DRM",
                fix_hint="Add DECRYPT_DRM=yes to .env",
                doc_link="docs/REQUIREMENTS.md §6",
                auto_fixable=True,
            )
        return CheckResult(
            name=".env file",
            status=True,
            message="Found with DECRYPT_DRM",
        )
    
    def format_report(self) -> str:
        """Generate colored report string."""
        lines = [
            f"{BOLD}thuis DRM Pipeline Diagnosis{RESET}",
            f"{'=' * 50}",
            "",
        ]
        
        all_pass = all(r.status for r in self.results)
        
        for r in self.results:
            icon = f"{GREEN}✓{RESET}" if r.status else f"{RED}✗{RESET}"
            lines.append(f"{icon} {BOLD}{r.name}{RESET}: {r.message}")
            if not r.status:
                if r.fix_hint:
                    lines.append(f"   {YELLOW}→ Fix:{RESET} {r.fix_hint}")
                if r.doc_link:
                    lines.append(f"   {BLUE}→ Docs:{RESET} {r.doc_link}")
            lines.append("")
        
        # Summary
        passed = sum(1 for r in self.results if r.status)
        total = len(self.results)
        lines.append(f"{'=' * 50}")
        if all_pass:
            lines.append(f"{GREEN}{BOLD}All checks passed!{RESET} DRM pipeline ready.")
            lines.append(f"Run: {BOLD}./thuis.sh <drm-url>{RESET}")
        else:
            lines.append(f"{RED}{BOLD}{total - passed}/{total} checks failed.{RESET}")
            if self.fix_mode:
                lines.append("Auto-fix attempted for fixable items.")
            else:
                lines.append(f"Run {BOLD}thuis doctor --fix{RESET} to auto-fix installable issues.")
                lines.append(f"For CDM: {BLUE}python scripts/extract_cdm.py{RESET}")
        return "\n".join(lines)
    
    def auto_fix(self) -> Tuple[int, int]:
        """Attempt to fix auto-fixable issues.
        
        Returns:
            (fixed_count, failed_count)
        """
        fixed = 0
        failed = 0
        
        for r in self.results:
            if r.status or not r.auto_fixable:
                continue
            
            if r.name == "Python dependencies":
                if self._fix_python_deps():
                    fixed += 1
                else:
                    failed += 1
            
            elif r.name == "Decryption engine":
                if self._fix_decrpytion_engine():
                    fixed += 1
                else:
                    failed += 1
            
            elif r.name == "N_m3u8DL-RE":
                if self._fix_n_m3u8dl_re():
                    fixed += 1
                else:
                    failed += 1
            
            elif r.name == "DECRYPT_DRM env var":
                if self._fix_decrypt_drm():
                    fixed += 1
                else:
                    failed += 1
            
            elif r.name == ".env file":
                if self._fix_env_file():
                    fixed += 1
                else:
                    failed += 1
        
        return fixed, failed
    
    def _fix_python_deps(self) -> bool:
        """Install Python deps via uv/pip."""
        try:
            # Prefer uv if available
            uv = shutil.which("uv")
            if uv:
                subprocess.run([uv, "pip", "install", "-r", "requirements.txt", "--python", ".venv/bin/python"], check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _fix_decrpytion_engine(self) -> bool:
        """Install mp4decrypt (Bento4) via system package manager."""
        pm = self._detect_package_manager()
        if not pm:
            print(f"{YELLOW}No supported package manager detected. Install mp4decrypt manually.{RESET}")
            return False
        
        try:
            if pm == "apt":
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "bento4"], check=True)
            elif pm == "brew":
                subprocess.run(["brew", "install", "bento4"], check=True)
            elif pm == "scoop":
                subprocess.run(["scoop", "install", "bento4"], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _fix_n_m3u8dl_re(self) -> bool:
        """Install N_m3u8DL-RE via package manager or download."""
        pm = self._detect_package_manager()
        
        # Try package manager first
        if pm == "brew":
            try:
                subprocess.run(["brew", "install", "nilaoda/tap/n_m3u8dl-re"], check=True)
                return True
            except subprocess.CalledProcessError:
                pass
        elif pm == "scoop":
            try:
                subprocess.run(["scoop", "install", "n_m3u8dl-re"], check=True)
                return True
            except subprocess.CalledProcessError:
                pass
        
        # Fallback: download binary
        try:
            system = platform.system().lower()
            arch = platform.machine().lower()
            if system == "linux" and arch in ("x86_64", "amd64"):
                url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_linux_x64"
            elif system == "darwin" and arch in ("x86_64", "arm64"):
                url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_macos_x64"
            elif system == "windows" and arch in ("amd64", "x86_64"):
                url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_win64.exe"
            else:
                return False
            
            dest = Path("/usr/local/bin/N_m3u8DL-RE") if system != "windows" else Path("N_m3u8DL-RE.exe")
            # Use curl/wget via subprocess
            if shutil.which("curl"):
                subprocess.run(["curl", "-L", "-o", str(dest), url], check=True)
            elif shutil.which("wget"):
                subprocess.run(["wget", "-O", str(dest), url], check=True)
            else:
                return False
            
            if system != "windows":
                dest.chmod(0o755)
            return True
        except Exception:
            return False
    
    def _fix_decrypt_drm(self) -> bool:
        """Set DECRYPT_DRM=yes in .env."""
        return self._fix_env_file()
    
    def _fix_env_file(self) -> bool:
        """Ensure .env exists with DECRYPT_DRM=yes."""
        env_path = Path.cwd() / ".env"
        content = env_path.read_text() if env_path.exists() else ""
        
        if "DECRYPT_DRM" not in content:
            with env_path.open("a") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write("DECRYPT_DRM=yes\n")
        
        # Also ensure WVD_CDM_PATH is commented as template
        if "WVD_CDM_PATH" not in content:
            with env_path.open("a") as f:
                f.write("# WVD_CDM_PATH=/path/to/cdm\n")
        
        return True
    
    def _detect_package_manager(self) -> Optional[str]:
        """Detect system package manager."""
        system = platform.system().lower()
        if system == "linux":
            if shutil.which("apt"):
                return "apt"
        elif system == "darwin":
            if shutil.which("brew"):
                return "brew"
        elif system == "windows":
            if shutil.which("scoop"):
                return "scoop"
            if shutil.which("choco"):
                return "choco"
        return None


def run_doctor(fix_mode: bool = False) -> int:
    """Main entry point for doctor command.
    
    Returns:
        Exit code: 0=all ok, 1=issues found, 2=error
    """
    doctor = Doctor(fix_mode=fix_mode)
    doctor.run_all_checks()
    
    if fix_mode:
        fixed, failed = doctor.auto_fix()
        print(f"{BLUE}Auto-fix: {fixed} fixed, {failed} failed{RESET}")
        # Re-run checks after fix
        doctor.run_all_checks()
    
    print(doctor.format_report())
    
    if all(r.status for r in doctor.results):
        return 0
    return 1
```

### 2. Register Subcommand in `src/thuis/main.py`
Add to argument parser (near line 100-150 where subcommands are defined):
```python
# Add subparser for doctor
doctor_parser = subparsers.add_parser("doctor", help="Diagnose DRM pipeline readiness")
doctor_parser.add_argument("--fix", action="store_true", help="Attempt to auto-fix installable issues")
doctor_parser.set_defaults(func=cmd_doctor)
```

Add handler function:
```python
def cmd_doctor(args):
    """Handle doctor subcommand."""
    from thuis.doctor import run_doctor
    sys.exit(run_doctor(fix_mode=args.fix))
```

### 3. Create `tests/test_doctor.py`
```python
"""Tests for doctor command."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thuis.doctor import Doctor, run_doctor, CheckResult


class TestDoctorChecks:
    """Test individual check functions."""
    
    def test_check_python_deps_all_present(self, monkeypatch):
        """Pass when pywidevine and pymp4 importable."""
        with patch.dict("sys.modules", {"pywidevine": MagicMock(), "pymp4": MagicMock()}):
            doctor = Doctor()
            result = doctor.check_python_deps()
            assert result.status is True
    
    def test_check_python_deps_missing(self, monkeypatch):
        """Fail when deps missing."""
        with patch.dict("sys.modules", {"pywidevine": None, "pymp4": None}, clear=True):
            # Actually need to simulate ImportError
            doctor = Doctor()
            # Mock import to raise ImportError
            with patch("builtins.__import__", side_effect=ImportError):
                result = doctor.check_python_deps()
                assert result.status is False
                assert result.auto_fixable is True
    
    def test_check_env_vars_enabled(self, monkeypatch):
        """Pass when DECRYPT_DRM=yes."""
        with patch("thuis.doctor.get_decrypt_policy", return_value="yes"):
            doctor = Doctor()
            result = doctor.check_env_vars()
            assert result.status is True
    
    def test_check_env_vars_disabled(self, monkeypatch):
        """Fail when DECRYPT_DRM=no."""
        with patch("thuis.doctor.get_decrypt_policy", return_value="no"):
            doctor = Doctor()
            result = doctor.check_env_vars()
            assert result.status is False
            assert result.auto_fixable is True


class TestDoctorAutoFix:
    """Test auto-fix logic."""
    
    def test_fix_env_file_creates_if_missing(self, tmp_path, monkeypatch):
        """Creates .env with DECRYPT_DRM=yes."""
        monkeypatch.chdir(tmp_path)
        doctor = Doctor()
        assert doctor._fix_env_file() is True
        env_content = (tmp_path / ".env").read_text()
        assert "DECRYPT_DRM=yes" in env_content
    
    def test_fix_env_file_updates_existing(self, tmp_path, monkeypatch):
        """Updates existing .env without DECRYPT_DRM."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("VRT_EMAIL=test@example.com\n")
        doctor = Doctor()
        assert doctor._fix_env_file() is True
        env_content = (tmp_path / ".env").read_text()
        assert "DECRYPT_DRM=yes" in env_content


class TestDoctorCLI:
    """Integration tests for CLI."""
    
    def test_doctor_help(self, capsys):
        """doctor --help shows usage."""
        with patch("sys.argv", ["thuis", "doctor", "--help"]):
            with pytest.raises(SystemExit) as exc:
                from thuis.main import main
                main()
            assert exc.value.code == 0
    
    def test_doctor_runs_checks(self, capsys, monkeypatch):
        """doctor runs and outputs report."""
        # Mock all checks to pass
        with patch("thuis.doctor.Doctor.check_python_deps", return_value=CheckResult("Python deps", True, "OK")):
            with patch("thuis.doctor.Doctor.check_decrpytion_engines", return_value=CheckResult("Engine", True, "OK")):
                with patch("thuis.doctor.Doctor.check_n_m3u8dl_re", return_value=CheckResult("N_m3u8DL-RE", True, "OK")):
                    with patch("thuis.doctor.Doctor.check_cdm", return_value=CheckResult("CDM", True, "OK")):
                        with patch("thuis.doctor.Doctor.check_env_vars", return_value=CheckResult("DECRYPT_DRM", True, "OK")):
                            with patch("thuis.doctor.Doctor.check_env_file", return_value=CheckResult(".env", True, "OK")):
                                exit_code = run_doctor(fix_mode=False)
                                assert exit_code == 0
                                out = capsys.readouterr().out
                                assert "All checks passed" in out
```

## Test / Verify
- `pytest tests/test_doctor.py` → all pass
- `python -m thuis doctor` → shows colored report with pass/fail
- `python -m thuis doctor --fix` → attempts auto-fix, re-runs checks
- `python -m thuis doctor --help` → shows usage
- Verify exit codes: 0=ready, 1=issues, 2=error

## Scope OUT (Must NOT Have)
- ❌ Auto-extract CDM (legal/hardware)
- ❌ Modify download pipeline logic
- ❌ Add Python dependencies (rich, colorama, etc.) — ANSI only
- ❌ Run sudo without prompt
- ❌ Change existing CLI behavior

## Explicit Constraints
- Reuse existing detection functions (single source of truth)
- Auto-fix limited to: system packages (mp4decrypt, N_m3u8DL-RE), DECRYPT_DRM=yes, .env creation
- CDM extraction guided to `scripts/extract_cdm.py` (cannot auto-fix)
- Output includes links to `docs/REQUIREMENTS.md` and `scripts/extract_cdm.py`
- Exit codes for CI/scripting

## Acceptance
- `thuis doctor` runs and shows colored status for all 6 check categories
- `thuis doctor --fix` installs mp4decrypt + N_m3u8DL-RE via package manager, sets DECRYPT_DRM=yes
- Failed checks show actionable hint + doc link (REQUIREMENTS.md § + extract_cdm.py)
- CDM check guides to `python scripts/extract_cdm.py` when missing/invalid
- All tests pass