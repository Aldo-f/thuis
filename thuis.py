#!/usr/bin/env python3
"""
Thuis v3.0.0

Download video's van VRT MAX met automatische authenticatie.

Gebruik:
    python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
    python thuis.py --setup          # Eerste keer configuratie
    python thuis.py --help           # Help tonen
"""

import asyncio
import argparse
import json
import os
import random
import re
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
import requests
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

CONFIG_FILE = Path(__file__).parent / ".env"
COOKIE_FILE = Path(__file__).parent / "cookies.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MEDIA_DIR = Path("media")
BASE_URL = "https://www.vrt.be"


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def save_cookies(cookies: List, path: Path = COOKIE_FILE):
    """Save cookies to a JSON file."""
    with open(path, "w") as f:
        json.dump(cookies, f)


def load_cookies(path: Path = COOKIE_FILE) -> Optional[List]:
    """Load cookies from a JSON file if it exists."""
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return None


def detect_url_type(url: str) -> str:
    """Detect if URL is a single episode, season, or trailer.

    Returns: 'single', 'season', or 'trailer'
    """
    url = url.rstrip("/")

    if "/trailer/" in url:
        return "trailer"

    url_parts = url.split("/")

    last_part = url_parts[-1]
    second_last = url_parts[-2] if len(url_parts) >= 2 else ""

    if re.match(r"^[a-z]+-s\d+[a]\d+$", last_part):
        return "single"

    if last_part.isdigit():
        return "season"

    return "single"


def parse_episode_info(url: str) -> Dict:
    """Parse episode information from URL.

    Returns dict with keys: program, season, episode, type
    """
    url = url.rstrip("/")
    url_parts = url.split("/")

    result = {"program": "", "season": "", "episode": "", "type": "episode"}

    if "/trailer/" in url:
        result["type"] = "trailer"
        for part in reversed(url_parts):
            if part and "trailer" not in part and part != "a-z" and part != "vrtmax":
                result["program"] = part.replace("-trailer", "")
                break
        return result

    last_part = url_parts[-1]
    season_part = url_parts[-2] if len(url_parts) >= 2 else ""

    match = re.match(r"^([a-z-]+)-s(\d+)a(\d+)$", last_part)
    if match:
        result["program"] = match.group(1)
        result["season"] = match.group(2)
        result["episode"] = match.group(3)
    else:
        if last_part.isdigit():
            result["program"] = url_parts[-2] if len(url_parts) >= 2 else "video"
            result["season"] = last_part
        else:
            result["program"] = last_part

    return result


def generate_filename(info: Dict) -> str:
    """Generate filename from episode info.

    Format: {program}-s{season}a{episode}.mp4
    """
    program = info.get("program", "video")

    if info.get("type") == "trailer":
        return f"{program}-trailer.mp4"

    season = info.get("season", "")
    episode = info.get("episode", "")

    if season and episode:
        return f"{program}-s{season}a{episode}.mp4"

    return f"{program}.mp4"


def get_output_path(url: str, program_name: str = None) -> Path:
    """Get output path for download.

    Returns Path in media/{program}/ folder.
    """
    info = parse_episode_info(url)

    if program_name:
        program = program_name
    else:
        program = info.get("program", "video")

    program_dir = MEDIA_DIR / program.capitalize()
    program_dir.mkdir(parents=True, exist_ok=True)

    filename = generate_filename(info)

    return program_dir / filename


def filter_episodes_to_download(
    all_episodes: List[str], existing_files: List[str] = None, start_episode: int = None
) -> List[str]:
    """Filter episodes to download based on existing files and start episode.

    Args:
        all_episodes: List of episode filenames
        existing_files: List of already downloaded filenames
        start_episode: Episode number to start from

    Returns:
        List of episodes to download
    """
    existing = set(existing_files) if existing_files else set()

    episodes_to_download = []

    for episode in all_episodes:
        if episode in existing:
            continue

        if start_episode:
            match = re.search(r"a(\d+)\.mp4$", episode)
            if match:
                ep_num = int(match.group(1))
                if ep_num < start_episode:
                    continue

        episodes_to_download.append(episode)

    return episodes_to_download


BASE_URL = "https://www.vrt.be"


def discover_season_episodes(page) -> List[str]:
    """Discover all episode URLs from a season page.

    Args:
        page: Playwright page object on the season URL

    Returns:
        List of episode URLs
    """
    episode_urls = []

    links = page.query_selector_all("a")

    for link in links:
        href = link.get_attribute("href")
        if href and "/vrtmax/a-z/" in href:
            if re.search(r"[a-z]+-s\d+a\d+", href):
                if href.startswith("/"):
                    href = BASE_URL + href
                if href not in episode_urls:
                    episode_urls.append(href)

    return sorted(episode_urls)


def get_existing_episodes(program_dir: Path) -> List[str]:
    """Get list of already downloaded episodes in a program directory.

    Args:
        program_dir: Path to the program directory

    Returns:
        List of existing episode filenames
    """
    if not program_dir.exists():
        return []

    return [f.name for f in program_dir.glob("*.mp4")]


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


async def download_season(
    season_url: str,
    username: str,
    password: str,
    start_episode: int = None,
    force: bool = False,
    headless: bool = True,
):
    """Download all episodes from a season"""

    url_type = detect_url_type(season_url)
    if url_type != "season":
        print(f"FOUT: URL is geen seizoens-URL: {season_url}", flush=True)
        return False

    info = parse_episode_info(season_url)
    program = info.get("program", "video").capitalize()
    season = info.get("season", "")

    print(f"Seizoen downloaden: {program} S{season}\n", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, user_agent=USER_AGENT
        )
        page = await context.new_page()

        await stealth_async(page)

        print("Stap 1: Inloggen...", flush=True)

        saved_cookies = load_cookies()
        if saved_cookies:
            print("  Opgeslagen cookies gevonden, proberen...", flush=True)
            try:
                await context.add_cookies(saved_cookies)
                await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
                random_delay(1, 2)
                if "login" not in page.url.lower():
                    print("  ✓ Ingelogd met opgeslagen cookies!\n", flush=True)
                else:
                    print("  Cookies verlopen, opnieuw inloggen...\n", flush=True)
                    saved_cookies = None
            except Exception:
                saved_cookies = None

        if not saved_cookies:
            redirect_uri = "https://www.vrt.be/vrtmax/sso/callback"
            login_url = (
                f"https://login.vrt.be/authorize?response_type=code"
                f"&client_id=vrtnu-site&redirect_uri={redirect_uri}"
                f"&scope=openid%20profile%20email%20video"
            )

            await page.goto(login_url, wait_until="networkidle")
            random_delay(1, 2)

            await page.fill('input[type="email"]', username)
            await page.click('button[type="submit"]')
            random_delay(1, 3)

            pw = await page.query_selector('input[type="password"]')
            if pw:
                await pw.fill(password)
                await page.click('button[type="submit"]')
                random_delay(5, 8)

            if "login" in page.url.lower():
                print("FOUT: Inloggen mislukt", flush=True)
                await browser.close()
                return False

            cookies = await context.cookies()
            save_cookies(cookies)
            print("  ✓ Ingelogd en cookies opgeslagen!\n", flush=True)

        print("Stap 2: Afleveringen ophalen...", flush=True)
        await page.goto("https://www.vrt.be/vrtmax/", wait_until="networkidle")
        random_delay(1, 2)

        await page.goto(season_url, wait_until="networkidle")
        random_delay(3, 5)

        episode_urls = await page.evaluate("""
            () => {
                const allLinks = document.querySelectorAll('a');
                const urls = [];
                const baseUrl = 'https://www.vrt.be';
                allLinks.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href && href.includes('/vrtmax/a-z/')) {
                        if (href.match(/[a-z]+-s\\d+a\\d+/)) {
                            if (href.startsWith('/')) {
                                urls.push(baseUrl + href);
                            } else {
                                urls.push(href);
                            }
                        }
                    }
                });
                return [...new Set(urls)].sort();
            }
        """)

        if not episode_urls:
            print("FOUT: Geen afleveringen gevonden", flush=True)
            return False

        print(f"  Gevonden: {len(episode_urls)} afleveringen\n", flush=True)

        program_dir = MEDIA_DIR / program
        program_dir.mkdir(parents=True, exist_ok=True)

        existing_files = [] if force else get_existing_episodes(program_dir)

        if existing_files:
            print(f"  Reeds gedownload: {len(existing_files)}\n", flush=True)

        all_episodes = []
        for url in episode_urls:
            info = parse_episode_info(url)
            filename = generate_filename(info)
            all_episodes.append(filename)

        episodes_to_download = filter_episodes_to_download(
            all_episodes,
            existing_files=existing_files if not force else None,
            start_episode=start_episode,
        )

        if not episodes_to_download:
            print("  Alle afleveringen zijn al gedownload!", flush=True)
            return True

        print(
            f"  Te downloaden: {len(episodes_to_download)} afleveringen\n", flush=True
        )

        cookies = await context.cookies()
        cookie_header = "; ".join(
            [f"{c.get('name', '')}={c.get('value', '')}" for c in cookies]
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": cookie_header,
            "Referer": "https://www.vrt.be/",
        }

        print(
            f"  Te downloaden: {len(episodes_to_download)} afleveringen\n", flush=True
        )

        success_count = 0
        failed_count = 0

        for i, filename in enumerate(episodes_to_download, 1):
            episode_url = None
            for url in episode_urls:
                if parse_episode_info(url).get("episode") in filename:
                    episode_url = url
                    break

            if not episode_url:
                continue

            episode_info = parse_episode_info(episode_url)
            print(f"[{i}/{len(episodes_to_download)}] {filename}...", flush=True)

            redirect_url = None

            page_episode = await context.new_page()
            await stealth_async(page_episode)

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

            page_episode.on("response", handle_response)

            await page_episode.goto(episode_url, wait_until="networkidle")
            random_delay(3, 6)

            if not redirect_url:
                print(f"    FOUT: Kon stream URL niet ophalen", flush=True)
                failed_count += 1
                await page_episode.close()
                continue

            resp = requests.get(redirect_url, headers=headers)

            if resp.status_code != 200:
                print(f"    FOUT: API gaf status {resp.status_code}", flush=True)
                failed_count += 1
                await page_episode.close()
                continue

            data = resp.json()
            title = data.get("title", filename)

            stream_url = None
            for tu in data.get("targetUrls", []):
                if tu.get("type") == "hls":
                    stream_url = tu.get("url")
                    break

            if not stream_url:
                print(f"    FOUT: Geen HLS stream gevonden", flush=True)
                failed_count += 1
                await page_episode.close()
                continue

            output_path = program_dir / filename

            success, result = download_with_ffmpeg(stream_url, output_path, title)

            if success:
                print(f"    ✓", flush=True)
                success_count += 1
            else:
                print(f"    ✗ FOUT", flush=True)
                failed_count += 1

            await page_episode.close()

            random_delay(1, 3)

        await browser.close()

        print(
            f"\n  Resultaat: {success_count} gelukt, {failed_count} gefaald", flush=True
        )
        return success_count > 0


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Thuis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
  python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/" --start 10
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
    parser.add_argument("-s", "--start", type=int, help="Start vanaf aflevering nummer")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Herdownload bestaande bestanden"
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

    url_type = detect_url_type(args.url)
    output_path = Path(args.output) if args.output else None

    if url_type == "season":
        success = asyncio.run(
            download_season(
                season_url=args.url,
                username=args.username,
                password=args.password,
                start_episode=args.start,
                force=args.force,
                headless=not args.no_headless,
            )
        )
    else:
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
