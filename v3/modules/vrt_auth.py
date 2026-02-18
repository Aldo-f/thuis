"""VRT MAX Authentication Module"""

import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import os


class VRTAuthenticator:
    VRT_LOGIN_URL = "https://login.vrt.be/authorize"
    VRT_MAX_BASE = "https://www.vrt.be/vrtmax"

    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.page = await self.context.new_page()

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self) -> bool:
        if not self.page:
            await self.start_browser()

        try:
            await self.page.goto(self.VRT_LOGIN_URL, wait_until="networkidle")
            await asyncio.sleep(2)

            email_input = await self.page.query_selector(
                'input[type="email"], input[name="username"], input[id="email"]'
            )
            if email_input:
                await email_input.fill(self.username)
                await asyncio.sleep(0.5)

                password_input = await self.page.query_selector(
                    'input[type="password"]'
                )
                if password_input:
                    await password_input.fill(self.password)
                    await asyncio.sleep(0.5)

                    submit_btn = await self.page.query_selector(
                        'button[type="submit"], input[type="submit"], button:has-text("Log in"), button:has-text("Aanmelden")'
                    )
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(3)

                        if "vrt.be" in self.page.url or "vrtmax" in self.page.url:
                            return True

            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def navigate_to_video(self, video_url: str) -> bool:
        if not self.page:
            return False

        try:
            await self.page.goto(video_url, wait_until="networkidle")
            await asyncio.sleep(3)

            play_button = await self.page.query_selector(
                'button[aria-label*="play"], button:has-text("Play"), .vjs-big-play-button'
            )
            if play_button:
                await play_button.click()
                await asyncio.sleep(5)

            return True
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    def get_page(self) -> Optional[Page]:
        return self.page

    async def get_cookies(self) -> dict:
        if self.context:
            return await self.context.cookies()
        return {}
