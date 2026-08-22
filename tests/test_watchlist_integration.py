#!/usr/bin/env python3
Integration tests for watchlist feature.

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from thuis.watchlist import (
    parse_watchlist_file,
    resolve_output_dir,
    WatchlistDB,
    check_file_exists,
)


class TestWatchlistIntegration:
    Integration tests for watchlist parsing and processing.

    def test_full_watchlist_file_parsing(self, tmp_path):
        Test parsing a complete watchlist file with multiple entries.
        wl_file = tmp_path / tv.txt
        wl_file.write_text(# Thuis TV downloads
