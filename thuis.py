#!/usr/bin/env python3
"""
Thuis

Download video's van VRT MAX met automatische authenticatie.

Gebruik:
    python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
    python thuis.py --setup          # Eerste keer configuratie
    python thuis.py --help           # Help tonen
"""

import asyncio
import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import requests
from playwright.async_api import async_playwright

CONFIG_FILE = Path(__file__).parent / ".env"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def setup():
    """Interactieve configuratie voor eerste keer"""
    print("=" * 50, flush=True)
    print("Thuis - Eerste keer setup", flush=True)
    print("=" * 50, flush=True)
    print("\nJe VRT MAX credentials worden opgeslagen in .env", flush=True)
    print("WAARSCHUWING: Wachtwoord wordt ongecodeerd opgeslagen!\n", flush=True)

    username = input("VRT MAX email: ").strip()
    password = input("VRT MAX wachtwoord: ").strip()

    if not username or not password:
        print("ERROR: Email en wachtwoord zijn verplicht", flush=True)
        sys.exit(1)

    with open(CONFIG_FILE, "w") as f:
        f.write(f"VRT_USERNAME={username}\n")
        f.write(f"VRT_PASSWORD={password}\n")

    print(f"\nCredentials opgeslagen in {CONFIG_FILE}", flush=True)
    print("Je kan nu video's downloaden!", flush=True)


def check_ffmpeg():
    """Controleer of ffmpeg geïnstalleerd is"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def download_with_ffmpeg(stream_url: str, output_path: Path, title: str):
    """Download video met ffmpeg"""
    print(f"Downloaden naar: {output_path}", flush=True)

    cmd = [
        "ffmpeg",
        "-i",
        stream_url,
        "-c",
        "copy",
        "-bsf:a",
        "aac_adtstoasc",
        "-progress",
        "pipe:1",
        "-y",
        str(output_path),
    ]

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line.strip():
                print(f"  {line.strip()}", flush=True)

        returncode = process.wait()

        if returncode == 0 and output_path.exists():
            size = output_path.stat().st_size
            return True, size
        else:
            error = process.stderr.read() if process.stderr else "Onbekende fout"
            return False, error
    except Exception as e:
        return False, str(e)


async def download_video(
    video_url: str,
    username: str,
    password: str,
    output_path: Optional[Path] = None,
    headless: bool = True,
):
    """Download een VRT MAX video"""

    print(f"Video: {video_url}\n", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, user_agent=USER_AGENT
        )
        page = await context.new_page()

        # Stap 1: Inloggen
        print("Stap 1: Inloggen...", flush=True)

        redirect_uri = "https://www.vrt.be/vrtmax/sso/callback"
        login_url = (
            f"https://login.vrt.be/authorize?response_type=code"
            f"&client_id=vrtnu-site&redirect_uri={redirect_uri}"
            f"&scope=openid%20profile%20email%20video"
        )

        await page.goto(login_url, wait_until="networkidle")
        await asyncio.sleep(3)

        await page.fill('input[type="email"]', username)
        await page.click('button[type="submit"]')
        await asyncio.sleep(3)

        pw = await page.query_selector('input[type="password"]')
        if pw:
            await pw.fill(password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(8)

        if "login" in page.url.lower():
            print("FOUT: Inloggen mislukt", flush=True)
            return False

        print("  Ingelogd!\n", flush=True)

        # Stap 2: Naar VRT MAX
        print("Stap 2: Stream ophalen...", flush=True)
        await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        await asyncio.sleep(3)

        # Stap 3: Stream URL
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

        await page.goto(video_url, wait_until="networkidle")
        await asyncio.sleep(8)

        if not redirect_url:
            print("FOUT: Kon stream URL niet ophalen", flush=True)
            return False

        cookies = await context.cookies()
        cookie_header = "; ".join(
            [f"{c.get('name', '')}={c.get('value', '')}" for c in cookies]
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": cookie_header,
            "Referer": "https://www.vrt.be/",
        }

        resp = requests.get(redirect_url, headers=headers)

        if resp.status_code != 200:
            print(f"FOUT: API gaf status {resp.status_code}", flush=True)
            return False

        data = resp.json()
        title = data.get("title", "video")
        print(f"  Titel: {title}\n", flush=True)

        stream_url = None
        for tu in data.get("targetUrls", []):
            if tu.get("type") == "hls":
                stream_url = tu.get("url")
                break

        if not stream_url:
            print("FOUT: Geen HLS stream gevonden", flush=True)
            return False

        # Stap 4: Downloaden
        print("Stap 3: Downloaden...", flush=True)

        if not output_path:
            output_dir = Path("media")
            output_dir.mkdir(exist_ok=True)
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            output_path = output_dir / f"{safe_title}.mp4"

        success, result = download_with_ffmpeg(stream_url, output_path, title)

        if success:
            size_mb = int(result) / 1024 / 1024
            print(f"\n  SUCCES!", flush=True)
            print(f"  Opgeslagen: {output_path}", flush=True)
            print(f"  Grootte: {size_mb:.2f} MB", flush=True)
            return True
        else:
            error_msg = str(result)
            print(f"  FOUT: {error_msg[:200]}", flush=True)
            return False

        await browser.close()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Thuis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
  python thuis.py --setup
  python thuis.py "url" -o "output.mp4"
  python thuis.py "url" --no-headless
        """,
    )

    parser.add_argument("url", nargs="?", help="VRT MAX video URL")
    parser.add_argument(
        "-u", "--username", default=os.getenv("VRT_USERNAME"), help="VRT MAX email"
    )
    parser.add_argument(
        "-p", "--password", default=os.getenv("VRT_PASSWORD"), help="VRT MAX wachtwoord"
    )
    parser.add_argument("-o", "--output", help="Output bestand")
    parser.add_argument("--setup", action="store_true", help="Eerste keer configuratie")
    parser.add_argument(
        "--no-headless", action="store_true", help="Toon browser venster"
    )

    args = parser.parse_args()

    if args.setup:
        setup()
        return

    if not check_ffmpeg():
        print("FOUT: ffmpeg is niet geïnstalleerd", flush=True)
        print("Installeer ffmpeg eerst:", flush=True)
        print("  Ubuntu/Debian: sudo apt install ffmpeg", flush=True)
        print("  Mac: brew install ffmpeg", flush=True)
        print("  Windows: winget install ffmpeg", flush=True)
        sys.exit(1)

    if not args.username or not args.password:
        print("Geen credentials gevonden.", flush=True)
        print("Gebruik: python thuis.py --setup", flush=True)
        print(
            "Of geef credentials mee: python thuis.py <url> -u <email> -p <wachtwoord>",
            flush=True,
        )
        sys.exit(1)

    if not args.url:
        parser.print_help()
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    success = asyncio.run(
        download_video(
            video_url=args.url,
            username=args.username,
            password=args.password,
            output_path=output_path,
            headless=not args.no_headless,
        )
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
