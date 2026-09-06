# DRM Key Extraction Extension Spec

## Goal
Extend thuis to accept content keys (KID:KEY pairs) from sources **other than the pywidevine CDM pipeline**, enabling use of keys extracted via browser extensions or manual input.

## Current Architecture (drm_decrypt.py)

```
VUDRM token + PSSH + CDM (.wvd)
        │
        ▼
acquire_license()  ──►  pywidevine → VUDRM proxy  ──►  KID:KEY dict
        │
        ▼
N_m3u8DL-RE --key KID:KEY ...  ──►  decrypted MP4
```

## Extension Points

### 1. New Key Source Abstraction
Add `KeyProvider` protocol with implementations:
- `WidevineCdmProvider` (current: pywidevine + VUDRM)
- `KeyFileProvider` (read KID:KEY from file)
- `CliKeyProvider` (keys passed via CLI `--key` args)

### 2. CLI Arguments (thuis.sh / main.py)
```bash
# New options
--key-file PATH          # JSON file: {"KID_HEX": "KEY_HEX", ...}
--key KID:KEY            # Repeatable, direct key pairs
--key-provider NAME      # Select provider: cdm | file | cli (default: cdm)
```

### 3. Key File Format (JSON)
```json
{
  "eb676abbcb345e96bbcf616630f1a3da": "100b6c20940f779a4589152b57d2dacb",
  "another_kid_hex": "another_key_hex"
}
```

### 4. Pipeline Changes

**decrypt_drm_content() signature:**
```python
def decrypt_drm_content(
    ...,
    cdm_path: Optional[str] = None,
    key_file: Optional[str] = None,
    cli_keys: Optional[Dict[str, str]] = None,
    key_provider: str = "cdm"
) -> Optional[Path]:
```

**Key resolution order:**
1. `cli_keys` (highest priority, explicit override)
2. `key_file` (JSON file)
3. `cdm_path` + VUDRM (current behavior, default)

### 5. Implementation Details

**New function: `load_keys_from_source()`**
```python
def load_keys_from_source(
    provider: str,
    vudrm_token: Optional[str] = None,
    pssh: Optional[bytes] = None,
    cdm_path: Optional[str] = None,
    key_file: Optional[str] = None,
    cli_keys: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Resolve keys from selected provider."""
```

**Provider implementations:**
- `cdm`: call existing `acquire_license()` (requires vudrm_token, pssh, cdm_path)
- `file`: parse JSON from key_file
- `cli`: return cli_keys dict

### 6. Error Handling
- Provider validation: all required args present
- Key format validation: KID/KEY are valid hex strings
- Graceful degradation: if provider fails, log error, return None (existing behavior)

### 7. Backward Compatibility
- All new args optional
- Default `key_provider="cdm"` preserves current behavior
- Existing `.env` / CLI usage unchanged

## Files to Modify
1. `src/thuis/drm_decrypt.py` - Core logic
2. `src/thuis/main.py` - CLI argument parsing (pass through to decrypt_drm_content)
3. `thuis.sh` - No changes needed (passes args through)

## Testing
- Unit test: `load_keys_from_source()` with each provider
- Integration test: `--key-file` with valid JSON
- Integration test: `--key` CLI args
- Verify existing CDM path still works