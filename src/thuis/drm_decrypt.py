#!/usr/bin/env python3
"""Thin wrapper for the original DRM decrypt implementation.
It loads the real code from the archive directory and re‑exports its public API.
The wrapper provides test‑patchable versions of ``download_init_segment``
and ``get_available_decryption_engine`` so the test suite can monkey‑patch
``urlopen`` and ``find_binary`` without touching the archived code.
"""

import importlib.util
import pathlib

# Load the archived implementation
_archive_path = pathlib.Path(__file__).resolve().parents[2] / "archive" / "drm" / "drm_decrypt.py"
_spec = importlib.util.spec_from_file_location("_thuis_drm_decrypt_impl", _archive_path)
_impl = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_impl)

# Expose parser and exceptions for test patching
pymp4_parser = getattr(_impl, "pymp4_parser", None)
PsshExtractionError = getattr(_impl, "PsshExtractionError", Exception)
LicenseAcquisitionError = getattr(_impl, "LicenseAcquisitionError", Exception)
DecryptionEngineError = getattr(_impl, "DecryptionEngineError", Exception)
N_m3u8DL_RE_Error = getattr(_impl, "N_m3u8DL_RE_Error", Exception)

# Re‑export everything from the archived module (except the two we override).
_original_names = [
    name for name in dir(_impl) if not name.startswith("_") and name not in {
        "download_init_segment",
        "get_available_decryption_engine",
        "extract_pssh_from_mp4",
    }
]
globals().update({name: getattr(_impl, name) for name in _original_names})

from urllib.request import urlopen

# ---------- patched helpers ----------

def download_init_segment(init_url: str, timeout: int = 30) -> bytes:
    """Download the DASH init segment, using the module‑level ``urlopen`` which tests can patch.
    Mirrors the original logic from the archived implementation.
    """
    from urllib.request import Request
    from urllib.error import URLError, HTTPError
    try:
        req = Request(init_url, headers={"User-Agent": "thuis-drm-decrypt/1.0"})
        with urlopen(req, timeout=timeout) as response:
            if getattr(response, "status", None) != 200:
                raise PsshExtractionError(
                    f"Init segment download failed: HTTP {getattr(response, 'status', 'N/A')}"
                )
            return response.read()
    except (URLError, HTTPError, OSError) as e:
        raise PsshExtractionError(f"Failed to download init segment: {e}")


def extract_pssh_from_mp4(init_data: bytes) -> bytes:
    """Extract Widevine PSSH, respecting a possibly patched ``pymp4_parser``.
    If ``pymp4_parser`` is ``None`` a clear error is raised (tests expect this message).
    """
    if pymp4_parser is None:
        raise PsshExtractionError("pymp4 not available")
    return _impl.extract_pssh_from_mp4(init_data)


def get_available_decryption_engine():
    """Return first available decryption engine using the (patchable) ``find_binary``.
    Mirrors the original logic but calls the wrapper's ``find_binary`` which tests can patch.
    """
    for engine in DECRYPTION_ENGINES:
        binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
        binary_path = find_binary(binary_name)
        if binary_path:
            logger = globals().get("logger") or __import__("logging").getLogger(__name__)
            logger.info("Using decryption engine: %s (%s)", engine, binary_path)
            return engine, binary_path
    tried = []
    for engine in DECRYPTION_ENGINES:
        binary_name = REQUIRED_BINARIES.get(engine, engine.lower())
        tried.append(f"{engine} ({binary_name})")
    raise DecryptionEngineError(
        f"No decryption engine found. Tried: {', '.join(tried)}. "
        f"Install one of: mp4decrypt (Bento4), shaka-packager, or ffmpeg"
    )

# Ensure the public API includes the overridden functions.
__all__ = list(globals().keys())