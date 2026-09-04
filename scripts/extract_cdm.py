#!/usr/bin/env python3
"""
Widevine L3 CDM Extraction Helper

Prints step-by-step wvdumper/Frida extraction guide and validates existing .wvd files.
Never auto-executes adb/frida/wvdumper commands (legal/consent requirement).

Usage:
    python scripts/extract_cdm.py           # Validate cache + print guide if missing/invalid
    python scripts/extract_cdm.py --help    # Show help
    python scripts/extract_cdm.py --guide   # Print extraction guide only (skip validation)

Exit codes:
    0 = valid CDM found in cache
    1 = no CDM found or invalid CDM
    2 = usage error
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Tuple

# Try to import pywidevine for validation
try:
    from pywidevine.device import Device, DeviceTypes
    PYWIDEVINE_AVAILABLE = True
except ImportError:
    PYWIDEVINE_AVAILABLE = False
    Device = None
    DeviceTypes = None


# Default cache directory (matches src/thuis/cdm.py)
DEFAULT_CDM_CACHE = Path.home() / ".thuis" / "cdm"
DEFAULT_CDM_FILENAME = "widevine_l3_android.wvd"


def get_cdm_cache_dir() -> Path:
    """Get the CDM cache directory from WVD_CDM_PATH env var or default."""
    env_path = os.getenv("WVD_CDM_PATH")
    if env_path:
        path = Path(env_path).expanduser().resolve()
    else:
        path = DEFAULT_CDM_CACHE
    return path


def find_wvd_files(cache_dir: Path) -> List[Path]:
    """Find all .wvd files in the cache directory."""
    if not cache_dir.exists():
        return []
    return list(cache_dir.glob("*.wvd"))


def validate_wvd(wvd_path: Path) -> Tuple[bool, str]:
    """
    Validate a .wvd file using pywidevine.
    
    Returns:
        (is_valid, details_string)
    """
    if not PYWIDEVINE_AVAILABLE:
        return False, "pywidevine not installed (pip install pywidevine)"
    
    try:
        device = Device.load(str(wvd_path))
        
        # Check it's an L3 ANDROID device
        if device.type != DeviceTypes.ANDROID:
            return False, f"CDM type is {device.type}, expected ANDROID"
        
        if device.security_level != 3:
            return False, f"CDM security_level is {device.security_level}, expected 3 (L3)"
        
        details = (
            f"Valid L3 ANDROID CDM\n"
            f"  Type: {device.type}\n"
            f"  Security Level: {device.security_level} (L3)\n"
            f"  System ID: {device.system_id}\n"
            f"  Client ID: {device.client_id.hex()[:16]}..."
        )
        return True, details
        
    except Exception as e:
        return False, f"Validation error: {e}"


def print_extraction_guide():
    """Print condensed step-by-step extraction guide from REQUIREMENTS.md Section 3.3."""
    guide = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║              WIDEVINE L3 CDM (.wvd) MANUAL EXTRACTION GUIDE                  ║
║                    (Condensed from REQUIREMENTS.md §3.3)                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

⚠️  LEGAL NOTICE: This guide is for educational/interoperability purposes only.
    You are responsible for complying with applicable laws in your jurisdiction.
    See REQUIREMENTS.md §8 for full disclaimer.

┌──────────────────────────────────────────────────────────────────────────────┐
│ PREREQUISITES                                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ • Rooted Android device (Magisk / KernelSU)                                  │
│ • ADB access with root shell (adb root && adb shell)                         │
│ • Frida server running on device (matching arch: arm64/arm/x86)              │
│ • Python 3.8+ with frida-tools and pywidevine                                │
│                                                                              │
│ Install Frida tools on host:                                                 │
│   pip install frida-tools                                                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ METHOD 1: wvdumper (RECOMMENDED)                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1. On host: Clone and install wvdumper                                       │
│    git clone https://github.com/keyset/wvdumper                              │
│    cd wvdumper && pip install -r requirements.txt                            │
│                                                                              │
│ 2. On device (via ADB): Push and start Frida server                          │
│    adb push frida-server /data/local/tmp/                                    │
│    adb shell chmod 755 /data/local/tmp/frida-server                          │
│    adb shell /data/local/tmp/frida-server &                                  │
│                                                                              │
│ 3. Run wvdumper targeting Widevine process                                   │
│    python wvdumper.py -p com.google.android.gms -o my_cdm.wvd                │
│    # Older devices may use: -p com.widevine                                  │
│                                                                              │
│ 4. Pull the extracted CDM to host                                            │
│    adb pull /data/local/tmp/my_cdm.wvd ~/.thuis/cdm/widevine_l3_android.wvd  │
│                                                                              │
│ 5. Validate (optional, tool does this automatically)                         │
│    python -c "from pywidevine.device import Device;                          │
│        d=Device.load('~/.thuis/cdm/widevine_l3_android.wvd');                │
│        print(d.type, d.security_level)"                                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ METHOD 2: Direct Frida Script (ALTERNATIVE)                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Requires a Frida script that hooks CdmFactory.create() and dumps device blob │
│                                                                              │
│   frida -U -f com.google.android.gms -l extract_cdm.js --no-pause            │
│                                                                              │
│ See wvdumper source for reference implementation of the hook.                │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ IMPORTANT NOTES                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ • Tool ONLY supports L3 ANDROID CDMs (security_level=3)                     │
│ • L1 hardware-backed CDMs CANNOT be extracted (TEE-protected)               │
│ • Some Xiaomi devices have extractable L1 CDMs (security_level=1)           │
│   → Tool will REJECT these (validates security_level == 3)                  │
│ • Community CDMs (nicko170/video-devices) are auto-fetched by default       │
│   → Higher revocation risk; consider extracting your own for production     │
│ • NEVER commit .wvd files to any repository (gitignored by default)         │
│ • Custom cache location: set WVD_CDM_PATH=/path/to/cdm in .env or shell     │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ QUICK VALIDATION COMMANDS                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ # Auto-fetch & validate (default behavior)                                   │
│ python -m thuis.cdm                                                          │
│                                                                              │
│ # Manual validation of existing CDM                                          │
│ python scripts/extract_cdm.py                                                │
│                                                                              │
│ # Check CDM details                                                          │
│ python -c "from pywidevine.device import Device;                             │
│     d=Device.load('~/.thuis/cdm/widevine_l3_android.wvd');                   │
│     print(f'Type: {d.type}, Level: {d.security_level}, ID: {d.system_id}')"
└──────────────────────────────────────────────────────────────────────────────┘
"""
    print(guide)


def validate_cache(cache_dir: Path, verbose: bool = True) -> Tuple[int, Optional[Path]]:
    """
    Validate all .wvd files in cache directory.
    
    Returns:
        (exit_code, valid_wvd_path)
        exit_code: 0 = valid found, 1 = none valid
        valid_wvd_path: Path to first valid .wvd, or None
    """
    wvd_files = find_wvd_files(cache_dir)
    
    if verbose:
        print(f"🔍 Scanning CDM cache: {cache_dir}")
        print(f"   WVD_CDM_PATH env: {os.getenv('WVD_CDM_PATH', '(not set, using default)')}")
        print()
    
    if not wvd_files:
        if verbose:
            print("❌ No .wvd files found in cache.")
        return 1, None
    
    if verbose:
        print(f"📁 Found {len(wvd_files)} .wvd file(s):")
        for wvd in wvd_files:
            print(f"   • {wvd.name} ({wvd.stat().st_size} bytes)")
        print()
    
    valid_wvd = None
    for wvd_path in wvd_files:
        if verbose:
            print(f"🔎 Validating: {wvd_path.name}")
        
        is_valid, details = validate_wvd(wvd_path)
        
        if is_valid:
            if verbose:
                print(f"   ✅ VALID")
                print(f"   {details}")
            valid_wvd = wvd_path
            break
        else:
            if verbose:
                print(f"   ❌ INVALID: {details}")
    
    if verbose:
        print()
    
    if valid_wvd:
        if verbose:
            print(f"✅ Valid CDM found: {valid_wvd}")
        return 0, valid_wvd
    else:
        if verbose:
            print("❌ No valid L3 ANDROID CDM found in cache.")
        return 1, None


def main():
    parser = argparse.ArgumentParser(
        description="Widevine L3 CDM Extraction Helper - Validate cache + print extraction guide",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/extract_cdm.py           # Validate cache, print guide if missing/invalid
  python scripts/extract_cdm.py --guide   # Print extraction guide only
  python scripts/extract_cdm.py -q        # Quiet validation (exit code only)

Exit codes:
  0 = Valid L3 ANDROID CDM found in cache
  1 = No valid CDM found (missing or invalid)
  2 = Usage error
        """
    )
    parser.add_argument(
        "-g", "--guide",
        action="store_true",
        help="Print extraction guide only (skip cache validation)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode - only exit code, no output (unless --guide)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Override CDM cache directory (default: ~/.thuis/cdm/ or WVD_CDM_PATH)"
    )
    
    args = parser.parse_args()
    
    # Handle --guide flag
    if args.guide:
        print_extraction_guide()
        return 0
    
    # Determine cache directory
    if args.cache_dir:
        cache_dir = args.cache_dir.expanduser().resolve()
    else:
        cache_dir = get_cdm_cache_dir()
    
    # Validate cache
    exit_code, valid_wvd = validate_cache(cache_dir, verbose=not args.quiet)
    
    # Print guide if validation failed and not quiet
    if exit_code != 0 and not args.quiet:
        print()
        print_extraction_guide()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())