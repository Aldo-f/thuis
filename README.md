# Thuis

Download videos from VRT MAX with automatic authentication.

[Get Started](#installation) · [Usage](#usage) · [Web UI](#web-ui) · [Docs](https://aldo-f.github.io/thuis/) · [Nederlands](README.nl.md)

---

## Features

- **Automatic Login**: Authenticate via Playwright browser automation
- **HLS Stream Download**: Extract and download HLS streams with FFmpeg
- **DRM Detection**: Detects DRM-protected content
- **Simple CLI**: Easy-to-use command line interface
- **Web UI**: Browser-based interface for easy downloading

---

## Requirements

- Python 3.9+
- ffmpeg
- VRT MAX account

---

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

---

## Setup

```bash
python thuis.py --setup
```

This prompts for your VRT MAX email and password, stored in `.env`.

**Note:** Your password is stored unencrypted in `.env`!

---

## Usage

```bash
# Download a video
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"

# Download entire season
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/"

# Dry-run (show what would be downloaded)
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/" --dry-run

# Interactive mode (ask before downloading)
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/" --interactive

# With custom output name
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "thuis.mp4"

# Show browser window (for debugging)
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

Videos are automatically saved to the `media/` directory.

---

## Web UI

A browser-based interface is also available:

```bash
# Start the web server
python app.py
```

Then open http://localhost:5000 in your browser.

The Web UI allows you to:
- Enter a VRT MAX URL
- See what would be downloaded (season or single episode)
- Start downloads with one click
- Monitor download progress

---

## Testing

```bash
# Fast tests (default, DRM detection only)
pytest tests/ -v

# All tests including downloads (slow)
pytest tests/ -v -m ""
```

### Test URLs

| Type | Program | DRM |
|------|---------|-----|
| Short DRM-free | Flikken Maastricht trailer | No |
| Long DRM-free | Thuis episode | No |
| DRM protected | De camping S1 E1 | Yes |

---

## How It Works

1. **Login**: Automatic login to VRT MAX via Playwright
2. **Stream Extraction**: Fetches HLS stream URL via VRT API
3. **Download**: Uses FFmpeg to download the video

---

## Troubleshooting

### Login fails
- Check credentials in `.env`
- Try with `--no-headless` to see what's happening

### Download fails
- Check if FFmpeg is installed: `ffmpeg -version`

---

## Links

- [Documentation](https://aldo-f.github.io/thuis/)
- [GitHub](https://github.com/Aldo-f/thuis)
- [Report Issues](https://github.com/Aldo-f/thuis/issues)
