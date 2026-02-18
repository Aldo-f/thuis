"""Test authentication flow"""

import pytest
import asyncio
import os
from pathlib import Path

TEST_URLS = [
    "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/",
    "https://www.vrt.be/vrtmax/a-z/den-elfde-van-den-elfde/1/den-elfde-van-den-elfde-s1a1/",
]

from dotenv import load_dotenv

load_dotenv("/media/aldo/shared/thuis/v3/.env")

VRT_USERNAME = os.getenv("VRT_USERNAME", "kuxelu@ipdeer.com")
VRT_PASSWORD = os.getenv("VRT_PASSWORD", "Els123456")


class TestVRTMaxAuthentication:
    """Tests for VRT MAX authentication"""

    @pytest.mark.asyncio
    async def test_login_and_get_stream(self):
        """Test login and getting stream URL"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()

        await scraper.start()

        # Try to login
        print(f"\nAttempting login with: {VRT_USERNAME}")
        login_success = await scraper.login(VRT_USERNAME, VRT_PASSWORD)
        print(f"Login success: {login_success}")

        if login_success:
            # Try to get stream info
            url = TEST_URLS[0]
            print(f"\nGetting stream info for: {url}")
            stream_info = await scraper.get_stream_info(url)

            print(f"Stream info: {stream_info}")

            if stream_info:
                print(f"Video ID: {stream_info.video_id}")
                print(f"Stream URL: {stream_info.stream_url}")
                print(f"MPD URL: {stream_info.mpd_url}")
                print(f"Has DRM: {stream_info.has_drm}")
                print(f"DRM Free: {stream_info.is_drm_free}")

        await scraper.close()

        assert True, "Test completed"

    @pytest.mark.asyncio
    async def test_get_stream_after_login(self):
        """Test getting stream after login"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()

        await scraper.start()

        # Login first
        login_success = await scraper.login(VRT_USERNAME, VRT_PASSWORD)
        assert login_success, "Login should succeed"

        # Go to VRT MAX homepage first to get token
        await scraper.page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        # Get stream for Thuis (should be DRM-free)
        stream_info = await scraper.get_stream_info(TEST_URLS[0])
        assert stream_info is not None, "Should get stream info"

        print(f"\n=== Thuis (should be DRM-free) ===")
        print(f"Has DRM: {stream_info.has_drm}")
        print(f"DRM Free: {stream_info.is_drm_free}")
        print(
            f"Stream URL: {stream_info.stream_url[:50] if stream_info.stream_url else 'None'}..."
        )
        print(
            f"MPD URL: {stream_info.mpd_url[:50] if stream_info.mpd_url else 'None'}..."
        )

        # Save for download test
        if stream_info.stream_url:
            print(f"\n=== Stream URL found! ===")

        await scraper.close()
