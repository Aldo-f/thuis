#!/usr/bin/env python3
"""
C7 Doctor Module for VRT MAX downloader.

System health checks and auto-fix for the DRM pipeline:
- Python dependencies (yt-dlp, pywidevine, pymp4, python-dotenv)
- Decryption engines (mp4decrypt, shaka-packager, ffmpeg)
- N_m3u8DL-RE binary
- Widevine CDM (.wvd file)
- Environment variables (VRT_EMAIL, VRT_PASSWORD, DECRYPT_DRM, WVD_CDM_PATH)
- .env file existence and content
"""

import os
import sys
import subprocess
import shutil
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

# Reuse from existing modules
try:
    from .drm_decrypt import find_binary, DECRYPTION_ENGINES, REQUIRED_BINARIES
except ImportError:
    from thuis.drm_decrypt import find_binary, DECRYPTION_ENGINES, REQUIRED_BINARIES

try:
    from .cdm import ensure_cdm, get_cdm_cache_dir
except ImportError:
    from thuis.cdm import ensure_cdm, get_cdm_cache_dir

try:
    from .main import get_decrypt_policy
except ImportError:
    from thuis.main import get_decrypt_policy

logger = logging.getLogger(__name__)

# ANSI color codes (no external deps)
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    DIM = "\033[2m"

@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    passed: bool
    message: str
    fixable: bool = False
    fix_hint: str = ""

class Doctor:
    """System health checker and auto-fixer for thuis DRM pipeline."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[CheckResult] = []

    def _log(self, msg: str, level: str = "info") -> None:
        if self.verbose or level in ("warning", "error"):
            getattr(logger, level)(msg)

    def run_all_checks(self) -> List[CheckResult]:
        self.results = [
            self.check_python_deps(),
            self.check_decryption_engines(),
            self.check_n_m3u8dl_re(),
            self.check_cdm(),
            self.check_env_vars(),
            self.check_env_file(),
        ]
        return self.results

    # ---------- individual checks ----------
    def check_python_deps(self) -> CheckResult:
        required = {
            "yt_dlp": "yt-dlp (from fork)",
            "pywidevine": "pywidevine",
            "pymp4": "pymp4.parser",
            "dotenv": "python-dotenv",
        }
        missing = []
        for module, display in required.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(display)
        if missing:
            return CheckResult(
                name="Python Dependencies",
                passed=False,
                message=f"Missing: {', '.join(missing)}",
                fixable=True,
                fix_hint="Run: uv pip install -r requirements.txt --python .venv/bin/python",
            )
        return CheckResult(name="Python Dependencies", passed=True, message="All required packages available")

    def check_decryption_engines(self) -> CheckResult:
        found = []
        for engine in DECRYPTION_ENGINES:
            binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
            path = find_binary(binary_name)
            if path:
                found.append(f"{engine} ({path})")
        if not found:
            tried = []
            for engine in DECRYPTION_ENGINES:
                binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
                tried.append(f"{engine} ({binary_name})")
            return CheckResult(
                name="Decryption Engines",
                passed=False,
                message=f"No engine found. Tried: {', '.join(tried)}",
                fixable=True,
                fix_hint="Install one of: mp4decrypt (Bento4), shaka-packager, or ffmpeg",
            )
        return CheckResult(name="Decryption Engines", passed=True, message=f"Available: {', '.join(found)}")

    def check_n_m3u8dl_re(self) -> CheckResult:
        path = find_binary("N_m3u8DL-RE")
        if not path:
            return CheckResult(
                name="N_m3u8DL-RE",
                passed=False,
                message="Not found in PATH",
                fixable=True,
                fix_hint="Download from https://github.com/nilaoda/N_m3u8DL-RE/releases and add to PATH",
            )
        return CheckResult(name="N_m3u8DL-RE", passed=True, message=f"Found at {path}")

    def check_cdm(self) -> CheckResult:
        cache_dir = get_cdm_cache_dir()
        cdm_path = cache_dir / "widevine_l3_android.wvd"
        if not cdm_path.exists():
            return CheckResult(
                name="Widevine CDM",
                passed=False,
                message=f"Not found at {cdm_path}",
                fixable=False,
                fix_hint="Run: python scripts/extract_cdm.py (requires Android device/emulator) or place .wvd manually",
            )
        try:
            from pywidevine.device import Device, DeviceTypes
            device = Device.load(str(cdm_path))
            if device.type != DeviceTypes.ANDROID:
                return CheckResult(
                    name="Widevine CDM",
                    passed=False,
                    message=f"Wrong device type: {device.type} (expected ANDROID)",
                    fixable=False,
                    fix_hint="Extract a valid L3 ANDROID CDM",
                )
            if device.security_level != 3:
                return CheckResult(
                    name="Widevine CDM",
                    passed=False,
                    message=f"Wrong security level: {device.security_level} (expected 3/L3)",
                    fixable=False,
                    fix_hint="Extract a valid L3 ANDROID CDM",
                )
            return CheckResult(name="Widevine CDM", passed=True, message=f"Valid L3 ANDROID CDM at {cdm_path}")
        except Exception as e:
            return CheckResult(
                name="Widevine CDM",
                passed=False,
                message=f"Validation failed: {e}",
                fixable=False,
                fix_hint="Re-extract CDM or place a valid .wvd file",
            )

    def check_env_vars(self) -> CheckResult:
        issues = []
        if not os.getenv("VRT_EMAIL") and not os.getenv("VRT_PASSWORD"):
            issues.append("VRT_EMAIL/VRT_PASSWORD not set (using built-in defaults)")
        policy = get_decrypt_policy()
        if policy == "no":
            issues.append("DECRYPT_DRM=no (DRM decryption disabled)")
        wvd_path = os.getenv("WVD_CDM_PATH")
        if wvd_path:
            p = Path(wvd_path).expanduser()
            if not p.exists():
                issues.append(f"WVD_CDM_PATH points to non-existent file: {wvd_path}")
        if issues:
            return CheckResult(
                name="Environment Variables",
                passed=False,
                message="; ".join(issues),
                fixable=True,
                fix_hint="Set vars in .env or export: VRT_EMAIL, VRT_PASSWORD, DECRYPT_DRM=yes, WVD_CDM_PATH",
            )
        return CheckResult(name="Environment Variables", passed=True, message="All DRM env vars configured")

    def check_env_file(self) -> CheckResult:
        env_path = Path(".env")
        if not env_path.exists():
            return CheckResult(
                name=".env File",
                passed=False,
                message="No .env file found in project root",
                fixable=True,
                fix_hint="Create .env from .env.template: cp .env.template .env",
            )
        expected_keys = ["VRT_EMAIL", "VRT_PASSWORD", "DECRYPT_DRM", "WVD_CDM_PATH"]
        found_keys = set()
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0].strip()
                    found_keys.add(key)
        except Exception as e:
            return CheckResult(name=".env File", passed=False, message=f"Failed to read .env: {e}", fixable=False)
        missing = [k for k in expected_keys if k not in found_keys]
        if missing:
            return CheckResult(
                name=".env File",
                passed=False,
                message=f"Missing keys: {', '.join(missing)}",
                fixable=True,
                fix_hint="Add missing keys to .env file",
            )
        return CheckResult(name=".env File", passed=True, message=f"All expected keys present ({', '.join(expected_keys)})")

    def format_report(self, results: List[CheckResult]) -> str:
        lines = []
        lines.append(f"{Colors.BOLD}{Colors.CYAN}=== thuis Doctor Report ==={Colors.RESET}\n")
        passed = sum(r.passed for r in results)
        total = len(results)
        for r in results:
            status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if r.passed else f"{Colors.RED}✗ FAIL{Colors.RESET}" + (f" {Colors.YELLOW}(fixable){Colors.RESET}" if r.fixable else "")
            lines.append(f"  {status}  {Colors.BOLD}{r.name}{Colors.RESET}")
            lines.append(f"    {Colors.DIM}{r.message}{Colors.RESET}")
            if not r.passed and r.fix_hint:
                lines.append(f"    {Colors.BLUE}→ Fix: {r.fix_hint}{Colors.RESET}")
            lines.append("")
        summary = f"{Colors.GREEN}{Colors.BOLD}All checks passed! System ready for DRM decryption.{Colors.RESET}" if passed == total else f"{Colors.RED}{Colors.BOLD}{total - passed}/{total} checks failed.{Colors.RESET}"
        if passed != total:
            fixable = sum(1 for r in results if not r.passed and r.fixable)
            if fixable:
                summary += f" {Colors.YELLOW}{fixable} can be auto-fixed with --fix.{Colors.RESET}"
        lines.append(summary)
        return "\n".join(lines)

    # ---------- auto‑fix utilities ----------
    def auto_fix(self, results: List[CheckResult]) -> Tuple[int, int]:
        fixed = failed = 0
        for r in results:
            if r.passed or not r.fixable:
                continue
            method = getattr(self, f"_fix_{r.name.lower().replace(' ', '_').replace('.', '')}", None)
            if method:
                self._log(f"Attempting fix for {r.name}")
                try:
                    if method():
                        fixed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    self._log(f"Fix error for {r.name}: {e}", "error")
            else:
                failed += 1
        return fixed, failed

    def _fix_python_deps(self) -> bool:
        req = Path("requirements.txt")
        if not req.exists():
            self._log("requirements.txt not found", "error")
            return False
        if shutil.which("uv"):
            res = subprocess.run(["uv", "pip", "install", "-r", str(req), "--python", ".venv/bin/python"], capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                return True
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], capture_output=True, text=True, timeout=120)
        return res.returncode == 0

    def _fix_decryption_engine(self) -> bool:
        mgr = self._detect_package_manager()
        if not mgr:
            self._log("No supported package manager found", "error")
            return False
        if mgr == "apt":
            return self._apt_install(["bento4-utils"])
        if mgr == "brew":
            return self._brew_install(["bento4"])
        if mgr == "pacman":
            return self._pacman_install(["bento4"])
        if mgr == "dnf":
            return self._dnf_install(["bento4"])
        if mgr == "choco":
            return self._choco_install(["bento4"])
        return False

    def _fix_n_m3u8dl_re(self) -> bool:
        self._log("N_m3u8DL-RE must be downloaded manually from GitHub releases", "warning")
        return False

    def _fix_decrypt_drm(self) -> bool:
        env = Path(".env")
        try:
            if env.exists():
                lines = []
                found = False
                for line in env.read_text().splitlines():
                    if line.strip().startswith("DECRYPT_DRM"):
                        lines.append("DECRYPT_DRM=yes")
                        found = True
                    else:
                        lines.append(line)
                if not found:
                    lines.append("DECRYPT_DRM=yes")
                env.write_text("\n".join(lines) + "\n")
            else:
                tpl = Path(".env.template")
                if tpl.exists():
                    env.write_text(tpl.read_text().replace("DECRYPT_DRM=no", "DECRYPT_DRM=yes"))
                else:
                    env.write_text("DECRYPT_DRM=yes\n")
            return True
        except Exception as e:
            self._log(f"Failed to update .env: {e}", "error")
            return False

    def _fix_env_file(self) -> bool:
        env = Path(".env")
        tpl = Path(".env.template")
        if env.exists():
            return True
        if tpl.exists():
            try:
                shutil.copy2(tpl, env)
                self._log("Created .env from template")
                return True
            except Exception as e:
                self._log(f"Copy failed: {e}", "error")
                return False
        try:
            env.write_text("# thuis environment variables\nVRT_EMAIL=\nVRT_PASSWORD=\nDECRYPT_DRM=yes\nWVD_CDM_PATH=\n")
            return True
        except Exception as e:
            self._log(f"Failed to create .env: {e}", "error")
            return False

    # ---------- helper methods ----------
    def _detect_package_manager(self) -> Optional[str]:
        if shutil.which("apt"):
            return "apt"
        if shutil.which("brew"):
            return "brew"
        if shutil.which("pacman"):
            return "pacman"
        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("choco"):
            return "choco"
        return None

    def _run_with_sudo(self, cmd: List[str]) -> bool:
        print(f"{Colors.YELLOW}This requires sudo. Command: {' '.join(cmd)}{Colors.RESET}")
        try:
            res = subprocess.run(["sudo"] + cmd, timeout=120)
            return res.returncode == 0
        except Exception as e:
            self._log(f"sudo failed: {e}", "error")
            return False

    def _apt_install(self, pkgs: List[str]) -> bool:
        if not self._run_with_sudo(["apt", "update"]):
            return False
        return self._run_with_sudo(["apt", "install", "-y"] + pkgs)

    def _brew_install(self, pkgs: List[str]) -> bool:
        try:
            res = subprocess.run(["brew", "install"] + pkgs, timeout=180)
            return res.returncode == 0
        except Exception as e:
            self._log(f"brew failed: {e}", "error")
            return False

    def _pacman_install(self, pkgs: List[str]) -> bool:
        return self._run_with_sudo(["pacman", "-S", "--noconfirm"] + pkgs)

    def _dnf_install(self, pkgs: List[str]) -> bool:
        return self._run_with_sudo(["dnf", "install", "-y"] + pkgs)

    def _choco_install(self, pkgs: List[str]) -> bool:
        try:
            res = subprocess.run(["choco", "install", "-y"] + pkgs, timeout=180)
            return res.returncode == 0
        except Exception as e:
            self._log(f"choco failed: {e}", "error")
            return False

def run_doctor(fix_mode: bool = False, verbose: bool = False) -> int:
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    doc = Doctor(verbose=verbose)
    results = doc.run_all_checks()
    print(doc.format_report(results))
    if all(r.passed for r in results):
        return 0
    if fix_mode:
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Attempting Auto-fix ==={Colors.RESET}\n")
        fixed, failed = doc.auto_fix(results)
        print(f"\nAuto-fix: {fixed} fixed, {failed} failed\n")
        results = doc.run_all_checks()
        print(doc.format_report(results))
        return 0 if all(r.passed for r in results) else 1
    return 1

def main():
    import argparse
    p = argparse.ArgumentParser(description="thuis system health check")
    p.add_argument("--fix", action="store_true", help="Attempt to auto‑fix issues")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = p.parse_args()
    sys.exit(run_doctor(fix_mode=args.fix, verbose=args.verbose))

if __name__ == "__main__":
    main()
