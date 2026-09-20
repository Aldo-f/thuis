"""Configuration loader for thuis - reads config.yaml and config.local.yaml"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def find_config_dir() -> Path:
    """Find the project root directory containing config.yaml."""
    # Start from this file's directory and walk up
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "config.yaml").exists():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()


def load_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from config.yaml and optionally config.local.yaml.

    Args:
        config_dir: Directory to search for config files. If None, auto-detects.

    Returns:
        Merged configuration dictionary.
    """
    if config_dir is None:
        config_dir = find_config_dir()

    config: Dict[str, Any] = {}

    # Load base config
    base_config = config_dir / "config.yaml"
    if base_config.exists():
        with open(base_config, "r") as f:
            config = yaml.safe_load(f) or {}

    # Load local overrides (gitignored)
    local_config = config_dir / "config.local.yaml"
    if local_config.exists():
        with open(local_config, "r") as f:
            local = yaml.safe_load(f) or {}
            # Deep merge
            config = deep_merge(config, local)

    # Environment variable overrides (highest priority)
    env_overrides = {
        "output_dir": os.getenv("OUTPUT_DIR"),
        "watchlist_dir": os.getenv("WATCHLIST_DIR"),
        "log_dir": os.getenv("LOG_DIR"),
        "database_path": os.getenv("DATABASE_PATH"),
        "drm.enabled": os.getenv("DECRYPT_DRM", "").lower() == "yes",
        "drm.cdm_path": os.getenv("WVD_CDM_PATH"),
        "drm.decrypt_policy": os.getenv("DECRYPT_DRM"),
    }
    apply_env_overrides(config, env_overrides)

    return config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def apply_env_overrides(config: Dict[str, Any], overrides: Dict[str, Optional[str]]) -> None:
    """Apply environment variable overrides to config using dot notation keys."""
    for key, value in overrides.items():
        if value is None or value == "":
            continue
        parts = key.split(".")
        target = config
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value


# Singleton pattern for global config access
_config: Optional[Dict[str, Any]] = None


def get_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Get the global configuration (cached)."""
    global _config
    if _config is None:
        _config = load_config(config_dir)
    return _config


def reset_config() -> None:
    """Reset the cached configuration (useful for testing)."""
    global _config
    _config = None