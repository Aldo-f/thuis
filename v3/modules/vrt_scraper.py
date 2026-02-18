"""VRT MAX scraper module"""

import asyncio
import re
import json
import requests
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class StreamInfo:
    video_id: Optional[str] = None
    publication_id: Optional[str] = None
    mvp_id: Optional[str] = None
    title: Optional[str] = None
    stream_url: Optional[str] = None
    mpd_url: Optional[str] = None
    has_drm: bool = False
    is_drm_free: bool = False
    pssh: Optional[str] = None
    license_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    player_token: Optional[str] = None


class VRTMaxScraper:
    VRT_MAX_BASE = "https://www.vrt.be/vrtmax"
    VRT_API_BASE = "https://www.vrt.be/vrtmax/a-z"
    TOKEN_API = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens"
    VIDEO_API = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/videos"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.context = None
        self.player_token: Optional[str] = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.page = await self.context.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self, username: str, password: str) -> bool:
        """Login to VRT MAX"""
        if not self.page:
            await self.start()

        redirect_uri = "https://www.vrt.be/vrtmax/sso/callback"
        login_url = f"https://login.vrt.be/authorize?response_type=code&client_id=vrtnu-site&redirect_uri={redirect_uri}&scope=openid%20profile%20email%20video"

        try:
            await self.page.goto(login_url, wait_until="networkidle")
            await asyncio.sleep(3)

            email_input = await self.page.query_selector('input[type="email"]')
            if email_input:
                await email_input.fill(username)
                await asyncio.sleep(1)

                submit_btn = await self.page.query_selector('button[type="submit"]')
                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(3)

                password_input = await self.page.query_selector(
                    'input[type="password"]'
                )
                if password_input:
                    await password_input.fill(password)
                    await asyncio.sleep(0.5)

                    submit_btn2 = await self.page.query_selector(
                        'button[type="submit"]'
                    )
                    if submit_btn2:
                        await submit_btn2.click()
                        await asyncio.sleep(8)

                        current_url = self.page.url
                        if (
                            "vrt.be" in current_url
                            and "login" not in current_url.lower()
                        ):
                            print(f"Login successful, redirected to: {self.page.url}")
                            return True

            print(f"Login failed. Current URL: {self.page.url}")
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def get_player_token(self) -> Optional[str]:
        """Get player token from VRT"""
        if not self.page:
            await self.start()

        token = None

        async def handle_response(response):
            nonlocal token
            if "/tokens" in response.url and "vualto" in response.url:
                try:
                    data = await response.json()
                    token = data.get("vrtPlayerToken")
                    print(f"Got player token: {token[:50]}..." if token else "No token")
                except:
                    pass

        self.page.on("response", handle_response)

        # First go to VRT MAX homepage to trigger token
        await self.page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        self.player_token = token
        return token

    async def navigate(self, url: str) -> bool:
        if not self.page:
            await self.start()

        try:
            await self.page.goto(url, wait_until="networkidle")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    async def extract_video_id(self, url: str) -> Optional[str]:
        if not self.page:
            await self.start()

        if not await self.navigate(url):
            return None

        content = await self.page.content()

        patterns = [
            r'"videoId"\s*:\s*"([^"]+)"',
            r'"mvpId"\s*:\s*"([^"]+)"',
            r'"mediaId"\s*:\s*"([^"]+)"',
            r'data-video-id="([^"]+)"',
            r"/vid-([a-f0-9-]+)",
            r'video[_-]?id["\s:=]+([a-zA-Z0-9-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        # Try to get from JSON-LD
        json_ld_scripts = await self.page.query_selector_all(
            'script[type="application/ld+json"]'
        )
        for script in json_ld_scripts:
            try:
                content = await script.inner_text()
                data = json.loads(content)
                if isinstance(data, dict):
                    # Get video ID from nested video object
                    if "video" in data and isinstance(data["video"], dict):
                        vid = data["video"].get("@id", "")
                        if vid.startswith("vid-"):
                            return vid
                    # Or from @id directly
                    vid = data.get("@id", "")
                    if vid.startswith("vid-"):
                        return vid
            except:
                pass

        url_pattern = r"/([a-z0-9-]+)(?:/)?$"
        match = re.search(url_pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    async def extract_publication_id(self, url: str) -> Optional[str]:
        """Extract publication ID from page"""
        if not self.page:
            await self.start()

        if not await self.navigate(url):
            return None

        # Get from JSON-LD
        json_ld_scripts = await self.page.query_selector_all(
            'script[type="application/ld+json"]'
        )
        for script in json_ld_scripts:
            try:
                content = await script.inner_text()
                data = json.loads(content)
                if isinstance(data, dict):
                    # Look for publication with @id starting with pbs-pub-
                    publications = data.get("publication", [])
                    for pub in publications:
                        pub_id = pub.get("@id", "")
                        if pub_id.startswith("pbs-pub-"):
                            return pub_id
            except:
                pass

        return None

    async def extract_mvp_id(self, url: str) -> Optional[str]:
        if not self.page:
            await self.start()

        if not await self.navigate(url):
            return None

        content = await self.page.content()

        patterns = [
            r'"mvpId"\s*:\s*"([^"]+)"',
            r'mvpId["\s:=]+([a-zA-Z0-9_-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def get_video_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        if not self.page:
            await self.start()

        if not await self.navigate(url):
            return None

        title = await self.page.title()

        json_ld_scripts = await self.page.query_selector_all(
            'script[type="application/ld+json"]'
        )
        metadata = {"title": title}

        for script in json_ld_scripts:
            try:
                content = await script.inner_text()
                data = json.loads(content)
                metadata.update(data)
            except:
                pass

        meta_description = await self.page.query_selector('meta[name="description"]')
        if meta_description:
            desc = await meta_description.get_attribute("content")
            if desc:
                metadata["description"] = desc

        return metadata

    async def get_stream_info(self, url: str) -> Optional[StreamInfo]:
        if not self.page:
            await self.start()

        if not await self.navigate(url):
            return None

        stream_info = StreamInfo()

        stream_info.video_id = await self.extract_video_id(url)
        stream_info.publication_id = await self.extract_publication_id(url)
        stream_info.mvp_id = await self.extract_mvp_id(url)
        stream_info.metadata = await self.get_video_metadata(url)
        if stream_info.metadata:
            stream_info.title = stream_info.metadata.get("title")

        video_element = await self.page.query_selector("video")
        if video_element:
            src = await video_element.get_attribute("src")
            if src:
                stream_info.stream_url = src
                stream_info.is_drm_free = True

        content = await self.page.content()

        mpd_patterns = [
            r'(https?://[^\s"\'<>]+\.mpd[^\s"\'<>]*)',
            r'"url"\s*:\s*"(https?://[^\s"\'<>]+\.mpd[^\s"\'<>]*)"',
        ]

        for pattern in mpd_patterns:
            match = re.search(pattern, content)
            if match:
                stream_info.mpd_url = match.group(1)
                break

        drm_indicators = [
            "widevine",
            "playready",
            "fairplay",
            "drm",
            "license",
            "encrypted",
            "cenc",
        ]

        content_lower = content.lower()
        for indicator in drm_indicators:
            if indicator in content_lower:
                stream_info.has_drm = True
                break

        if stream_info.stream_url and not stream_info.has_drm:
            stream_info.is_drm_free = True

        # Try to get stream via API if not found on page
        if not stream_info.stream_url and not stream_info.mpd_url:
            api_stream_info = await self._get_stream_via_api(
                stream_info.video_id, stream_info.publication_id
            )
            if api_stream_info:
                stream_info.stream_url = api_stream_info.get("stream_url")
                stream_info.mpd_url = api_stream_info.get("mpd_url")
                stream_info.has_drm = api_stream_info.get("has_drm", False)
                stream_info.is_drm_free = api_stream_info.get("is_drm_free", False)
                stream_info.player_token = self.player_token

        return stream_info

    async def _get_stream_via_api(
        self, video_id: Optional[str], publication_id: Optional[str]
    ) -> Optional[Dict]:
        """Get stream URL via VRT API"""
        if not self.player_token:
            await self.get_player_token()

        if not self.player_token:
            print("No player token available")
            return None

        # Build video ID from publication and video
        if publication_id and video_id:
            full_video_id = f"{publication_id}${video_id}"
        elif video_id:
            full_video_id = video_id
        else:
            return None

        # Try the video API
        api_url = f"{self.VIDEO_API}/{full_video_id}?vrtPlayerToken={self.player_token}&client=vrtnu-web@PROD"

        print(f"Calling video API: {api_url[:100]}...")

        try:
            resp = requests.get(api_url, allow_redirects=True)
            print(f"Video API status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Video API response keys: {list(data.keys())}")

                result = {}

                # Get target URLs (HLS or DASH)
                target_urls = data.get("targetUrls", [])
                for tu in target_urls:
                    url_type = tu.get("type", "")
                    stream_url = tu.get("url", "")

                    if url_type == "hls" and not result.get("stream_url"):
                        result["stream_url"] = stream_url
                    elif url_type == "mpeg_dash" and not result.get("mpd_url"):
                        result["mpd_url"] = stream_url

                # Check DRM
                drm_impl = data.get("drmImplementation")
                result["has_drm"] = drm_impl not in [None, "NoDrm", ""]
                result["is_drm_free"] = (
                    drm_impl in [None, "NoDrm", ""] or drm_impl == ""
                )

                # Get title
                result["title"] = data.get("title")

                print(
                    f"Stream URL: {result.get('stream_url', 'None')[:100] if result.get('stream_url') else 'None'}"
                )
                print(
                    f"MPD URL: {result.get('mpd_url', 'None')[:100] if result.get('mpd_url') else 'None'}"
                )
                print(f"DRM: {drm_impl}, is_drm_free: {result['is_drm_free']}")

                return result
            else:
                print(f"API error: {resp.text[:200]}")

        except Exception as e:
            print(f"API error: {e}")

        return None
