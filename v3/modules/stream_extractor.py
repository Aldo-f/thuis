"""Stream and Key Extraction Module"""

import asyncio
import re
import json
from playwright.async_api import Page
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class StreamInfo:
    mpd_url: str
    pssh: Optional[str] = None
    license_url: Optional[str] = None
    license_headers: Optional[Dict[str, str]] = None
    keys: Optional[List[str]] = None


class StreamExtractor:
    EME_CAPTURE_SCRIPT = """
    window.__emeData = {
        pssh: null,
        licenseRequests: [],
        licenseResponses: []
    };
    
    const originalCreateMediaKeys = navigator.requestMediaKeySystemAccess ? 
        MediaKeySystemAccess.prototype.createMediaKeys : null;
    
    if (originalCreateMediaKeys) {
        MediaKeySystemAccess.prototype.createMediaKeys = function() {
            return originalCreateMediaKeys.apply(this).then(mediaKeys => {
                const originalCreateSession = mediaKeys.createSession.bind(mediaKeys);
                mediaKeys.createSession = function(sessionType) {
                    const session = originalCreateSession(sessionType);
                    
                    session.generateRequest = function(initDataType, initData) {
                        if (initDataType === 'cenc' || initDataType === 'webm') {
                            const pssh = btoa(String.fromCharCode.apply(null, new Uint8Array(initData)));
                            window.__emeData.pssh = pssh;
                            console.log('[EME-CAPTURE] PSSH:', pssh);
                        }
                        return Object.getPrototypeOf(session).generateRequest.call(this, initDataType, initData);
                    };
                    
                    const originalUpdate = session.update.bind(session);
                    session.update = function(response) {
                        const responseStr = btoa(String.fromCharCode.apply(null, new Uint8Array(response)));
                        window.__emeData.licenseResponses.push(responseStr);
                        console.log('[EME-CAPTURE] License Response:', responseStr.substring(0, 100) + '...');
                        return originalUpdate(response);
                    };
                    
                    return session;
                };
                return mediaKeys;
            });
        };
    }
    """

    LICENSE_CAPTURE_SCRIPT = """
    window.__licenseUrls = [];
    
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);
        const url = args[0];
        const options = args[1] || {};
        
        if (url && (url.includes('license') || url.includes('widevine') || url.includes('drm'))) {
            console.log('[LICENSE-CAPTURE] URL:', url);
            console.log('[LICENSE-CAPTURE] Headers:', JSON.stringify(options.headers));
            window.__licenseUrls.push({
                url: url,
                headers: options.headers || {}
            });
        }
        
        return response;
    };
    
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this.__url = url;
        this.__method = method;
        return originalXHROpen.apply(this, [method, url, ...rest]);
    };
    
    XMLHttpRequest.prototype.send = function(body) {
        if (this.__url && (this.__url.includes('license') || this.__url.includes('widevine') || this.__url.includes('drm'))) {
            console.log('[LICENSE-CAPTURE-XHR] URL:', this.__url);
            window.__licenseUrls.push({
                url: this.__url,
                method: this.__method,
                body: body
            });
        }
        return originalXHRSend.apply(this, [body]);
    };
    """

    def __init__(self, page: Page):
        self.page = page
        self.stream_info: Optional[StreamInfo] = None

    async def inject_capture_scripts(self):
        await self.page.evaluate(self.EME_CAPTURE_SCRIPT)
        await self.page.evaluate(self.LICENSE_CAPTURE_SCRIPT)

    async def capture_network_requests(self):
        mpd_urls = []
        license_urls = []

        async def handle_response(response):
            url = response.url
            if ".mpd" in url or "manifest" in url.lower():
                mpd_urls.append(url)
                print(f"[MPD Found] {url}")
            elif (
                "license" in url.lower()
                or "widevine" in url.lower()
                or "drm" in url.lower()
            ):
                license_urls.append({"url": url, "headers": response.headers})
                print(f"[License URL Found] {url}")

        self.page.on("response", handle_response)
        return mpd_urls, license_urls

    async def extract_stream_info(self) -> Optional[StreamInfo]:
        await asyncio.sleep(2)

        mpd_url = await self._extract_mpd_url()
        pssh = await self._extract_pssh()
        license_data = await self._extract_license_data()

        if mpd_url:
            self.stream_info = StreamInfo(
                mpd_url=mpd_url,
                pssh=pssh,
                license_url=license_data.get("url") if license_data else None,
                license_headers=license_data.get("headers") if license_data else None,
            )
            return self.stream_info

        return None

    async def _extract_mpd_url(self) -> Optional[str]:
        video_elements = await self.page.query_selector_all("video")

        for video in video_elements:
            src = await video.get_attribute("src")
            if src and ".mpd" in src:
                return src

        mpd_in_page = await self.page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                for (const script of scripts) {
                    const content = script.textContent || script.innerHTML;
                    const mpdMatch = content.match(/["'](https?:\\/\\/[^"']+\\.mpd[^"']*)["']/g);
                    if (mpdMatch) {
                        return mpdMatch[0].replace(/["']/g, '');
                    }
                }
                return null;
            }
        """)

        return mpd_in_page

    async def _extract_pssh(self) -> Optional[str]:
        pssh = await self.page.evaluate("window.__emeData?.pssh")
        return pssh

    async def _extract_license_data(self) -> Optional[Dict]:
        license_urls = await self.page.evaluate("window.__licenseUrls")

        if license_urls and len(license_urls) > 0:
            return license_urls[-1]

        return None

    async def get_manifest_content(self, mpd_url: str) -> Optional[str]:
        try:
            response = await self.page.evaluate(f'''
                async () => {{
                    const response = await fetch("{mpd_url}");
                    return await response.text();
                }}
            ''')
            return response
        except Exception as e:
            print(f"Error fetching manifest: {e}")
            return None
