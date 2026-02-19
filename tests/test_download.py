"""Test end-to-end download"""

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


class TestVRTMaxDownload:
    """Tests for VRT MAX download"""

    @pytest.mark.asyncio
    async def test_full_download_flow(self):
        """Test complete login + stream extraction + download for Thuis"""
        from modules.vrt_scraper import VRTMaxScraper
        import requests

        scraper = VRTMaxScraper(headless=True)

        await scraper.start()

        # Step 1: Login
        print("\n=== Step 1: Login ===")
        login_success = await scraper.login(VRT_USERNAME, VRT_PASSWORD)
        assert login_success, "Login should succeed"
        print("Login successful!")

        # Step 2: Go to VRT MAX homepage to get token
        print("\n=== Step 2: Get token ===")
        await scraper.page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        # Step 3: Navigate to video to trigger API calls
        print("\n=== Step 3: Navigate to video ===")
        await scraper.page.goto(TEST_URLS[0], wait_until="networkidle")
        await asyncio.sleep(3)

        # Step 4: Get stream info via API
        print("\n=== Step 4: Get stream info ===")

        # First, set up response handler BEFORE navigating
        token = None

        async def handle_response(response):
            nonlocal token
            if "/tokens" in response.url and "vualto" in response.url:
                print(f"Token request: {response.url[:80]}")
                try:
                    data = await response.json()
                    token = data.get("vrtPlayerToken")
                    print(f"Got token: {token[:30]}..." if token else "No token")
                except Exception as e:
                    print(f"Error getting token: {e}")

        scraper.page.on("response", handle_response)

        # Go to VRT MAX homepage first
        print("Navigating to VRT MAX homepage...")
        await scraper.page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        # Then navigate to video
        print("Navigating to video...")
        await scraper.page.goto(TEST_URLS[0], wait_until="networkidle")
        await asyncio.sleep(5)

        # Extract IDs after navigation
        video_id = await scraper.extract_video_id(TEST_URLS[0])
        pub_id = await scraper.extract_publication_id(TEST_URLS[0])

        print(f"Video ID: {video_id}")
        print(f"Publication ID: {pub_id}")
        print(f"Token: {token[:30] if token else 'None'}...")

        if token:
            # Get stream via API
            full_id = f"{pub_id}${video_id}"
            api_url = f"https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/videos/{full_id}?vrtPlayerToken={token}&client=vrtnu-web@PROD"

            resp = requests.get(api_url, allow_redirects=True)
            print(f"API Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                target_urls = data.get("targetUrls", [])

                print(f"\n=== Video Info ===")
                print(f"Title: {data.get('title')}")
                print(f"DRM: {data.get('drmImplementation')}")

                for tu in target_urls:
                    url_type = tu.get("type")
                    url = tu.get("url")
                    print(f"\n{url_type}: {url[:80]}...")

                    # Save stream URL for next test
                    if url_type == "hls":
                        hls_url = url

                print("\n=== SUCCESS: Stream URL found! ===")

        await scraper.close()

        assert token is not None, "Should get player token"

    @pytest.mark.asyncio
    async def test_actually_download_video(self):
        """Test actually downloading the video"""
        from modules.vrt_scraper import VRTMaxScraper
        import requests
        import subprocess

        # First get the stream URL
        scraper = VRTMaxScraper(headless=True)

        await scraper.start()

        # Login
        await scraper.login(VRT_USERNAME, VRT_PASSWORD)

        # Get token
        await scraper.page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        token = None

        async def handle_response(response):
            nonlocal token
            if "/tokens" in response.url and "vualto" in response.url:
                try:
                    data = await response.json()
                    token = data.get("vrtPlayerToken")
                except:
                    pass

        scraper.page.on("response", handle_response)

        # Get video
        video_id = "vid-99ec2208-55d9-4d8c-9414-d8665d9142a4"
        pub_id = "pbs-pub-0e4e7132-ac25-454b-9b84-4e733f09a994"

        await scraper.page.goto(TEST_URLS[0], wait_until="networkidle")
        await asyncio.sleep(5)

        await scraper.close()

        # Now get stream URL
        if token:
            full_id = f"{pub_id}${video_id}"
            api_url = f"https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/videos/{full_id}?vrtPlayerToken={token}&client=vrtnu-web@PROD"

            resp = requests.get(api_url, allow_redirects=True)
            data = resp.json()

            # Get HLS URL
            hls_url = None
            for tu in data.get("targetUrls", []):
                if tu.get("type") == "hls":
                    hls_url = tu.get("url")
                    break

            if hls_url:
                print(f"\n=== Downloading ===")
                print(f"URL: {hls_url[:100]}...")

                # Create output directory
                output_dir = Path("/media/aldo/shared/thuis/media")
                output_dir.mkdir(exist_ok=True)

                output_file = output_dir / "thuis_test.mp4"

                # Download with ffmpeg
                print(f"Running ffmpeg...")
                cmd = [
                    "ffmpeg",
                    "-i",
                    hls_url,
                    "-c",
                    "copy",
                    "-bsf:a",
                    "aac_adtstoasc",
                    "-y",
                    str(output_file),
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and output_file.exists():
                    size = output_file.stat().st_size
                    print(f"\n=== SUCCESS ===")
                    print(f"Downloaded: {output_file}")
                    print(f"Size: {size / 1024 / 1024:.2f} MB")
                else:
                    print(f"Error: {result.stderr[:500]}")
