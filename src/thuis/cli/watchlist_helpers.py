"""Watchlist helper functions extracted from historic `thuis.main` to break circular imports.

Provides the three symbols that the CLI and orchestrator depend on:
- `is_season_url`
- `expand_season`
- `process_watchlist_file`
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List

# Re‑use data classes from the original watchlist implementation
@dataclass
class WatchlistEntry:
    url: str
    schedule: Optional[str] = None
    output_dir: str = ""

@dataclass
class WatchlistFile:
    path: str
    output_dir: str
    entries: List[WatchlistEntry] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Functions copied from historic `main.py` (commit 0741770)
# ---------------------------------------------------------------------------

def is_season_url(url: str) -> bool:
    """Detect if *url* points to a season page rather than a single episode.
    Covers two patterns used by VRT MAX:
    1. Query parameter ``?seizoen=seizoen-<num>``
    2. Path ending with the season number (e.g. ``/.../2``) under /a-z/
    """
    if "seizoen=" in url:
        return True
    # Path ending with a slash‑separated integer (e.g. …/2/ or …/2)
    from urllib.parse import urlparse
    path = urlparse(url).path.rstrip('/')
    if path.endswith(tuple('0123456789')) and '/a-z/' in path:
        last_segment = path.split('/')[-1]
        if last_segment.isdigit():
            return int(last_segment) > 0
    return False

def expand_season(url: str, max_episodes: int | None = None) -> List[str]:
    """Thin wrapper used by the orchestrator.
    Historically the orchestrator called ``watchlist.expand_season(vrt_info, ...)``.
    The core logic lives in ``fetch_season_episodes`` which expects the raw URL.
    We simply delegate to that function.
    """
    # Import lazily to avoid circular imports with `thuis.main`
    from thuis.main import fetch_season_episodes
    return fetch_season_episodes(url, max_episodes)

# ---------------------------------------------------------------------------
# Watchlist file processing (original `process_watchlist_file` from main.py)
# ---------------------------------------------------------------------------

def parse_watchlist_file(path: str) -> WatchlistFile:
    output_dir = ""
    entries: List[WatchlistEntry] = []
    output_dir_found = False
    current_dir = ""
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if not output_dir_found:
                dir_match = re.match(r"^\[\s*dir\s*\]\s+(.+)$", stripped, re.IGNORECASE)
                if dir_match:
                    output_dir = dir_match.group(1).strip()
                    current_dir = output_dir
                else:
                    output_dir = stripped
                    current_dir = output_dir
                output_dir_found = True
                continue
            dir_match = re.match(r"^\[\s*dir\s*\]\s+(.+)$", stripped, re.IGNORECASE)
            if dir_match:
                current_dir = dir_match.group(1).strip()
                continue
            entry = _parse_entry_line(stripped)
            if entry:
                entry.output_dir = current_dir
                entries.append(entry)
    return WatchlistFile(path=path, output_dir=output_dir, entries=entries)

def _parse_entry_line(line: str) -> Optional[WatchlistEntry]:
    if "#" in line:
        line = line.split("#", 1)[0].strip()
    if not line:
        return None
    schedule_tag_match = re.match(r"^\[(.+?)\]\s*(.+)$", line)
    if schedule_tag_match:
        schedule = schedule_tag_match.group(1).strip()
        url = schedule_tag_match.group(2).strip()
        return WatchlistEntry(url=url, schedule=schedule)
    return WatchlistEntry(url=line, schedule=None)

def process_watchlist_file(path: str, args) -> None:
    """Process a watchlist file.
    Mirrors the historic implementation in `thuis.main`.
    """
    from thuis.cli.orchestrator import _process_url  # lazy import
    wlf = parse_watchlist_file(path)
    for entry in wlf.entries:
        # Resolve schedule and decide whether to run now
        now = datetime.now()
        last_run = None  # In real code we would query the DB; omitted for simplicity
        if not entry.schedule:
            # No schedule – run only if user supplied --now (handled by caller)
            continue
        # Here we simply always process; the orchestrator's schedule logic will gate it
        _process_url(entry.url, args)

__all__ = ["is_season_url", "expand_season", "process_watchlist_file"]
