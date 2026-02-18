# Thuis v3 - VRT MAX Downloader

Automated video downloader for VRT MAX with Widevine DRM support.

## Requirements

- Python 3.9+
- Playwright
- N_m3u8DL-RE
- FFmpeg

## Installation

```bash
# Clone and enter v3 directory
cd v3

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install N_m3u8DL-RE
# Download from: https://github.com/nilaoda/N_m3u8DL-RE/releases
# Place in PATH or in ./tools/ directory

# Install FFmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# Mac: brew install ffmpeg
# Windows: winget install ffmpeg
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
VRT_USERNAME=your_email@example.com
VRT_PASSWORD=your_password
OUTPUT_DIR=media
DEFAULT_RESOLUTION=1080
```

## Usage

```bash
# Basic usage
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"

# With manual DRM keys (if automatic extraction fails)
python thuis.py "https://www.vrt.be/vrtmax/..." --key abc123:def456

# Show browser (for debugging)
python thuis.py "https://www.vrt.be/vrtmax/..." --no-headless
```

## Getting DRM Keys

If the video is DRM protected, you need decryption keys.

### Method 1: AllHell3
1. Install AllHell3 extension in Chrome/Firefox
2. Open the video in browser
3. Copy the license request/response from DevTools
4. Use AllHell3 to get the keys

### Method 2: pywidevine
1. Install pywidevine
2. Dump your own Widevine CDM
3. Use it to decrypt license responses

### Method 3: Key Databases
- Search for existing keys on forums
- Use keydb services

## Architecture

```
v3/
├── thuis.py              # Main entry point
├── modules/
│   ├── __init__.py
│   ├── vrt_auth.py       # VRT MAX authentication
│   ├── stream_extractor.py  # MPD/key extraction
│   └── downloader.py     # N_m3u8DL-RE orchestration
├── .env                  # Credentials (gitignored)
├── .env.example          # Template
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Login fails
- Check credentials in `.env`
- Try with `--no-headless` to see what's happening
- VRT might have changed their login flow

### No MPD URL found
- The video might not have started playing
- Try with `--no-headless` to manually trigger playback

### Download fails
- Check if you have the correct DRM keys
- Verify N_m3u8DL-RE is installed and in PATH
- Check FFmpeg installation

## Legal Notice

This tool is for personal archival purposes only. Only download content you have legal access to. Respect VRT's terms of service.
