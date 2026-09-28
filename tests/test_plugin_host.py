"""Tests for src/thuis/plugin_host.py."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thuis.plugin_host import (
    PostprocessContext,
    PluginManager,
    load_entry_point_plugins,
)


# ---------------------------------------------------------------------------
# Baseline: entry_points returns empty when no plugins installed
# ---------------------------------------------------------------------------

class TestBaseline:
    def test_entry_points_empty_when_no_plugins(self):
        """With no plugins installed, load_entry_point_plugins returns []."""
        result = load_entry_point_plugins()
        assert isinstance(result, list)
        assert result == []


# ---------------------------------------------------------------------------
# PostprocessContext
# ---------------------------------------------------------------------------

class TestPostprocessContext:
    def test_frozen_dataclass(self):
        ctx = PostprocessContext(
            filepath=Path("/tmp/video.mp4"),
            metadata={"title": "test"},
            output_dir=Path("/tmp/out"),
            dry_run=False,
        )
        with pytest.raises(AttributeError):
            ctx.filepath = Path("/other")

    def test_equality(self):
        a = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={"k": "v"},
            output_dir=Path("/tmp/out"),
            dry_run=True,
        )
        b = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={"k": "v"},
            output_dir=Path("/tmp/out"),
            dry_run=True,
        )
        assert a == b

    def test_frozen_prevents_reassignment(self):
        """Frozen dataclass rejects attribute reassignment."""
        ctx = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={},
            output_dir=Path("/tmp"),
            dry_run=False,
        )
        with pytest.raises(AttributeError):
            ctx.metadata = {"new": "data"}


# ---------------------------------------------------------------------------
# load_entry_point_plugins
# ---------------------------------------------------------------------------

class TestLoadEntryPoints:
    def test_returns_list_of_dicts(self):
        """When entry points exist, each item has name and value."""
        fake_ep = MagicMock()
        fake_ep.name = "my_plugin"
        fake_ep.value = "pkg.mod:fn"

        with patch("thuis.plugin_host.importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = [fake_ep]
            result = load_entry_point_plugins()

        assert result == [{"name": "my_plugin", "value": "pkg.mod:fn"}]

    def test_empty_entry_points(self):
        with patch("thuis.plugin_host.importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = []
            result = load_entry_point_plugins()
        assert result == []


# ---------------------------------------------------------------------------
# PluginManager
# ---------------------------------------------------------------------------

class TestPluginManager:
    def test_init_stores_config(self):
        pm = PluginManager({"plugins": {"enabled": ["a"]}})
        assert pm._config == {"plugins": {"enabled": ["a"]}}

    def test_load_plugins_no_enabled(self):
        pm = PluginManager({})
        assert pm.load_plugins() == []

    def test_load_plugins_empty_enabled_list(self):
        pm = PluginManager({"plugins": {"enabled": []}})
        assert pm.load_plugins() == []

    def test_load_plugins_filters_by_enabled(self):
        pm = PluginManager({"plugins": {"enabled": ["known"]}})
        fake_eps = [
            {"name": "known", "value": "pkg:fn"},
            {"name": "unknown", "value": "other:fn"},
        ]
        with patch("thuis.plugin_host.load_entry_point_plugins", return_value=fake_eps):
            result = pm.load_plugins()
        assert result == [{"name": "known", "value": "pkg:fn"}]

    def test_run_plugins_calls_each(self):
        pm = PluginManager({"plugins": {"enabled": ["plugA"]}})
        fake_eps = [{"name": "plugA", "value": "tests.test_plugin_host:_noop_plugin"}]
        ctx = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={},
            output_dir=Path("/tmp"),
            dry_run=False,
        )

        with patch("thuis.plugin_host.load_entry_point_plugins", return_value=fake_eps):
            result = pm.run_plugins(ctx)

        assert result == {"plugA": True}

    def test_run_plugins_catches_exception(self):
        def bad_fn(_ctx):
            raise RuntimeError("boom")

        # Patch import to return a broken module
        fake_eps = [{"name": "bad", "value": "tests.test_plugin_host:bad_fn"}]
        pm = PluginManager({"plugins": {"enabled": ["bad"]}})
        ctx = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={},
            output_dir=Path("/tmp"),
            dry_run=False,
        )

        with patch("thuis.plugin_host.load_entry_point_plugins", return_value=fake_eps):
            result = pm.run_plugins(ctx)

        assert result == {"bad": False}

    def test_run_plugins_no_plugins(self):
        pm = PluginManager({})
        ctx = PostprocessContext(
            filepath=Path("/tmp/v.mp4"),
            metadata={},
            output_dir=Path("/tmp"),
            dry_run=False,
        )
        assert pm.run_plugins(ctx) == {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _noop_plugin(_ctx: PostprocessContext) -> dict:
    return {}
