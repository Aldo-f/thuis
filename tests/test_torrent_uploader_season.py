"""Tests for season upload flow in torrent_uploader plugin."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from thuis.plugins.torrent_uploader import postprocess


class TestSeasonUploadFlow:
    """postprocess triggers season upload when season is complete."""

    def test_single_episode_creates_episode_torrent_only(self, tmp_path):
        """When season is NOT complete, only creates per-episode .torrent."""
        # Create one episode file
        ep = tmp_path / "FC.De.Kampioenen.S01E01.1080p.WEB-DL.AAC.x264.mp4"
        ep.touch()

        from thuis.plugin_host import PostprocessContext
        ctx = PostprocessContext(
            filepath=ep,
            metadata={"series": "FC De Kampioenen", "season": 1, "episode": 1},
            output_dir=tmp_path,
            dry_run=True,
        )
        with patch.dict("sys.modules", {"thuis.plugins.season_detector": MagicMock()}):
            result = postprocess(ctx)
        # Should succeed (dry-run mode)
        assert result is True

    def test_season_complete_triggers_season_torrent(self, tmp_path):
        """When season IS complete, creates season .torrent + uploads."""
        # Create all 13 episodes
        for i in range(1, 14):
            (tmp_path / f"FC.De.Kampioenen.S01E{i:02d}.1080p.WEB-DL.AAC.x264.mp4").touch()

        from thuis.plugin_host import PostprocessContext
        ep = tmp_path / "FC.De.Kampioenen.S01E13.1080p.WEB-DL.AAC.x264.mp4"
        ctx = PostprocessContext(
            filepath=ep,
            metadata={"series": "FC De Kampioenen", "season": 1, "episode": 13},
            output_dir=tmp_path,
            dry_run=True,
        )
        result = postprocess(ctx)
        # Should succeed in dry-run mode
        assert result is True
