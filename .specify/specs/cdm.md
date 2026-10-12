# CDM Module Specification

## Module
`src/thuis/cdm.py` — Widevine L3 CDM auto-fetch, validation, caching

## Functions
```python
def ensure_cdm() -> str | None:
    """
    Ensure a valid Widevine L3 Android CDM (.wvd) is available.
    Returns path to CDM file, or None if unavailable.
    """

def get_cdm_cache_dir() -> Path:
    """Return CDM cache directory (~/.thuis/cdm/ or WVD_CDM_PATH)."""
```

## Logic
1. Check `WVD_CDM_PATH` env var for custom location
2. Default: `~/.thuis/cdm/widevine_l3_android.wvd`
3. If file exists → validate with `pywidevine.device.Device.load()`
   - Must be ANDROID type, security_level=3
4. If invalid/missing → auto-fetch from community sources:
   - `https://github.com/nicko170/video-devices/raw/main/widevine_l3_android.wvd`
   - Fallback: other known mirrors
5. Cache downloaded CDM for reuse
6. Return path to valid CDM

## Validation
```python
from pywidevine.device import Device
d = Device.load(cdm_path)
assert d.type == "ANDROID"
assert d.security_level == 3
```

## Sources (priority order)
1. `WVD_CDM_PATH` env var
2. `~/.thuis/cdm/widevine_l3_android.wvd`
3. Auto-fetch from `nicko170/video-devices` (current default)

## Warning
- Community CDMs are shared → higher revocation risk
- Never commit `.wvd` files to git (gitignored)
- For production: extract own CDM from rooted Android (see `extract_cdm.py`)

## Tests
- `tests/test_cdm.py` (exists)
- Mock pywidevine validation, test auto-fetch fallback