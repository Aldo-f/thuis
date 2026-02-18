"""Test VRT MAX video extraction"""

import pytest
import asyncio
from pathlib import Path

TEST_URLS = [
    "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/",
    "https://www.vrt.be/vrtmax/a-z/den-elfde-van-den-elfde/1/den-elfde-van-den-elfde-s1a1/",
]


class TestVRTMaxExtraction:
    """Tests for VRT MAX video extraction"""

    @pytest.mark.asyncio
    async def test_explore_page_structure(self):
        """Explore VRT MAX page to understand structure"""
        from playwright.async_api import async_playwright

        url = TEST_URLS[0]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, wait_until="networkidle")

            page_content = await page.content()

            title = await page.title()

            video_elements = await page.query_selector_all("video")

            data_videoid = await page.query_selector("[data-video-id]")
            data_mediainfo = await page.query_selector("[data-media-info]")

            scripts = await page.query_selector_all("script")
            script_contents = []
            for script in scripts:
                content = await script.inner_text()
                if content and (
                    "mvpId" in content
                    or "mediaId" in content
                    or "videoId" in content
                    or "mpd" in content.lower()
                ):
                    script_contents.append(content[:500])

            await browser.close()

            assert len(page_content) > 0, "Page content should not be empty"
            assert "vrt" in page_content.lower() or "max" in page_content.lower(), (
                "Should be VRT MAX page"
            )

            print(f"\n=== Page Analysis ===")
            print(f"Title: {title}")
            print(f"Video elements found: {len(video_elements)}")
            print(f"Has data-video-id: {data_videoid is not None}")
            print(f"Has data-media-info: {data_mediainfo is not None}")
            print(f"Relevant scripts: {len(script_contents)}")

            if script_contents:
                print("\n=== Script snippets ===")
                for i, content in enumerate(script_contents[:3]):
                    print(f"Script {i}: {content[:200]}...")

    @pytest.mark.asyncio
    async def test_extract_video_id_from_page(self):
        """Test extracting video ID from VRT MAX page"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()
        url = TEST_URLS[0]

        video_id = await scraper.extract_video_id(url)

        assert video_id is not None, "Should extract video ID"
        assert len(video_id) > 5, "Video ID should be meaningful"

        print(f"Extracted video ID: {video_id}")

    @pytest.mark.asyncio
    async def test_extract_mvp_id_from_page(self):
        """Test extracting MVP ID from VRT MAX page"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()
        url = TEST_URLS[0]

        mvp_id = await scraper.extract_mvp_id(url)

        assert mvp_id is not None, "Should extract MVP ID"

        print(f"Extracted MVP ID: {mvp_id}")

    @pytest.mark.asyncio
    async def test_get_video_metadata_without_login(self):
        """Test getting video metadata without login"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()
        url = TEST_URLS[0]

        metadata = await scraper.get_video_metadata(url)

        assert metadata is not None, "Should get metadata"
        assert "title" in metadata, "Should have title"

        print(f"Metadata: {metadata}")

    @pytest.mark.asyncio
    async def test_get_stream_url_without_login(self):
        """Test getting stream URL without login (for DRM-free content)"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()
        url = TEST_URLS[0]

        stream_info = await scraper.get_stream_info(url)

        print(f"Stream info: {stream_info}")

        if stream_info and stream_info.is_drm_free:
            assert stream_info.stream_url is not None, (
                "Should have stream URL for DRM-free content"
            )

    @pytest.mark.asyncio
    async def test_detect_drm_status(self):
        """Test detecting if video has DRM"""
        from modules.vrt_scraper import VRTMaxScraper

        scraper = VRTMaxScraper()
        url = TEST_URLS[1]

        stream_info = await scraper.get_stream_info(url)

        assert stream_info is not None, "Should get stream info"
        assert stream_info.has_drm is not None, "Should have DRM status"

        print(f"Has DRM: {stream_info.has_drm}")

    @pytest.mark.asyncio
    async def test_capture_network_requests(self):
        """Capture network requests to find MPD and license URLs"""
        from playwright.async_api import async_playwright

        url = TEST_URLS[0]

        mpd_urls = []
        license_urls = []
        media_urls = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            def handle_response(response):
                req_url = response.url
                if ".mpd" in req_url or "manifest" in req_url.lower():
                    mpd_urls.append(req_url)
                    print(f"[MPD] {req_url}")
                elif (
                    "license" in req_url.lower()
                    or "widevine" in req_url.lower()
                    or "drm" in req_url.lower()
                ):
                    license_urls.append(
                        {
                            "url": req_url,
                            "status": response.status,
                            "headers": dict(response.headers),
                        }
                    )
                    print(f"[LICENSE] {req_url}")
                elif any(ext in req_url for ext in [".m3u8", ".mp4", ".m4s", ".ts"]):
                    media_urls.append(req_url)

            page.on("response", handle_response)

            await page.goto(url, wait_until="networkidle")

            play_button = await page.query_selector(
                'button[aria-label*="play"], .vjs-big-play-button, button:has-text("Play")'
            )
            if play_button:
                print("Found play button, clicking...")
                await play_button.click()
                await asyncio.sleep(5)
            else:
                video = await page.query_selector("video")
                if video:
                    print("Found video element, trying to play...")
                    await video.evaluate("v => { if (v.play) v.play(); }")
                    await asyncio.sleep(5)

            await browser.close()

        print(f"\n=== Network Capture Results ===")
        print(f"MPD URLs: {len(mpd_urls)}")
        for mpd in mpd_urls:
            print(f"  - {mpd}")
        print(f"License URLs: {len(license_urls)}")
        for lic in license_urls:
            print(f"  - {lic['url']}")
        print(f"Media URLs: {len(media_urls)}")

        assert len(mpd_urls) > 0 or len(media_urls) > 0, (
            "Should find at least one media URL"
        )
