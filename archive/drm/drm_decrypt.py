#!/usr/bin/env python3
"""
C4 DRM Decrypt Worker for VRT MAX.

Core DRM decryption pipeline:
- PSSH extraction from DASH init segment
- pywidevine license acquisition (VUDRM proxy with X-VUDRM-TOKEN)
- N_m3u8DL-RE download + decrypt + mux to playable MP4
- Graceful degradation on any failure
"""

import os
import sys
import logging
import tempfile
import shutil
import subprocess
import base64
import struct
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Import pymp4 at module level for test patching
try:
    import pymp4.parser as pymp4_parser
except ImportError:
    pymp4_parser = None

logger = logging.getLogger(__name__)

# Constants
WIDEVINE_SYSTEM_ID = "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
WIDEVINE_SYSTEM_ID_BYTES = bytes.fromhex(WIDEVINE_SYSTEM_ID.replace("-", ""))

VUDRM_LICENSE_PROXY = "https://widevine-proxy.drm.technology/proxy"
VUDRM_CERT_URL = "https://widevine-proxy.drm.technology/proxy"

# N_m3u8DL-RE decryption engine fallback chain
DECRYPTION_ENGINES = ["MP4DECRYPT", "SHAKA_PACKAGER", "FFMPEG"]

# Required external binaries
REQUIRED_BINARIES = {
    "MP4DECRYPT": "mp4decrypt",
    "SHAKA_PACKAGER": "shaka-packager",
    "FFMPEG": "ffmpeg",
}


class DrmDecryptError(Exception):
    """Base exception for DRM decryption failures."""
    pass


class PsshExtractionError(DrmDecryptError):
    """Failed to extract PSSH from init segment."""
    pass


class LicenseAcquisitionError(DrmDecryptError):
    """Failed to acquire license from VUDRM proxy."""
    pass


class DecryptionEngineError(DrmDecryptError):
    """No suitable decryption engine found."""
    pass


class N_m3u8DL_RE_Error(DrmDecryptError):
    """N_m3u8DL-RE execution failed."""
    pass


def find_binary(name: str) -> Optional[str]:
    """Find a binary in PATH or common locations."""
    # Check PATH first
    path = shutil.which(name)
    if path:
        return path
    
    # Check common locations
    common_paths = [
        f"/usr/local/bin/{name}",
        f"/opt/homebrew/bin/{name}",
        f"C:\\Program Files\\{name}.exe",
        f"C:\\Program Files (x86)\\{name}.exe",
    ]
    for p in common_paths:
        if Path(p).exists():
            return p
    
    return None


def load_keys_from_file(key_file_path: str) -> Dict[str, str]:
    """Load KID:KEY pairs from a JSON file."""
    import json
    path = Path(key_file_path)
    if not path.exists():
        raise DrmDecryptError(f"Key file not found: {key_file_path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for k, v in data.items():
        result[k.lower().replace("-", "")] = v.lower().replace("-", "")
    return result


def load_keys_from_source(
    provider: str,
    vudrm_token: Optional[str] = None,
    pssh_bytes: Optional[bytes] = None,
    cdm_path: Optional[str] = None,
    key_file: Optional[str] = None,
    cli_keys: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Resolve keys from selected provider (cdm, file, cli)."""
    if provider == "cli" and cli_keys:
        return cli_keys
    if provider == "file" and key_file:
        return load_keys_from_file(key_file)
    if not cdm_path:
        from thuis.cdm import ensure_cdm
        cdm_path = ensure_cdm()
    if not cdm_path or not vudrm_token or not pssh_bytes:
        raise DrmDecryptError("CDM provider requires vudrm_token, pssh_bytes, and valid cdm_path")
    return acquire_license(vudrm_token, pssh_bytes, cdm_path)


def get_available_decryption_engine() -> Tuple[str, str]:
    """
    Find the best available decryption engine.
    
    Returns:
        Tuple of (engine_name, binary_path).
        
    Raises:
        DecryptionEngineError: If no engine is available.
    """
    for engine in DECRYPTION_ENGINES:
        binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
        binary_path = find_binary(binary_name)
        if binary_path:
            logger.info("Using decryption engine: %s (%s)", engine, binary_path)
            return engine, binary_path
    
    # Build error message with all tried binaries
    tried = []
    for engine in DECRYPTION_ENGINES:
        binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
        tried.append(f"{engine} ({binary_name})")
    
    raise DecryptionEngineError(
        f"No decryption engine found. Tried: {', '.join(tried)}. "
        f"Install one of: mp4decrypt (Bento4), shaka-packager, or ffmpeg"
    )


def download_init_segment(init_url: str, timeout: int = 30) -> bytes:
    """
    Download the DASH init segment (MP4 init box).
    
    Args:
        init_url: URL to the init segment (.m3u8 or .mp4 init)
        timeout: Request timeout in seconds.
        
    Returns:
        Raw bytes of the init segment.
        
    Raises:
        PsshExtractionError: On download failure.
    """
    try:
        req = Request(init_url, headers={"User-Agent": "thuis-drm-decrypt/1.0"})
        with urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise PsshExtractionError(f"Init segment download failed: HTTP {response.status}")
            return response.read()
    except (URLError, HTTPError, OSError) as e:
        raise PsshExtractionError(f"Failed to download init segment: {e}")


def extract_pssh_from_mp4(init_data: bytes) -> bytes:
    """
    Extract Widevine PSSH box from MP4 init segment.
    
    Parses MP4 boxes (moov -> pssh) to find Widevine system ID.
    Uses pymp4 for robust parsing.
    
    Args:
        init_data: Raw bytes of the init segment.
        
    Returns:
        Raw PSSH box bytes (including box header).
        
    Raises:
        PsshExtractionError: If no Widevine PSSH found.
    """
    if pymp4_parser is None:
        raise PsshExtractionError("pymp4 not available for MP4 parsing")
    
    # Parse the MP4
    try:
        boxes = pymp4_parser.MP4.parse(init_data)
    except Exception as e:
        raise PsshExtractionError(f"Failed to parse MP4 init segment: {e}")
    
    # Find all pssh boxes
    pssh_boxes = []
    for box in boxes:
        if box.type == b'pssh':
            pssh_boxes.append(box)
    
    # Search recursively in nested boxes
    def find_pssh_recursive(box_list):
        found = []
        for box in box_list:
            if box.type == b'pssh':
                found.append(box)
            # Check children if container box
            if hasattr(box, 'children') and box.children:
                found.extend(find_pssh_recursive(box.children))
        return found
    
    all_pssh = find_pssh_recursive(boxes)
    
    # Find Widevine PSSH (system ID = edef8ba9-79d6-4ace-a3c8-27dcd51d21ed)
    for pssh in all_pssh:
        if hasattr(pssh, 'system_id'):
            # pymp4 returns system_id as UUID bytes
            if pssh.system_id == WIDEVINE_SYSTEM_ID_BYTES:
                # Return the full box data
                return pssh.data if hasattr(pssh, 'data') else pssh.raw_data
    
    raise PsshExtractionError(
        f"No Widevine PSSH found in init segment. "
        f"Found {len(all_pssh)} PSSH box(es), none with Widevine system ID."
    )


def extract_pssh_from_init(init_url: str) -> bytes:
    """
    Download init segment and extract Widevine PSSH.
    
    Args:
        init_url: URL to the init segment.
        
    Returns:
        Raw PSSH box bytes.
    """
    logger.info("Downloading init segment from %s", init_url)
    init_data = download_init_segment(init_url)
    
    logger.debug("Init segment size: %d bytes", len(init_data))
    pssh = extract_pssh_from_mp4(init_data)
    
    logger.info("Extracted Widevine PSSH (%d bytes)", len(pssh))
    return pssh


def acquire_license(
    vudrm_token: str,
    pssh_bytes: bytes,
    cdm_path: str
) -> Dict[str, str]:
    """
    Acquire license keys via pywidevine using VUDRM proxy.
    
    Flow:
    1. Load CDM from .wvd file
    2. Open session
    3. Get service certificate from proxy
    4. Set service certificate
    5. Generate license challenge with PSSH
    6. POST challenge to proxy with X-VUDRM-TOKEN header
    7. Parse license response
    8. Extract CONTENT keys
    
    Args:
        vudrm_token: VUDRM token from yt-dlp metadata.
        pssh_bytes: Raw PSSH box bytes.
        cdm_path: Path to validated .wvd file.
        
    Returns:
        Dict mapping KID (hex) -> KEY (hex).
        
    Raises:
        LicenseAcquisitionError: On any step failure.
    """
    try:
        from pywidevine.device import Device
        from pywidevine.cdm import Cdm
        from pywidevine.pssh import PSSH
    except ImportError as e:
        raise LicenseAcquisitionError(f"pywidevine not available: {e}")
    
    # Parse PSSH
    try:
        pssh = PSSH(pssh_bytes)
    except Exception as e:
        raise LicenseAcquisitionError(f"Failed to parse PSSH: {e}")
    
    logger.debug("PSSH system_id: %s, key_ids: %s", pssh.system_id, pssh.key_ids)
    
    # Load device and create CDM
    try:
        device = Device.load(cdm_path)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()
    except Exception as e:
        raise LicenseAcquisitionError(f"Failed to initialize CDM: {e}")
    
    try:
        # Step 1: Get service certificate from proxy (POST empty challenge)
        logger.debug("Requesting service certificate from %s", VUDRM_CERT_URL)
        try:
            cert_req = Request(VUDRM_CERT_URL, data=b"", method="POST")
            cert_req.add_header("Content-Type", "application/octet-stream")
            with urlopen(cert_req, timeout=30) as resp:
                if resp.status != 200:
                    raise LicenseAcquisitionError(f"Service certificate request failed: HTTP {resp.status}")
                service_cert = resp.read()
        except (URLError, HTTPError, OSError) as e:
            raise LicenseAcquisitionError(f"Service certificate request failed: {e}")
        
        logger.debug("Received service certificate (%d bytes)", len(service_cert))
        
        # Step 2: Set service certificate
        try:
            cdm.set_service_certificate(session_id, service_cert)
        except Exception as e:
            raise LicenseAcquisitionError(f"Failed to set service certificate: {e}")
        
        # Step 3: Generate license challenge
        logger.debug("Generating license challenge (STREAMING, privacy_mode=True)")
        try:
            challenge = cdm.get_license_challenge(
                session_id,
                pssh,
                license_type="STREAMING",
                privacy_mode=True
            )
        except Exception as e:
            raise LicenseAcquisitionError(f"Failed to generate license challenge: {e}")
        
        # Step 4: POST challenge to VUDRM proxy with X-VUDRM-TOKEN
        logger.debug("Requesting license from VUDRM proxy")
        try:
            license_req = Request(
                VUDRM_LICENSE_PROXY,
                data=challenge,
                method="POST"
            )
            license_req.add_header("Content-Type", "application/octet-stream")
            license_req.add_header("X-VUDRM-TOKEN", vudrm_token)
            
            with urlopen(license_req, timeout=30) as resp:
                if resp.status != 200:
                    raise LicenseAcquisitionError(f"License request failed: HTTP {resp.status}")
                license_response = resp.read()
        except (URLError, HTTPError, OSError) as e:
            raise LicenseAcquisitionError(f"License request failed: {e}")
        
        logger.debug("Received license response (%d bytes)", len(license_response))
        
        # Step 5: Parse license
        try:
            cdm.parse_license(session_id, license_response)
        except Exception as e:
            raise LicenseAcquisitionError(f"Failed to parse license: {e}")
        
        # Step 6: Extract CONTENT keys
        try:
            keys = cdm.get_keys(session_id, "CONTENT")
        except Exception as e:
            raise LicenseAcquisitionError(f"Failed to get keys: {e}")
        
        # Convert to dict: KID hex -> KEY hex
        key_dict = {}
        for key in keys:
            kid_hex = key.kid.hex()
            key_hex = key.key.hex()
            key_dict[kid_hex] = key_hex
            logger.info("Got key: KID=%s", kid_hex)
        
        if not key_dict:
            raise LicenseAcquisitionError("No CONTENT keys returned from license")
        
        return key_dict
        
    finally:
        # Always close session
        try:
            cdm.close(session_id)
        except Exception:
            pass


def build_n_m3u8dl_re_cmd(
    mpd_url: str,
    keys: Dict[str, str],
    output_dir: Path,
    output_name: str,
    engine: str
) -> List[str]:
    """
    Build N_m3u8DL-RE command line.
    
    Args:
        mpd_url: MPD manifest URL.
        keys: Dict of KID -> KEY (hex strings).
        output_dir: Output directory.
        output_name: Base filename (without extension).
        engine: Decryption engine name.
        
    Returns:
        Command as list of strings.
    """
    cmd = ["N_m3u8DL-RE", mpd_url]
    
    # Add keys
    for kid, key in keys.items():
        cmd.extend(["--key", f"{kid}:{key}"])
    
    # Output options
    cmd.extend([
        "--save-dir", str(output_dir),
        "--save-name", output_name,
        "--auto-select",
        "--decryption-engine", engine,
        # Disable logging to stdout to avoid noise
        "--log-level", "ERROR",
    ])
    
    return cmd


def run_n_m3u8dl_re(cmd: List[str], timeout: int = 600) -> Path:
    """
    Run N_m3u8DL-RE and return the output file path.
    
    Args:
        cmd: Command list.
        timeout: Process timeout in seconds.
        
    Returns:
        Path to the output MP4 file.
        
    Raises:
        N_m3u8DL_RE_Error: On execution failure.
    """
    logger.info("Running N_m3u8DL-RE: %s", " ".join(cmd))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
    except subprocess.TimeoutExpired:
        raise N_m3u8DL_RE_Error(f"N_m3u8DL-RE timed out after {timeout}s")
    except FileNotFoundError:
        raise N_m3u8DL_RE_Error("N_m3u8DL-RE not found in PATH")
    except Exception as e:
        raise N_m3u8DL_RE_Error(f"Failed to start N_m3u8DL-RE: {e}")
    
    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "no stderr"
        stdout = result.stdout.strip() if result.stdout else "no stdout"
        raise N_m3u8DL_RE_Error(
            f"N_m3u8DL-RE exited with code {result.returncode}. "
            f"stdout: {stdout[:500]} stderr: {stderr[:500]}"
        )
    
    # Find the output file (should be output_name.mp4 in output_dir)
    output_dir = Path(cmd[cmd.index("--save-dir") + 1])
    output_name = cmd[cmd.index("--save-name") + 1]
    
    output_files = list(output_dir.glob(f"{output_name}*.mp4"))
    if not output_files:
        # Try without extension
        output_files = list(output_dir.glob(f"{output_name}*"))
        output_files = [f for f in output_files if f.suffix in ('.mp4', '.mkv', '.ts')]
    
    if not output_files:
        raise N_m3u8DL_RE_Error(f"No output file found in {output_dir}")
    
    # Return the largest file (likely the main muxed output)
    output_file = max(output_files, key=lambda f: f.stat().st_size)
    logger.info("N_m3u8DL-RE produced: %s (%d bytes)", output_file, output_file.stat().st_size)
    
    return output_file


def decrypt_drm_content(
    vudrm_token: str,
    mpd_url: str,
    init_url: str,
    output_dir: Path,
    output_name: str,
    cdm_path: Optional[str] = None,
    key_file: Optional[str] = None,
    cli_keys: Optional[Dict[str, str]] = None,
    key_provider: str = "cdm",
) -> Optional[Path]:
    """
    Main DRM decryption pipeline.
    
    Args:
        vudrm_token: VUDRM token from yt-dlp metadata.
        mpd_url: MPD manifest URL.
        init_url: Init segment URL (for PSSH extraction).
        output_dir: Output directory.
        output_name: Base output filename.
        cdm_path: Path to CDM .wvd file (auto-fetched if None).
        
    Returns:
        Path to decrypted MP4 on success, None on failure (with error logged).
    """
    # Ensure CDM is available
    if cdm_path is None:
        from thuis.cdm import ensure_cdm
        cdm_path = ensure_cdm()
    
    if not cdm_path:
        logger.error("No valid CDM available (auto-fetch failed or disabled)")
        return None
    
    logger.info("Using CDM: %s", cdm_path)
    
    # Step 1: Extract PSSH from init segment
    try:
        pssh = extract_pssh_from_init(init_url)
    except PsshExtractionError as e:
        logger.error("PSSH extraction failed: %s", e)
        return None
    
    # Step 2: Resolve content keys (CDM or external provider)
    try:
        keys = load_keys_from_source(
            provider=key_provider,
            vudrm_token=vudrm_token,
            pssh_bytes=pssh,
            cdm_path=cdm_path,
            key_file=key_file,
            cli_keys=cli_keys,
        )
    except DrmDecryptError as e:
        logger.error("Key acquisition failed: %s", e)
        return None
    
    logger.info("Acquired %d content key(s)", len(keys))
    
    # Step 3: Find decryption engine
    try:
        engine, binary_path = get_available_decryption_engine()
    except DecryptionEngineError as e:
        logger.error("No decryption engine available: %s", e)
        return None
    
    # Step 4: Run N_m3u8DL-RE with keys
    try:
        with tempfile.TemporaryDirectory(prefix="thuis_drm_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            cmd = build_n_m3u8dl_re_cmd(mpd_url, keys, tmpdir_path, output_name, engine)
            output_file = run_n_m3u8dl_re(cmd)
            
            # Move to final destination
            final_path = output_dir / f"{output_name}.mp4"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if final_path.exists():
                # Backup existing
                backup = final_path.with_suffix(f".mp4.bak")
                if backup.exists():
                    backup.unlink()
                final_path.rename(backup)
            
            shutil.move(str(output_file), str(final_path))
            logger.info("Decrypted file saved to: %s", final_path)
            
            return final_path
            
    except N_m3u8DL_RE_Error as e:
        logger.error("N_m3u8DL-RE failed: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error during decryption: %s (%s)", e, type(e).__name__)
        return None


def main():
    """CLI entry point for testing."""
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    parser = argparse.ArgumentParser(description="DRM decrypt worker")
    parser.add_argument("--vudrm-token", required=True, help="VUDRM token")
    parser.add_argument("--mpd-url", required=True, help="MPD manifest URL")
    parser.add_argument("--init-url", required=True, help="Init segment URL")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output directory")
    parser.add_argument("--output-name", required=True, help="Output filename (no extension)")
    parser.add_argument("--cdm-path", help="Path to .wvd file (auto-fetch if omitted)")
    
    args = parser.parse_args()
    
    result = decrypt_drm_content(
        vudrm_token=args.vudrm_token,
        mpd_url=args.mpd_url,
        init_url=args.init_url,
        output_dir=args.output_dir,
        output_name=args.output_name,
        cdm_path=args.cdm_path,
    )
    
    if result:
        print(f"SUCCESS: {result}")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()