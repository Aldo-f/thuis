"""Tests for podcast URL support in url_parser."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from thuis.url_parser import parse_vrt_url


class TestPodcastUrls:
    PODCAST_SHOW = "https://www.vrt.be/vrtmax/podcasts/radio-1/d/de-gifmenger"
    PODCAST_EP = ("https://www.vrt.be/vrtmax/podcasts/radio-1/d/"
                  "de-gifmenger/1/1--in-coma/")

    def test_podcast_show_url(self):
        info = parse_vrt_url(self.PODCAST_SHOW)
        assert info.show_slug == "de-gifmenger"
        assert info.season == 0
        assert info.episode == 0

    def test_podcast_episode_url(self):
        info = parse_vrt_url(self.PODCAST_EP)
        assert info.show_slug == "de-gifmenger"
        assert info.season == 1
        assert info.episode == 0  # slug has no sNaM pattern

    def test_podcast_episode_snam_pattern(self):
        url = ("https://www.vrt.be/vrtmax/podcasts/radio-1/d/"
               "de-gifmenger/2/de-gifmenger-s2a5/")
        info = parse_vrt_url(url)
        assert info.season == 2
        assert info.episode == 5

    def test_a_z_still_works(self):
        info = parse_vrt_url("https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6109/")
        assert info.show_slug == "thuis"
        assert info.season == 31
        assert info.episode == 6109

    def test_invalid_path_raises(self):
        import pytest
        with pytest.raises(ValueError):
            parse_vrt_url("https://www.vrt.be/something/else/")
