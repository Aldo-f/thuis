#!/usr/bin/env python3
"""
Thuis v3 - VRT MAX Downloader

Downloads video content from VRT MAX with automatic authentication
and DRM key extraction.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

from modules import VRTAuthenticator, StreamExtractor, Downloader


async def download_video(
    video_url: str,
    username: str,
    password: str,
    output_dir: str,
    resolution: int,
    headless: bool = True,
    manual_keys: list = None,
):
    print("=" * 60)
    print("Thuis v3 - VRT MAX Downloader")
    print("=" * 60)

    downloader = Downloader(output_dir=output_dir, resolution=resolution)

    if not downloader.check_dependencies():
        print("\nError: Missing required dependencies.")
        print("Please install N_m3u8DL-RE and FFmpeg.")
        return False

    print(f"\n[1/4] Authenticating with VRT MAX...")
    auth = VRTAuthenticator(username, password, headless=headless)

    try:
        await auth.start_browser()

        if not await auth.login():
            print("Error: Failed to login to VRT MAX")
            return False

        print("[OK] Logged in successfully")

        print(f"\n[2/4] Navigating to video: {video_url}")
        if not await auth.navigate_to_video(video_url):
            print("Error: Failed to navigate to video")
            return False

        print("[OK] Video page loaded")

        print(f"\n[3/4] Extracting stream information...")
        page = auth.get_page()
        extractor = StreamExtractor(page)

        await extractor.inject_capture_scripts()

        await auth.navigate_to_video(video_url)

        stream_info = await extractor.extract_stream_info()

        if not stream_info:
            print("Error: Failed to extract stream information")
            return False

        print(f"[OK] Found MPD: {stream_info.mpd_url[:80]}...")
        if stream_info.pssh:
            print(f"[OK] PSSH: {stream_info.pssh[:50]}...")
        if stream_info.license_url:
            print(f"[OK] License URL: {stream_info.license_url}")

        print(f"\n[4/4] Starting download...")

        output_filename = downloader.generate_filename_from_url(video_url)

        keys_to_use = manual_keys
        if not keys_to_use and stream_info.keys:
            keys_to_use = stream_info.keys

        if stream_info.mpd_url:
            result = await downloader.download(
                mpd_url=stream_info.mpd_url,
                output_filename=output_filename,
                keys=keys_to_use,
                license_url=stream_info.license_url,
                license_headers=stream_info.license_headers,
            )

            if result.success:
                print(f"\n[SUCCESS] Downloaded: {result.output_file}")
                return True
            else:
                print(f"\n[ERROR] Download failed: {result.error}")

                if not keys_to_use:
                    print("\n" + "=" * 60)
                    print("DRM KEYS REQUIRED")
                    print("=" * 60)
                    print("This video is protected with Widevine DRM.")
                    print("You need to provide decryption keys.")
                    print("\nTo get keys:")
                    print("1. Use a tool like AllHell3 or pywidevine")
                    print("2. Or use a key database")
                    print("\nPSSH:", stream_info.pssh)
                    print("License URL:", stream_info.license_url)
                    print("\nThen run with: --key <kid>:<key>")
                    print("=" * 60)

                return False
        else:
            print("Error: No MPD URL found")
            return False

    finally:
        await auth.close_browser()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Download videos from VRT MAX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
  %(prog)s "https://www.vrt.be/vrtmax/..." --key abc123:def456
  %(prog)s "https://www.vrt.be/vrtmax/..." --no-headless
        """,
    )

    parser.add_argument("url", help="VRT MAX video URL")
    parser.add_argument(
        "--username",
        "-u",
        default=os.getenv("VRT_USERNAME"),
        help="VRT MAX username (or set VRT_USERNAME env)",
    )
    parser.add_argument(
        "--password",
        "-p",
        default=os.getenv("VRT_PASSWORD"),
        help="VRT MAX password (or set VRT_PASSWORD env)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=os.getenv("OUTPUT_DIR", "media"),
        help="Output directory",
    )
    parser.add_argument(
        "--resolution",
        "-r",
        type=int,
        default=int(os.getenv("DEFAULT_RESOLUTION", "1080")),
        help="Preferred resolution",
    )
    parser.add_argument(
        "--key",
        "-k",
        action="append",
        dest="keys",
        metavar="KID:KEY",
        help="DRM decryption key (can be specified multiple times)",
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Show browser window"
    )

    args = parser.parse_args()

    if not args.username or not args.password:
        print("Error: Username and password required.")
        print("Set VRT_USERNAME and VRT_PASSWORD in .env file")
        print("or use --username and --password arguments.")
        sys.exit(1)

    success = asyncio.run(
        download_video(
            video_url=args.url,
            username=args.username,
            password=args.password,
            output_dir=args.output,
            resolution=args.resolution,
            headless=not args.no_headless,
            manual_keys=args.keys,
        )
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
