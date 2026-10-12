#!/usr/bin/env python3
"""
C6 CDM Provisioner for VRT MAX DRM pipeline.

Auto-fetches, assembles, and validates L3 ANDROID Widevine CDM (.wvd file).
Uses pywidevine for validation. Gracefully degrades on any failure.
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import zipfile

logger = logging.getLogger(__name__)

# Known L3 ANDROID CDM sources (video-help hosts)
# These are pre-built .wvd files or zip archives with private_key.pem + client_id.bin
CDM_SOURCES = [
    "https://github.com/nicko170/video-devices/raw/main/wvd/google_widevine_l3.wvd",
    "https://github.com/nicko170/video-devices/raw/main/wvd/widevine_l3_android.wvd",
    # Fallback: zip archives with key material
    "https://github.com/nicko170/video-devices/raw/main/wvd/google_widevine_l3.zip",
    "https://github.com/nicko170/video-devices/raw/main/wvd/widevine_l3_android.zip",
]

# Default cache directory
DEFAULT_CDM_CACHE = Path.home() / ".thuis" / "cdm"
DEFAULT_CDM_FILENAME = "widevine_l3_android.wvd"


def get_cdm_cache_dir() -> Path:
    """
    Get the CDM cache directory from WVD_CDM_PATH env var or default.
    
    Returns:
        Path to the CDM cache directory (created if needed).
    """
    env_path = os.getenv("WVD_CDM_PATH")
    if env_path:
        path = Path(env_path).expanduser().resolve()
    else:
        path = DEFAULT_CDM_CACHE
    
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cdm_path() -> Path:
    """
    Get the full path to the cached CDM file.
    
    Returns:
        Path to the .wvd file in the cache directory.
    """
    return get_cdm_cache_dir() / DEFAULT_CDM_FILENAME


def validate_cdm(wvd_path: Path) -> bool:
    """
    Validate a CDM file using pywidevine's Device.load().
    
    Args:
        wvd_path: Path to the .wvd file to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        from pywidevine.device import Device
        device = Device.load(str(wvd_path))
        # Check it's an L3 ANDROID device
        from pywidevine.device import DeviceTypes
        if device.type != DeviceTypes.ANDROID:
            logger.warning("CDM is not ANDROID type: %s", device.type)
            return False
        if device.security_level != 3:
            logger.warning("CDM is not L3 (security_level=%d)", device.security_level)
            return False
        logger.debug("CDM validated: type=%s, level=%d, system_id=%s", 
                     device.type, device.security_level, device.system_id)
        return True
    except Exception as e:
        logger.debug("CDM validation failed: %s", e)
        return False


def download_file(url: str, dest: Path, timeout: int = 30) -> bool:
    """
    Download a file from URL to destination.
    
    Args:
        url: Source URL.
        dest: Destination path.
        timeout: Request timeout in seconds.
        
    Returns:
        True on success, False on failure.
    """
    try:
        req = Request(url, headers={"User-Agent": "thuis-cdm-provisioner/1.0"})
        with urlopen(req, timeout=timeout) as response:
            dest.write_bytes(response.read())
        return True
    except (URLError, HTTPError, OSError) as e:
        logger.debug("Download failed for %s: %s", url, e)
        return False


def extract_wvd_from_zip(zip_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Extract a .wvd file from a zip archive.
    
    Looks for .wvd files or private_key.pem + client_id.bin pairs.
    
    Args:
        zip_path: Path to the zip file.
        output_dir: Directory to extract to.
        
    Returns:
        Path to the extracted/assembled .wvd file, or None on failure.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # First, check for pre-built .wvd
            for name in zf.namelist():
                if name.endswith('.wvd'):
                    wvd_path = output_dir / "extracted.wvd"
                    with zf.open(name) as src, wvd_path.open('wb') as dst:
                        dst.write(src.read())
                    return wvd_path
            
            # If no .wvd, look for key material to assemble
            has_key = any(n.endswith('private_key.pem') for n in zf.namelist())
            has_client = any(n.endswith('client_id.bin') for n in zf.namelist())
            
            if has_key and has_client:
                # Extract key material
                key_path = output_dir / "private_key.pem"
                client_path = output_dir / "client_id.bin"
                
                for name in zf.namelist():
                    if name.endswith('private_key.pem'):
                        with zf.open(name) as src, key_path.open('wb') as dst:
                            dst.write(src.read())
                    elif name.endswith('client_id.bin'):
                        with zf.open(name) as src, client_path.open('wb') as dst:
                            dst.write(src.read())
                
                # Assemble .wvd using pywidevine
                wvd_path = assemble_wvd(key_path, client_path, output_dir / "assembled.wvd")
                return wvd_path
                
    except Exception as e:
        logger.debug("Zip extraction failed: %s", e)
    
    return None


def assemble_wvd(key_path: Path, client_path: Path, output_path: Path) -> Optional[Path]:
    """
    Assemble a .wvd file from private_key.pem and client_id.bin using pywidevine.
    
    Args:
        key_path: Path to private_key.pem.
        client_path: Path to client_id.bin.
        output_path: Output path for the .wvd file.
        
    Returns:
        Path to the assembled .wvd file, or None on failure.
    """
    try:
        from pywidevine.device import Device, DeviceTypes
        
        device = Device(
            type_=DeviceTypes.ANDROID,
            security_level=3,
            private_key=key_path.read_bytes(),
            client_id=client_path.read_bytes()
        )
        device.dump(str(output_path))
        return output_path
    except Exception as e:
        logger.debug("WVD assembly failed: %s", e)
        return None


def fetch_cdm() -> Optional[Path]:
    """
    Fetch a CDM from known sources.
    
    Tries each source in order until one succeeds.
    
    Returns:
        Path to the fetched/assembled .wvd file, or None on total failure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        for url in CDM_SOURCES:
            logger.info("Trying CDM source: %s", url)
            
            # Determine filename from URL
            filename = url.split('/')[-1]
            local_path = tmpdir_path / filename
            
            if not download_file(url, local_path):
                continue
            
            # If it's already a .wvd, validate and return
            if filename.endswith('.wvd'):
                if validate_cdm(local_path):
                    logger.info("Successfully fetched and validated CDM from %s", url)
                    return local_path
                else:
                    logger.debug("Downloaded .wvd failed validation: %s", url)
                    continue
            
            # If it's a zip, try to extract/assemble
            if filename.endswith('.zip'):
                wvd_path = extract_wvd_from_zip(local_path, tmpdir_path)
                if wvd_path and validate_cdm(wvd_path):
                    logger.info("Successfully extracted and validated CDM from %s", url)
                    return wvd_path
                else:
                    logger.debug("Zip extraction/validation failed: %s", url)
                    continue
    
    return None


def ensure_cdm() -> Optional[str]:
    """
    Ensure a valid L3 ANDROID Widevine CDM is available.
    
    This is the primary API for the DRM pipeline.
    1. Checks WVD_CDM_PATH env var (or default cache) for existing CDM
    2. Validates existing CDM with pywidevine
    3. Auto-fetches from known sources if missing or invalid
    4. Caches the validated CDM
    5. Returns path to the .wvd file, or None on failure (with warning logged)
    
    Returns:
        Path to validated .wvd file as string, or None if unavailable.
    """
    cdm_path = get_cdm_path()
    
    # Step 1: Check cache
    if cdm_path.exists():
        logger.debug("Found cached CDM at %s", cdm_path)
        if validate_cdm(cdm_path):
            logger.info("Using cached CDM: %s", cdm_path)
            return str(cdm_path)
        else:
            logger.warning("Cached CDM failed validation, will re-fetch")
            cdm_path.unlink(missing_ok=True)
    
    # Step 2: Auto-fetch
    logger.info("Auto-fetching L3 ANDROID Widevine CDM...")
    fetched_wvd = fetch_cdm()
    
    if fetched_wvd is None:
        logger.warning(
            "Failed to auto-fetch CDM from all sources. DRM decryption will be unavailable. "
            "See docs/REQUIREMENTS.md and run python scripts/extract_cdm.py to extract a CDM from your Android device."
        )
        return None
    
    # Step 3: Cache the fetched CDM
    try:
        shutil.copy2(fetched_wvd, cdm_path)
        logger.info("Cached CDM to %s", cdm_path)
    except Exception as e:
        logger.warning("Failed to cache CDM: %s", e)
        # Still return the temp path if copy failed but validation passed
        return str(fetched_wvd)
    
    # Final validation of cached copy
    if validate_cdm(cdm_path):
        return str(cdm_path)
    else:
        logger.warning("Cached CDM copy failed validation")
        cdm_path.unlink(missing_ok=True)
        return None


def main():
    """CLI entry point for testing."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    cdm_path = ensure_cdm()
    if cdm_path:
        print(f"CDM ready: {cdm_path}")
        sys.exit(0)
    else:
        print("CDM unavailable")
        sys.exit(1)


if __name__ == "__main__":
    main()