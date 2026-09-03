#!/usr/bin/env python3
"""
C3 probe helper — drives the pinned yt-dlp fork's VRT extractor internals
to perform the real login flow and dump the authenticated aggregator JSON.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Ensure project root and src/thuis are on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src', 'thuis'))

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present
except Exception:
    pass  # dotenv optional

# Import yt-dlp and the VRT extractor
import yt_dlp
from yt_dlp.extractor.vrt import VrtNUIE, VRTBaseIE


def get_credentials():
    """Get VRT credentials from environment, falling back to defaults."""
    email = os.getenv("VRT_EMAIL", "kuxelu@ipdeer.com")
    password = os.getenv("VRT_PASSWORD", "Els123456")
    return email, password


def dump_aggregator_json(url: str, output_path: str | None = None) -> dict:
    """
    Drive the VRT extractor's login flow and fetch the authenticated
    aggregator JSON for the given VRT MAX episode URL.
    
    Returns the raw streaming_info dict from the media aggregator.
    """
    email, password = get_credentials()
    
    # Create a YoutubeDL instance with quiet logging
    ydl = yt_dlp.YoutubeDL({
        'quiet': True,
        'skip_download': True,
    })
    
    # Instantiate the VRT MAX extractor (VrtNUIE)
    ie = VrtNUIE()
    ie.set_downloader(ydl)
    
    # Set credentials for login
    ie._downloader.params['username'] = email
    ie._downloader.params['password'] = password
    
    # Perform login flow to get tokens
    access_token, video_token = ie._fetch_tokens()
    
    if not access_token or not video_token:
        # Try explicit login if tokens not available
        try:
            ie._perform_login(email, password)
            access_token, video_token = ie._fetch_tokens()
        except Exception as e:
            raise RuntimeError(f"Login failed: {e}")
    
    if not access_token or not video_token:
        raise RuntimeError("Failed to obtain authentication tokens")
    
    # Extract video_id (streamId) from the episode page via GraphQL
    from urllib.parse import urlparse
    
    display_id = ie._match_id(url)
    page_id = urlparse(url).path
    
    # Fetch episode metadata via GraphQL to get the streamId
    metadata = ie._download_json(
        f'https://www.vrt.be/vrtnu-api/graphql{"" if access_token else "/public"}/v1',
        display_id, 'Downloading asset JSON', 'Unable to download asset JSON',
        data=json.dumps({
            'operationName': 'EpisodePage',
            'query': VrtNUIE._VIDEO_PAGE_QUERY,
            'variables': {'pageId': page_id},
        }).encode(),
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'x-vrt-client-name': 'WEB',
            'x-vrt-client-version': '1.5.15',
            'x-vrt-zone': 'default',
        })
    
    if not metadata or not metadata.get('data') or not metadata['data'].get('page'):
        raise RuntimeError("Unable to download asset JSON: no page data")
    
    page = metadata['data']['page']
    video_id = page['player']['modes'][0]['streamId']
    
    # Call the media aggregator API (this is the key method from VRTBaseIE)
    streaming_info = ie._call_api(video_id, 'vrtnu-web@PROD', id_token=video_token)
    
    # Output the JSON
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(streaming_info, f, indent=2, ensure_ascii=False)
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        json.dump(streaming_info, sys.stdout, indent=2, ensure_ascii=False)
        print()
    
    return streaming_info


def main():
    parser = argparse.ArgumentParser(
        description="Probe VRT MAX episode and dump authenticated aggregator JSON"
    )
    parser.add_argument("url", help="VRT MAX episode URL")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        dump_aggregator_json(args.url, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()