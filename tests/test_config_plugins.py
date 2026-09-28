"""Tests for plugins section in config.py loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from thuis.config import load_config


class TestPluginsConfig:
    def test_no_plugins_section_defaults_to_empty_dict(self, tmp_path: Path):
        """When config.yaml has no plugins section, plugins key is {}."""
        (tmp_path / "config.yaml").write_text(
            "output_dir: /tmp/out\n", encoding="utf-8"
        )
        cfg = load_config(tmp_path)
        assert cfg.get("plugins", {}) == {}

    def test_plugins_with_enabled_list_loads(self, tmp_path: Path):
        """When config.yaml has plugins.enabled, it loads correctly."""
        (tmp_path / "config.yaml").write_text(
            "plugins:\n"
            "  enabled:\n"
            "    - torrent_uploader\n",
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        assert cfg["plugins"]["enabled"] == ["torrent_uploader"]

    def test_nested_plugin_options_load(self, tmp_path: Path):
        """Deeply nested plugin config values are preserved."""
        (tmp_path / "config.yaml").write_text(
            "plugins:\n"
            "  enabled:\n"
            "    - torrent_uploader\n"
            "  torrent_uploader:\n"
            "    trackers:\n"
            '      - "http://tracker.example.com/announce"\n'
            '    tmdb_key: "${TMDB_KEY}"\n'
            "    piece_size: 262144\n",
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        p = cfg["plugins"]["torrent_uploader"]
        assert p["trackers"] == ["http://tracker.example.com/announce"]
        assert p["tmdb_key"] == "${TMDB_KEY}"
        assert p["piece_size"] == 262144

    def test_no_config_yaml_at_all(self, tmp_path: Path):
        """Empty dir (no config.yaml) still yields plugins={}. """
        cfg = load_config(tmp_path)
        assert cfg.get("plugins", {}) == {}
