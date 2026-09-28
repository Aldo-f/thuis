"""Plugin host — entry-point based postprocess plugin system."""

from __future__ import annotations

import importlib.metadata
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


__all__ = [
    "PostprocessContext",
    "PluginManager",
    "load_entry_point_plugins",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PostprocessContext:
    """Immutable context passed to every postprocess plugin."""

    filepath: Path
    """Path to the downloaded file."""
    metadata: dict[str, Any]
    """Metadata emitted by yt-dlp (title, duration, etc.)."""
    output_dir: Path
    """Directory where the file was saved."""
    dry_run: bool
    """If True, plugins should avoid side effects."""


def load_entry_point_plugins() -> list[dict[str, str]]:
    """Return all entry points registered under ``thuis.postprocess``.

    Returns a list of ``{"name": ..., "value": ...}`` dicts — one per
    discovered plugin — regardless of the project's config.  Used by tests
    and by :meth:`PluginManager.load_plugins` itself.
    """
    eps = importlib.metadata.entry_points(group="thuis.postprocess")
    return [{"name": ep.name, "value": ep.value} for ep in eps] if hasattr(eps, "__iter__") else []


class PluginManager:
    """Discovers and runs postprocess plugins."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def load_plugins(self) -> list[dict[str, str]]:
        """Discover enabled plugins from entry points.

        The ``plugins`` section of *config* must contain an ``enabled`` list.
        Only entry points whose ``name`` appears in that list are returned.

        Returns:
            List of ``{"name": ..., "value": ...}`` dicts for enabled plugins.
        """
        all_eps = load_entry_point_plugins()
        enabled: list[str] = self._config.get("plugins", {}).get("enabled", [])
        if not enabled:
            logger.debug("No plugins configured (plugins.enabled is empty)")
            return []
        filtered = [ep for ep in all_eps if ep["name"] in enabled]
        missing = set(enabled) - {ep["name"] for ep in filtered}
        if missing:
            logger.debug("Configured plugins not found as entry points: %s", sorted(missing))
        logger.debug("Loaded %d plugin(s): %s", len(filtered), [ep["name"] for ep in filtered])
        return filtered

    def run_plugins(self, ctx: PostprocessContext) -> dict[str, bool]:
        """Run every loaded plugin against *ctx*.

        Each plugin's entry point is imported and called as
        ``plugin_fn(ctx)``.  Exceptions are caught, logged, and recorded as
        failures.

        Returns:
            ``{plugin_name: bool_success}`` mapping.
        """
        loaded = self.load_plugins()
        results: dict[str, bool] = {}
        for ep in loaded:
            name = ep["name"]
            try:
                module, attr = ep["value"].split(":", 1)
                mod = importlib.import_module(module)
                fn = getattr(mod, attr)
            except Exception as exc:
                logger.error("Failed to load plugin %r: %s", name, exc)
                results[name] = False
                continue

            try:
                fn(ctx)
                results[name] = True
                logger.debug("Plugin %s succeeded", name)
            except Exception as exc:
                logger.error("Plugin %r raised: %s", name, exc)
                results[name] = False
        return results
