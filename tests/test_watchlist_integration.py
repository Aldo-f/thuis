"""Integration tests for watchlist feature."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest

from thuis.watchlist import (
    parse_watchlist_file,
    resolve_output_dir,
    WatchlistDB,
    check_file_exists,
)


class TestWatchlistIntegration:
    """Integration tests for watchlist parsing and processing."""

    def test_full_watchlist_file_parsing(self, tmp_path):
        """Parse a complete watchlist file with multiple entries."""
        wl_file = tmp_path / "tv.txt"
        wl_file.write_text(
            "# Thuis TV downloads\n"
            "https://www.vrt.be/vrtnu/a-recommended/fc-de-kampioenen/\n"
            "\n"
            "# comment line\n"
            "https://www.vrt.be/vrtnu/a-z/ketnet-doc/\n",
            encoding="utf-8",
        )
        entries = parse_watchlist_file(str(wl_file))
        # First line is consumed as the output directory, comments skipped
        assert len(entries.entries) == 1
        assert entries.output_dir.endswith("fc-de-kampioenen/")
