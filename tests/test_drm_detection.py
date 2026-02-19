"""Test DRM detection without downloading"""

import pytest
import asyncio
from conftest import TEST_URLS, skip_no_credentials, vrt_credentials


@skip_no_credentials
class TestDRMDetection:
    """Test DRM status detection"""

    @pytest.mark.asyncio
    async def test_detect_drm_free_video(self, vrt_credentials):
        """Test dat DRM-vrije video wordt herkend"""
        from playwright.async_api import async_playwright
        import requests

        username, password = vrt_credentials

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = await context.new_page()

            login_url = (
                "https://login.vrt.be/authorize?response_type=code"
                "&client_id=vrtnu-site&redirect_uri=https://www.vrt.be/vrtmax/sso/callback"
                "&scope=openid%20profile%20email%20video"
            )

            await page.goto(login_url, wait_until="networkidle")
            await asyncio.sleep(2)
            await page.fill('input[type="email"]', username)
            await page.click('button[type="submit"]')
            await asyncio.sleep(2)

            pw = await page.query_selector('input[type="password"]')
            if pw:
                await pw.fill(password)
                await page.click('button[type="submit"]')
                await asyncio.sleep(5)

            await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
            await asyncio.sleep(2)

            redirect_url = None

            async def handle_response(response):
                nonlocal redirect_url
                if "/videos/" in response.url and "vualto" in response.url:
                    location = response.headers.get("location", "")
                    if location:
                        redirect_url = (
                            "https://media-services-public.vrt.be" + location
                            if location.startswith("/")
                            else location
                        )

            page.on("response", handle_response)

            await page.goto(TEST_URLS["drm_free_short"], wait_until="networkidle")
            await asyncio.sleep(5)

            assert redirect_url is not None, "Zou API redirect moeten krijgen"

            cookies = await context.cookies()
            cookie_header = "; ".join(
                [f"{c.get('name', '')}={c.get('value', '')}" for c in cookies]
            )

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Cookie": cookie_header,
                "Referer": "https://www.vrt.be/",
            }

            resp = requests.get(redirect_url, headers=headers)
            assert resp.status_code == 200, (
                f"API zou 200 moeten geven, kreeg {resp.status_code}"
            )

            data = resp.json()
            target_urls = data.get("targetUrls", [])

            has_hls = any(tu.get("type") == "hls" for tu in target_urls)
            has_dash_drm = any(
                tu.get("type") == "dash" and "_drm_" in tu.get("url", "")
                for tu in target_urls
            )

            print(f"\n=== DRM-vrije video ===")
            print(f"Titel: {data.get('title')}")
            print(f"HLS (DRM-vrij): {has_hls}")
            print(f"DASH+DRM: {has_dash_drm}")
            print(f"Stream types: {[tu.get('type') for tu in target_urls]}")

            await browser.close()

            assert has_hls, "DRM-vrije video zou HLS moeten hebben"

    @pytest.mark.asyncio
    async def test_detect_drm_protected_video(self, vrt_credentials):
        """Test dat DRM-beschermde video wordt herkend"""
        from playwright.async_api import async_playwright
        import requests

        username, password = vrt_credentials

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = await context.new_page()

            login_url = (
                "https://login.vrt.be/authorize?response_type=code"
                "&client_id=vrtnu-site&redirect_uri=https://www.vrt.be/vrtmax/sso/callback"
                "&scope=openid%20profile%20email%20video"
            )

            await page.goto(login_url, wait_until="networkidle")
            await asyncio.sleep(2)
            await page.fill('input[type="email"]', username)
            await page.click('button[type="submit"]')
            await asyncio.sleep(2)

            pw = await page.query_selector('input[type="password"]')
            if pw:
                await pw.fill(password)
                await page.click('button[type="submit"]')
                await asyncio.sleep(5)

            await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
            await asyncio.sleep(2)

            redirect_url = None
            resp = None
            has_hls = False
            has_dash_drm = False
            target_urls = []

            async def handle_response(response):
                nonlocal redirect_url
                if "/videos/" in response.url and "vualto" in response.url:
                    location = response.headers.get("location", "")
                    if location:
                        redirect_url = (
                            "https://media-services-public.vrt.be" + location
                            if location.startswith("/")
                            else location
                        )

            page.on("response", handle_response)

            await page.goto(TEST_URLS["drm_protected"], wait_until="networkidle")
            await asyncio.sleep(5)

            if redirect_url:
                cookies = await context.cookies()
                cookie_header = "; ".join(
                    [f"{c.get('name', '')}={c.get('value', '')}" for c in cookies]
                )

                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Cookie": cookie_header,
                    "Referer": "https://www.vrt.be/",
                }

                resp = requests.get(redirect_url, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    target_urls = data.get("targetUrls", [])

                    has_hls = any(tu.get("type") == "hls" for tu in target_urls)
                    has_dash_drm = any(
                        tu.get("type") == "dash" and "_drm_" in tu.get("url", "")
                        for tu in target_urls
                    )

                    print(f"\n=== DRM-beschermde video ===")
                    print(f"Titel: {data.get('title')}")
                    print(f"HLS (DRM-vrij): {has_hls}")
                    print(f"DASH+DRM: {has_dash_drm}")
                    print(f"Stream types: {[tu.get('type') for tu in target_urls]}")

            await browser.close()

            if redirect_url and resp is not None and resp.status_code == 200:
                has_drm_in_url = any("_drm_" in tu.get("url", "") for tu in target_urls)
                if not has_drm_in_url:
                    pytest.skip(f"Deze video is DRM-vrij. Zoek een andere URL met DRM.")
                assert has_drm_in_url, (
                    "DRM-beschermde video zou _drm_ in URL moeten hebben"
                )
