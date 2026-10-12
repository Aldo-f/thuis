# Config Specification

## Module
`src/thuis/config.py` — YAML/env config loader

## Priority Order (last fallback wins)
1. Environment variables (exported in shell) — highest priority
2. `.env` file in project root — loaded via `python-dotenv` if installed
3. `~/.thuis.config.yaml` — user-level config
4. `pyproject.toml` `[project]` defaults
5. Hardcoded defaults in `main.py` (used for VRT credentials fallback)

## Config File Format (`.env` or `~/.thuis.config.yaml`)
```yaml
# ~/.thuis.config.yaml
output_dir: "/mnt/HDD1/services/nextcloud/data/aldo/files/Media"
output_dir_env: "/some/other/path"
verbose: 1
```

### .env format
```env
VRT_EMAIL=user@example.com
VRT_PASSWORD=SuperSecret123
DECRYPT_DRM=yes
WVD_CDM_PATH=/mnt/secure/cdm
OUTPUT_DIR=/mnt/HDD1/media
```

## Functions
```python
def get_config(key: str, default=None) -> any:
    # Check env vars first (UPPER_CASE key)
    env_key = key.upper()
    if env_key in os.environ:
        return os.environ[env_key]

    # Check .env file (python-dotenv)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if env_key in os.environ:
            return os.environ[env_key]
    except ImportError:
        pass

    # Check ~/.thuis.config.yaml
    config_path = Path.home() / ".thuis.config.yaml"
    if config_path.exists():
        with config_path.open() as f:
            cfg = yaml.safe_load(f)
        if key in cfg:
            return cfg[key]

    # Check pyproject.toml
    # ... (project defaults)

    return default
```

## Keys
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_dir` | str | `./media` | Base output directory |
| `verbose` | int | `0` | Log level |
| `decr_yet_drm` | bool | `yes` | Enable DRM decryption |
| `wvd_cdm_path` | str | `~/.thuis/cdm/` | CDM cache directory |
| `vrt_email` | str | (none) | VRT MAX email |
| `vrt_password` | str | (none) | VRT MAX password |
| `allow_external_downloader` | bool | `no` | Allow non-VRT URLs |
| `default_profile` | int | `0` | Default yt-dlp profile index |