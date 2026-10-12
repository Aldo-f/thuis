# Plugin System

Thuis supports post-download plugins via Python entry points. Plugins run after a file is saved and can perform actions like creating torrents, uploading to remote storage, or tagging metadata.

## Plugin Interface

Every plugin exposes a single function:

```python
from pathlib import Path
from typing import Any

def postprocess(ctx: PostprocessContext) -> bool:
    ...
```

The function receives a `PostprocessContext` and returns `True` on success, `False` on failure. Exceptions are caught by the host and recorded as failures, so plugins should return `False` rather than raise.

### PostprocessContext Fields

| Field | Type | Description |
|-------|------|-------------|
| `filepath` | `Path` | Absolute path to the downloaded file. |
| `metadata` | `dict[str, Any]` | Metadata emitted by yt-dlp (title, duration, description, etc.). |
| `output_dir` | `Path` | Directory where the file was saved. |
| `dry_run` | `bool` | If `True`, the plugin must avoid side effects (no writes, no network calls). |

The host also attaches a `_plugin_config` attribute to the context when a plugin declares its own config section. Access it with `getattr(ctx, "_plugin_config", {})`.

## Entry Point Registration

Plugins register themselves by adding an entry point under the `thuis.postprocess` group in `pyproject.toml`:

```toml
[project.entry-points."thuis.postprocess"]
my_plugin = "my_package.module:postprocess"
```

The format is `<name> = "<module>:<function>"`. The `name` is what users refer to in their config. The host discovers all entry points at runtime via `importlib.metadata.entry_points`.

## Configuration

Enable plugins in `config.yaml` under the `plugins` key:

```yaml
plugins:
  enabled: [torrent_uploader, my_plugin]
  torrent_uploader:
    trackers: []
    piece_size: 262144
    comment: ""
    source: "thuis"
  my_plugin:
    some_option: value
```

- `enabled` — list of entry-point names to load. Omit or leave empty to disable all plugins.
- Per-plugin subsections (e.g. `torrent_uploader:`) are passed through as `_plugin_config` to that plugin's `postprocess` function.

## Error Handling

- A plugin that raises an exception is logged and marked as failed (`False`).
- A plugin that returns `False` is also marked as failed but does not produce an error log.
- Plugin failures do not abort the download — they are reported after the file is saved.
- In `dry_run` mode, plugins should skip all side effects and return `True`.

## Example Plugin

A minimal plugin that logs file info:

```python
"""Example plugin — logs downloaded file details."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def postprocess(ctx: Any) -> bool:  # type: ignore[name-defined]
    """Log basic info about the downloaded file."""
    filepath = Path(ctx.filepath)
    metadata = ctx.metadata
    dry_run = ctx.dry_run

    logger.info(
        "Plugin example: %s (%s)",
        filepath.name,
        metadata.get("title", "unknown title"),
    )

    if dry_run:
        logger.info("[dry-run] Would have processed: %s", filepath)
        return True

    # plugin_config is set by the host when a config section exists
    config = getattr(ctx, "_plugin_config", {}) or {}
    logger.debug("Plugin config: %s", config)

    return True
```

Register it in `pyproject.toml`:

```toml
[project.entry-points."thuis.postprocess"]
example = "my_package.example:postprocess"
```

And enable it in `config.yaml`:

```yaml
plugins:
  enabled: [example]
```

## Full Example: Torrent Creator

A more complete example based on the built-in `torrent_uploader`:

```python
"""Creates a .torrent file from downloaded media."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import libtorrent as lt
except ImportError:  # pragma: no cover
    lt = None


class TorrentCreator:
    """Creates .torrent files from local media using python-libtorrent."""

    def __init__(
        self,
        trackers: list[str] | None = None,
        piece_size: int = 262144,
        comment: str = "",
        source: str = "thuis",
    ) -> None:
        if lt is None:
            raise RuntimeError(
                "python-libtorrent is not installed. "
                "Install it with: pip install libtorrent"
            )
        self._trackers = list(trackers or [])
        self._piece_size = piece_size
        self._comment = comment
        self._source = source

    def create(self, filepath: Path) -> Path:
        """Create a .torrent file next to the source.

        Returns the path to the generated .torrent file.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Source not found: {filepath}")

        fs = lt.file_storage()
        lt.add_files(fs, str(filepath))

        if fs.num_files() == 0:
            raise RuntimeError(f"No files found in: {filepath}")

        tor = lt.create_torrent(fs, piece_size=self._piece_size)
        tor.set_comment(self._comment)
        tor.set_creator(self._source)

        for url in self._trackers:
            tor.add_tracker(url)

        lt.set_piece_hashes(tor, str(filepath.parent))
        torrent_data = lt.bencode(tor.generate())

        out_path = filepath.parent / f"{filepath.stem}.torrent"
        out_path.write_bytes(torrent_data)
        return out_path


def postprocess(ctx: Any) -> bool:  # type: ignore[name-defined]
    """Entry point called by the plugin host."""
    filepath = Path(ctx.filepath)

    if not filepath.exists():
        logger.warning("Skipped — file not found: %s", filepath)
        return False

    try:
        cfg = getattr(ctx, "_plugin_config", {}) or {}
        creators = TorrentCreator(
            trackers=cfg.get("trackers"),
            piece_size=cfg.get("piece_size") or 262144,
            comment=cfg.get("comment", ""),
            source=cfg.get("source", "thuis"),
        )

        if ctx.dry_run:
            logger.info("[dry-run] Would create .torrent for: %s", filepath)
            return True

        out = creators.create(filepath)
        logger.info("Created .torrent: %s", out)
        return True

    except Exception as exc:
        logger.error("Plugin failed: %s", exc)
        return False
```

## Third-Party Plugins

Plugins can live in separate packages. Install the package and add its entry point to your project's `pyproject.toml`, or have the package declare its own entry point and install it into the same environment. The host discovers all `thuis.postprocess` entry points regardless of which package registered them.
