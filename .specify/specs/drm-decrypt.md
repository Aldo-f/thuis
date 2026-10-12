# DRM Decrypt Specification

## Module
`src/thuis/drm_decrypt.py` — Core DRM decryption pipeline

## Function
```python
def decrypt_drm_content(
    url: str,
    pssh: bytes,
    vudrm_token: str,
    cdm_path: str,
    output_path: Path,
    args: Namespace,
    key_file: str | None = None,
    cli_keys: dict | None = None,
    key_provider: str = "cdm"
) -> Path | None:
    """
    Decrypt DRM-protected content using N_m3u8DL-RE.
    Returns output Path on success, None on failure.
    """
```

## Pipeline
```
1. Load keys from provider (key_provider):
   - "cdm": pywidevine + VUDRM proxy → acquire_license()
   - "file": parse JSON from key_file
   - "cli": use cli_keys dict

2. Build N_m3u8DL-RE command:
   N_m3u8DL-RE <url> --key KID:KEY --key KID:KEY ...
     --decryption-engine MP4DECRYPT|SHAKA_PACKAGER|FFMPEG
     --save-dir <output_dir> --save-name <filename>

3. Engine fallback chain (in order):
   1. MP4DECRYPT (mp4decrypt from Bento4) — PRIMARY
   2. SHAKA_PACKAGER (shaka-packager) — ALTERNATIVE
   3. FFMPEG (ffmpeg) — LAST RESORT

4. Run subprocess, capture output
5. Verify output file exists and is playable (ffprobe)
6. Return Path to decrypted file
```

## Key Acquisition (`acquire_license`)
```python
def acquire_license(
    pssh: bytes,
    cdm_path: str,
    vudrm_token: str
) -> dict[str, str]:
    """
    Returns KID_HEX -> KEY_HEX dict.
    Uses pywidevine to generate license challenge,
    posts to VUDRM proxy, parses response.
    """
```

## Engine Detection
```python
DECRYPTION_ENGINES = ["MP4DECRYPT", "SHAKA_PACKAGER", "FFMPEG"]
REQUIRED_BINARIES = {
    "MP4DECRYPT": "mp4decrypt",
    "SHAKA_PACKAGER": "shaka-packager",
    "FFMPEG": "ffmpeg",
}

def find_binary(name: str) -> str | None:
    """Return full path to binary if in PATH, else None."""
```

## Required System Binaries
| Engine | Binary | Install (Debian) |
|--------|--------|------------------|
| MP4DECRYPT | mp4decrypt | `apt install bento4` |
| SHAKA_PACKAGER | shaka-packager | Download from GitHub Releases |
| FFMPEG | ffmpeg | `apt install ffmpeg` |
| All | N_m3u8DL-RE | Download from nilaoda releases |

## Error Handling
- Missing all engines → return None, log "No decryption engine found"
- CDM validation failed → return None, log "CDM validation failed"
- License request failed (403) → return None, log "License request failed"
- No keys returned → return None, log "No CONTENT keys returned"
- N_m3u8DL-RE non-zero exit → try next engine in chain

## Tests
- `tests/test_drm_decrypt.py` (exists — minimal)
- `tests/test_drm_status.py` (exists)
- Mock N_m3u8DL-RE subprocess, test engine fallback

## Legal
See `docs/REQUIREMENTS.md` §8 — DMCA/InfoSoc/Belgian law applies