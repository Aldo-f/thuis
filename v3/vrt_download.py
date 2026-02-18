#!/usr/bin/env python3
"""
VRT MAX Downloader - Thuis v3

Download video's van VRT MAX met automatische authenticatie.
"""

import asyncio
import argparse
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import requests
from playwright.async_api import async_playwright


async def download_vrt_max(
    video_url: str,
    username: str,
    password: str,
    output_path: str = None,
    headless: bool = True,
) -> bool:
    """Download een VRT MAX video"""

    print(f"=== VRT MAX Downloader ===\n")
    print(f"Video: {video_url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await context.new_page()

        # Stap 1: Inloggen
        print("Stap 1: Inloggen...")
        redirect_uri = "https://www.vrt.be/vrtmax/sso/callback"
        login_url = (
            f"https://login.vrt.be/authorize?response_type=code"
            f"&client_id=vrtnu-site&redirect_uri={redirect_uri}"
            f"&scope=openid%20profile%20email%20video"
        )

        await page.goto(login_url, wait_until="networkidle")
        await asyncio.sleep(5)

        await page.fill('input[type="email"]', username)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)

        pw = await page.query_selector('input[type="password"]')
        if pw:
            await pw.fill(password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(10)

        print("Ingelogd!\n")

        # Stap 2: Naar VRT MAX
        print("Stap 2: VRT MAX openen...")
        await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(5)

        # Stap 3: Stream URL ophalen
        print("Stream URL ophalen...")
        redirect_url = None

        async def handle_response(response):
            nonlocal redirect_url
            url = response.url
            if "/videos/" in url and "vualto" in url:
                location = response.headers.get("location", "")
                if location:
                    if location.startswith("/"):
                        redirect_url = "https://media-services-public.vrt.be" + location
                    else:
                        redirect_url = location

        page.on("response", handle_response)

        await page.goto(video_url, wait_until="networkidle")
        await asyncio.sleep(10)

        if not redirect_url:
            print("FOUT: Kon stream URL niet ophalen")
            return False

        # Cookies ophalen
        cookies = await context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_header,
            "Referer": "https://www.vrt.be/",
        }

        resp = requests.get(redirect_url, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", "video")
            print(f"Titel: {title}\n")

            # Stream URL
            stream_url = None
            for tu in data.get("targetUrls", []):
                if tu.get("type") == "hls":
                    stream_url = tu.get("url")
                    break

            if not stream_url:
                print("FOUT: Geen HLS stream gevonden")
                return False

            # Stap 4: Downloaden
            print("Downloaden...\n")

            if not output_path:
                output_dir = Path("media")
                output_dir.mkdir(exist_ok=True)
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in " -_"
                ).strip()
                output_path = output_dir / f"{safe_title}.mp4"

            cmd = [
                "ffmpeg",
                "-i",
                stream_url,
                "-c",
                "copy",
                "-bsf:a",
                "aac_adtstoasc",
                "-y",
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0 and output_path.exists():
                size = output_path.stat().st_size
                print(f"\n=== SUCCES ===")
                print(f"Gedownload: {output_path}")
                print(f"Grootte: {size / 1024 / 1024:.2f} MB")
                return True
            else:
                print(
                    f"FOUT: {result.stderr[:500] if result.stderr else 'Onbekende fout'}"
                )
                return False
        else:
            print(f"FOUT: API gaf {resp.status_code}")
            return False

        await browser.close()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Download VRT MAX video's")
    parser.add_argument("url", help="VRT MAX video URL")
    parser.add_argument(
        "-u",
        "--username",
        default=os.getenv("VRT_USERNAME"),
        help="VRT MAX gebruikersnaam",
    )
    parser.add_argument(
        "-p", "--password", default=os.getenv("VRT_PASSWORD"), help="VRT MAX wachtwoord"
    )
    parser.add_argument("-o", "--output", help="Output bestand")
    parser.add_argument(
        "--no-headless", action="store_true", help="Toon browser venster"
    )

    args = parser.parse_args()

    if not args.username or not args.password:
        print("Gebruik: python v3.py <url> -u <email> -p <wachtwoord>")
        print("Of stel VRT_USERNAME en VRT_PASSWORD in in .env")
        exit(1)

    success = asyncio.run(
        download_vrt_max(
            video_url=args.url,
            username=args.username,
            password=args.password,
            output_path=args.output,
            headless=not args.no_headless,
        )
    )

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
