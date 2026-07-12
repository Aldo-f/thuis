"""Test season URL expansion via GraphQL/HEAD-fallback."""

import sys
import os
# Add the repository src directory so we can import thuis.main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from unittest.mock import patch, MagicMock
from thuis.main import main

EXPECTED_EP1 = "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/1/f-c--de-kampioenen-s1a1/"
EXPECTED_EP2 = "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/1/f-c--de-kampioenen-s1a2/"

METADATA_EP1 = {
    "series": "Fc De Kampioenen",
    "season": "1",
    "episode": "1",
    "height": "1080p",
    "vcodec_raw": "avc1",
    "acodec_raw": "mp4a",
    "ext": "mp4",
    "title": "Episode 1",
    "vcodec_label": "x264",
    "acodec_label": "AAC",
}

METADATA_EP2 = {
    "series": "Fc De Kampioenen",
    "season": "1",
    "episode": "2",
    "height": "1080p",
    "vcodec_raw": "avc1",
    "acodec_raw": "mp4a",
    "ext": "mp4",
    "title": "Episode 2",
    "vcodec_label": "x264",
    "acodec_label": "AAC",
}


def test_season_expand_dry_run(capsys):
    """Given a season URL, dry-run prints scene-named filenames for each episode."""
    original_argv = sys.argv

    with patch('thuis.main.fetch_season_episodes') as mock_fetch_season, \
         patch('thuis.main.subprocess.run') as mock_run, \
         patch('thuis.main.get_yt_dlp_cmd', return_value=['yt-dlp']), \
         patch('thuis.main.metadata_fetcher.fetch_metadata') as mock_fetch:

        # Mock fetch_season_episodes to return two episode URLs
        mock_fetch_season.return_value = [EXPECTED_EP1, EXPECTED_EP2]

        # mock_run: one call per episode URL's subprocess.run()
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='', stderr=''),
            MagicMock(returncode=0, stdout='', stderr=''),
        ]

        # fetch_metadata: one call per episode URL
        mock_fetch.side_effect = [METADATA_EP1, METADATA_EP2]

        sys.argv = [
            'thuis',
            '--dry-run',
            'https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/?seizoen=seizoen-2',
        ]
        try:
            with pytest.raises(SystemExit):
                main()
        finally:
            sys.argv = original_argv

    captured = capsys.readouterr()
    assert 'Fc.De.Kampioenen.S01E01.1080p.WEB-DL' in captured.out
    assert 'Fc.De.Kampioenen.S01E02.1080p.WEB-DL' in captured.out
