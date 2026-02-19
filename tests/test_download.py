"""Test VRT MAX downloads - DRM-free and DRM protected"""

import sys
import pytest
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from conftest import TEST_URLS, skip_no_credentials, vrt_credentials, output_dir


@skip_no_credentials
class TestDownload:
    """Test video downloads from VRT MAX"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(300)
    async def test_download_short_drm_free(self, vrt_credentials, output_dir):
        """Test download van korte DRM-vrije trailer (~2 min)"""
        from thuis import download_video

        username, password = vrt_credentials
        output_path = output_dir / "test_trailer.mp4"

        success = await download_video(
            video_url=TEST_URLS["drm_free_short"],
            username=username,
            password=password,
            output_path=output_path,
            headless=True,
        )

        assert success, "Download zou moeten slagen voor DRM-vrije trailer"
        assert output_path.exists(), "Output bestand zou moeten bestaan"
        assert output_path.stat().st_size > 1_000_000, "Bestand zou > 1MB moeten zijn"

        output_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(600)
    async def test_download_long_drm_free(self, vrt_credentials, output_dir):
        """Test download van volledige aflevering (~10 min)"""
        from thuis import download_video

        username, password = vrt_credentials
        output_path = output_dir / "test_episode.mp4"

        success = await download_video(
            video_url=TEST_URLS["drm_free_long"],
            username=username,
            password=password,
            output_path=output_path,
            headless=True,
        )

        assert success, "Download zou moeten slagen voor DRM-vrije aflevering"
        assert output_path.exists(), "Output bestand zou moeten bestaan"
        assert output_path.stat().st_size > 50_000_000, "Bestand zou > 50MB moeten zijn"

        output_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(300)
    async def test_download_drm_protected_fails(self, vrt_credentials, output_dir):
        """Test dat DRM-beschermde video faalt met duidelijke foutmelding"""
        from thuis import download_video

        username, password = vrt_credentials
        output_path = output_dir / "test_drm.mp4"

        success = await download_video(
            video_url=TEST_URLS["drm_protected"],
            username=username,
            password=password,
            output_path=output_path,
            headless=True,
        )

        assert not success, "DRM-beschermde video zou moeten falen"
        assert not output_path.exists(), "Geen output bestand bij DRM fout"

        output_path.unlink(missing_ok=True)
