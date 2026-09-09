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
from typing import Optional, List, Tuple, Dict, Any

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
        """Run all health checks and return results."""
        self.results = [
            self.check_python_deps(),
            self.check_decryption_engines(),
            self.check_n_m3u8dl_re(),
            self.check_cdm(),
            self.check_env_vars(),
            self.check_env_file(),
        ]
        return self.results

    def check_python_deps(self) -> CheckResult:
        """Check required Python packages are importable."""
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
                fix_hint="Run: uv pip install -r requirements.txt --python .venv/bin/python"
            )
        return CheckResult(
            name="Python Dependencies",
            passed=True,
            message="All required packages available"
        )

    def check_decryption_engines(self) -> CheckResult:
        """Check at least one decryption engine binary is available."""
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
                fix_hint="Install one of: mp4decrypt (Bento4), shaka-packager, or ffmpeg"
            )
        return CheckResult(
            name="Decryption Engines",
            passed=True,
            message=f"Available: {', '.join(found)}"
        )

    def check_n_m3u8dl_re(self) -> CheckResult:
        """Check N_m3u8DL-RE is available in PATH."""
        path = find_binary("N_m3u8DL-RE")
        if not path:
            return CheckResult(
                name="N_m3u8DL-RE",
                passed=False,
                message="Not found in PATH",
                fixable=True,
                fix_hint="Download from https://github.com/nilaoda/N_m3u8DL-RE/releases and add to PATH"
            )
        return CheckResult(
            name="N_m3u8DL-RE",
            passed=True,
            message=f"Found at {path}"
        )

    def check_cdm(self) -> CheckResult:
        """Check Widevine CDM (.wvd) is available and valid."""
        cache_dir = get_cdm_cache_dir()
        cdm_path = cache_dir / "widevine_l3_android.wvd"

        if not cdm_path.exists():
            return CheckResult(
                name="Widevine CDM",
                passed=False,
                message=f"Not found at {cdm_path}",
                fixable=False,  # Cannot auto-fix CDM extraction
                fix_hint="Run: python scripts/extract_cdm.py (requires Android device/emulator) or place .wvd manually"
            )

        # Validate with pywidevine
        try:
            from pywidevine.device import Device, DeviceTypes
            device = Device.load(str(cdm_path))
            if device.type != DeviceTypes.ANDROID:
                return CheckResult(
                    name="Widevine CDM",
                    passed=False,
                    message=f"Wrong device type: {device.type} (expected ANDROID)",
                    fixable=False,
                    fix_hint="Extract a valid L3 ANDROID CDM"
                )
            if device.security_level != 3:
                return CheckResult(
                    name="Widevine CDM",
                    passed=False,
                    message=f"Wrong security level: {device.security_level} (expected 3/L3)",
                    fixable=False,
                    fix_hint="Extract a valid L3 ANDROID CDM"
                )
            return CheckResult(
                name="Widevine CDM",
                passed=True,
                message=f"Valid L3 ANDROID CDM at {cdm_path}"
            )
        except Exception as e:
            return CheckResult(
                name="Widevine CDM",
                passed=False,
                message=f"Validation failed: {e}",
                fixable=False,
                fix_hint="Re-extract CDM or place a valid .wvd file"
            )

    def check_env_vars(self) -> CheckResult:
        """Check DRM-related environment variables."""
        issues = []

        # VRT credentials
        if not os.getenv("VRT_EMAIL") and not os.getenv("VRT_PASSWORD"):
            issues.append("VRT_EMAIL/VRT_PASSWORD not set (using built-in defaults)")

        # DECRYPT_DRM
        policy = get_decrypt_policy()
        if policy == "no":
            issues.append("DECRYPT_DRM=no (DRM decryption disabled)")

        # WVD_CDM_PATH
        wvd_path = os.getenv("WVD_CDM_PATH")
        if wvd_path:
            path = Path(wvd_path).expanduser()
            if not path.exists():
                issues.append(f"WVD_CDM_PATH points to non-existent file: {wvd_path}")

        if issues:
            return CheckResult(
                name="Environment Variables",
                passed=False,
                message="; ".join(issues),
                fixable=True,
                fix_hint="Set vars in .env or export: VRT_EMAIL, VRT_PASSWORD, DECRYPT_DRM=yes, WVD_CDM_PATH"
            )
        return CheckResult(
            name="Environment Variables",
            passed=True,
            message="All DRM env vars configured"
        )

    def check_env_file(self) -> CheckResult:
        """Check .env file exists and has expected keys."""
        env_path = Path(".env")
        if not env_path.exists():
            return CheckResult(
                name=".env File",
                passed=False,
                message="No .env file found in project root",
                fixable=True,
                fix_hint="Create .env from .env.template: cp .env.template .env"
            )

        # Check for expected keys
        expected_keys = ["VRT_EMAIL", "VRT_PASSWORD", "DECRYPT_DRM", "WVD_CDM_PATH"]
        found_keys = set()
        try:
            content = env_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0].strip()
                    found_keys.add(key)
        except Exception as e:
            return CheckResult(
                name=".env File",
                passed=False,
                message=f"Failed to read .env: {e}",
                fixable=False,
                fix_hint="Check file permissions"
            )

        missing = [k for k in expected_keys if k not in found_keys]
        if missing:
            return CheckResult(
                name=".env File",
                passed=False,
                message=f"Missing keys: {', '.join(missing)}",
                fixable=True,
                fix_hint="Add missing keys to .env file"
            )

        return CheckResult(
            name=".env File",
            passed=True,
            message=f"All expected keys present ({', '.join(expected_keys)})"
        )

    def format_report(self, results: List[CheckResult]) -> str:
        """Format check results as colored ANSI output."""
        lines = []
        lines.append(f"{Colors.BOLD}{Colors.CYAN}=== thuis Doctor Report ==={Colors.RESET}")
        lines.append("")

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)

        for result in results:
            if result.passed:
                status = f"{Colors.GREEN}✓ PASS{Colors.RESET}"
            else:
                status = f"{Colors.RED}✗ FAIL{Colors.RESET}"
                if result.fixable:
                    status += f" {Colors.YELLOW}(fixable){Colors.RESET}"

            lines.append(f"  {status}  {Colors.BOLD}{result.name}{Colors.RESET}")
            lines.append(f"    {Colors.DIM}{result.message}{Colors.RESET}")

            if not result.passed and result.fix_hint:
                lines.append(f"    {Colors.BLUE}→ Fix: {result.fix_hint}{Colors.RESET}")
            lines.append("")

        # Summary
        if passed_count == total_count:
            summary = f"{Colors.GREEN}{Colors.BOLD}All checks passed! System ready for DRM decryption.{Colors.RESET}"
        else:
            failed = total_count - passed_count
            summary = f"{Colors.RED}{Colors.BOLD}{failed}/{total_count} checks failed.{Colors.RESET}"
            fixable = sum(1 for r in results if not r.passed and r.fixable)
            if fixable:
                summary += f" {Colors.YELLOW}{fixable} can be auto-fixed with --fix.{Colors.RESET}"

        lines.append(summary)
        return "\n".join(lines)

    def auto_fix(self, results: List[CheckResult]) -> Tuple[int, int]:
        """Attempt to auto-fix failed checks that are fixable.
        
        Returns:
            Tuple of (fixed_count, failed_fix_count)
        """
        fixed = 0
        failed = 0

        for result in results:
            if result.passed or not result.fixable:
                continue

            fix_method = getattr(self, f"_fix_{result.name.lower().replace(' ', '_').replace('.', '')}", None)
            if fix_method:
                self._log(f"Attempting fix for: {result.name}")
                try:
                    if fix_method():
                        fixed += 1
                        self._log(f"Fixed: {result.name}")
                    else:
                        failed += 1
                        self._log(f"Fix failed: {result.name}", "warning")
                except Exception as e:
                    failed += 1
                    self._log(f"Fix error for {result.name}: {e}", "error")
            else:
                self._log(f"No fix method for: {result.name}", "warning")
                failed += 1

        return fixed, failed

    def _fix_python_deps(self) -> bool:
        """Install missing Python dependencies via uv."""
        req_file = Path("requirements.txt")
        if not req_file.exists():
            self._log("requirements.txt not found", "error")
            return False

        try:
            # Try uv first (preferred)
            if shutil.which("uv"):
                result = subprocess.run(
                    ["uv", "pip", "install", "-r", str(req_file), "--python", ".venv/bin/python"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    return True
                self._log(f"uv install failed: {result.stderr}", "warning")

            # Fallback to pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            self._log(f"Python deps install error: {e}", "error")
            return False

    def _fix_decryption_engine(self) -> bool:
        """Install a decryption engine via package manager."""
        pkg_mgr = self._detect_package_manager()
        if not pkg_mgr:
            self._log("No supported package manager found", "error")
            return False

        # Try mp4decrypt (Bento4) first - most widely available
        if pkg_mgr == "apt":
            return self._apt_install(["bento4-utils"])
        elif pkg_mgr == "brew":
            return self._brew_install(["bento4"])
        elif pkg_mgr == "pacman":
            return self._pacman_install(["bento4"])
        elif pkg_mgr == "dnf":
            return self._dnf_install(["bento4"])
        elif pkg_mgr == "choco":
            return self._choco_install(["bento4"])

        return False

    def _fix_n_m3u8dl_re(self) -> bool:
        """N_m3u8DL-RE cannot be auto-installed via package manager.
        User must download manually."""
        self._log("N_m3u8DL-RE must be downloaded manually from GitHub releases", "warning")
        return False

    def _fix_decrypt_drm(self) -> bool:
        """Enable DRM decryption by setting DECRYPT_DRM=yes."""
        env_path = Path(".env")
        try:
            if env_path.exists():
                content = env_path.read_text()
                lines = content.splitlines()
                new_lines = []
                found = False
                for line in lines:
                    if line.strip().startswith("DECRYPT_DRM"):
                        new_lines.append("DECRYPT_DRM=yes")
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    new_lines.append("DECRYPT_DRM=yes")
                env_path.write_text("\n".join(new_lines) + "\n")
            else:
                # Create from template if exists, otherwise create minimal
                template = Path(".env.template")
                if template.exists():
                    content = template.read_text()
                    content = content.replace("DECRYPT_DRM=no", "DECRYPT_DRM=yes")
                    env_path.write_text(content)
                else:
                    env_path.write_text("DECRYPT_DRM=yes\n")
            return True
        except Exception as e:
            self._log(f"Failed to update .env: {e}", "error")
            return False

    def _fix_env_file(self) -> bool:
        """Create .env from .env.template if missing."""
        env_path = Path(".env")
        template_path = Path(".env.template")

        if env_path.exists():
            return True  # Already exists

        if template_path.exists():
            try:
                shutil.copy2(template_path, env_path)
                self._log("Created .env from .env.template")
                return True
            except Exception as e:
                self._log(f"Failed to copy template: {e}", "error")
                return False

        # Create minimal .env
        try:
            env_path.write_text("# thuis environment variables\n"
                                "VRT_EMAIL=\n"
                                "VRT_PASSWORD=\n"
                                "DECRYPT_DRM=yes\n"
                                "WVD_CDM_PATH=\n")
            return True
        except Exception as e:
            self._log(f"Failed to create .env: {e}", "error")
            return False

    def _detect_package_manager(self) -> Optional[str]:
        """Detect the system package manager."""
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
        """Run command with sudo, prompting user."""
        print(f"{Colors.YELLOW}This requires sudo. Command: {' '.join(cmd)}{Colors.RESET}")
        try:
            result = subprocess.run(["sudo"] + cmd, timeout=120)
            return result.returncode == 0
        except Exception as e:
            self._log(f"sudo command failed: {e}", "error")
            return False

    def _apt_install(self, packages: List[str]) -> bool:
        """Install packages via apt."""
        # Update first
        if not self._run_with_sudo(["apt", "update"]):
            return False
        return self._run_with_sudo(["apt", "install", "-y"] + packages)

    def _brew_install(self, packages: List[str]) -> bool:
        """Install packages via Homebrew."""
        try:
            result = subprocess.run(["brew", "install"] + packages, timeout=180)
            return result.returncode == 0
        except Exception as e:
            self._log(f"brew install failed: {e}", "error")
            return False

    def _pacman_install(self, packages: List[str]) -> bool:
        """Install packages via pacman."""
        return self._run_with_sudo(["pacman", "-S", "--noconfirm"] + packages)

    def _dnf_install(self, packages: List[str]) -> bool:
        """Install packages via dnf."""
        return self._run_with_sudo(["dnf", "install", "-y"] + packages)

    def _choco_install(self, packages: List[str]) -> bool:
        """Install packages via Chocolatey."""
        try:
            result = subprocess.run(["choco", "install", "-y"] + packages, timeout=180)
            return result.returncode == 0
        except Exception as e:
            self._log(f"choco install failed: {e}", "error")
            return False


def run_doctor(fix_mode: bool = False, verbose: bool = False) -> int:
    """
    Main entry point for doctor command.
    
    Args:
        fix_mode: If True, attempt to auto-fix issues.
        verbose: If True, enable verbose logging.
        
    Returns:
        Exit code: 0 = ready, 1 = issues found, 2 = error
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    doctor = Doctor(verbose=verbose)
    results = doctor.run_all_checks()

    # Print report
    report = doctor.format_report(results)
    print(report)

    # Check if all passed
    all_passed = all(r.passed for r in results)
    if all_passed:
        return 0

    # Try auto-fix if requested
    if fix_mode:
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Attempting Auto-Fix ==={Colors.RESET}\n")
        fixed, failed = doctor.auto_fix(results)
        print(f"\n{Colors.BOLD}Auto-fix: {fixed} fixed, {failed} failed{Colors.RESET}\n")

        # Re-run checks after fix
        results = doctor.run_all_checks()
        report = doctor.format_report(results)
        print(report)

        all_passed = all(r.passed for r in results)
        if all_passed:
            return 0
        return 1

    return 1


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="thuis system health check")
    parser.add_argument("--fix", action="store_true", help="Attempt to auto-fix issues")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    sys.exit(run_doctor(fix_mode=args.fix, verbose=args.verbose))


if __name__ == "__main__":
    main()