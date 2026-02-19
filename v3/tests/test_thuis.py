"""Test voor thuis.py"""

import pytest
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Laad .env voor tests
load_dotenv(Path(__file__).parent.parent / ".env")

TEST_URLS = [
    "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/",
    "https://www.vrt.be/vrtmax/a-z/den-elfde-van-den-elfde/1/den-elfde-van-den-elfde-s1a1/",
]

VRT_USERNAME = os.getenv("VRT_USERNAME", "")
VRT_PASSWORD = os.getenv("VRT_PASSWORD", "")


# Skip tests als er geen credentials zijn
pytestmark = pytest.mark.skipif(
    not VRT_USERNAME or not VRT_PASSWORD, reason="Geen VRT credentials gevonden in .env"
)


class TestThuisDownload:
    """Test class voor thuis.py functionaliteit"""

    @pytest.mark.asyncio
    async def test_download_thuis(self):
        """Test download van Thuis aflevering"""
        from thuis import download_video

        output_path = Path("media/test_thuis.mp4")

        success = await download_video(
            video_url=TEST_URLS[0],
            username=VRT_USERNAME,
            password=VRT_PASSWORD,
            output_path=output_path,
            headless=True,
        )

        assert success, "Download zou moeten slagen"
        assert output_path.exists(), "Output bestand zou moeten bestaan"
        assert output_path.stat().st_size > 100_000_000, (
            "Bestand zou groter dan 100MB moeten zijn"
        )

        # Clean up
        if output_path.exists():
            output_path.unlink()

    @pytest.mark.asyncio
    async def test_download_den_elfde(self):
        """Test download van Den Elfde aflevering"""
        from thuis import download_video

        output_path = Path("media/test_den_elfde.mp4")

        success = await download_video(
            video_url=TEST_URLS[1],
            username=VRT_USERNAME,
            password=VRT_PASSWORD,
            output_path=output_path,
            headless=True,
        )

        assert success, "Download zou moeten slagen"
        assert output_path.exists(), "Output bestand zou moeten bestaan"

        # Clean up
        if output_path.exists():
            output_path.unlink()
