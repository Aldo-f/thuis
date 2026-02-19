# Thuis - VRT MAX Downloader

Download videos from VRT MAX with automatic authentication.

[Get Started](#quick-start) · [Usage](#usage) · [Testing](#testing) · [Nederlands](nl/)

---

## Features

- **Automatic Login**: Authenticate via Playwright browser automation
- **HLS Stream Download**: Extract and download HLS streams with FFmpeg
- **DRM Detection**: Detects DRM-protected content
- **Simple CLI**: Easy-to-use command line interface

---

## Quick Start

```bash
# Setup (first time)
python thuis.py --setup

# Download a video
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

---

## Requirements

| Requirement | Description |
|-------------|-------------|
| Python 3.9+ | Required for async/await support |
| ffmpeg | Required for video download |
| VRT MAX account | Required for authentication |

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

## Usage

### Basic Download

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

### Custom Output

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "my_video.mp4"
```

### Debug Mode

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

### Commands

| Command | Description |
|---------|-------------|
| `python thuis.py --setup` | Configure credentials |
| `python thuis.py <url>` | Download video |
| `python thuis.py <url> -o <file>` | Download with custom name |
| `python thuis.py <url> --no-headless` | Show browser window |
| `python thuis.py --help` | Show help |

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

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  VRT MAX    │ ────── │  Playwright │ ────── │   Cookies   │
│  Login      │        │  Browser    │        │   + Token   │
└─────────────┘        └─────────────┘        └──────┬──────┘
                                                     │
                    ┌────────────────────────────────┘
                    ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  VRT API    │ ────── │  HLS Stream │ ────── │   FFmpeg    │
│  /videos/   │        │  URL        │        │   Download  │
└─────────────┘        └─────────────┘        └─────────────┘
```

1. **Login**: Automatic login to VRT MAX via Playwright
2. **Stream Extraction**: Fetches HLS stream URL via VRT API
3. **Download**: Uses FFmpeg to download the video

---

## DRM Protection

VRT MAX uses DRM (Digital Rights Management) on some content. The tool detects this:

| Stream Type | URL Pattern | Downloadable |
|-------------|-------------|--------------|
| DRM-free | `..._nodrm_...` | Yes |
| DRM-protected | `..._drm_...` | No |

When attempting to download DRM-protected content, the download will fail with an error.

---

## Troubleshooting

### Login fails

| Solution | Command |
|----------|---------|
| Check credentials | `cat .env` |
| Debug mode | `python thuis.py <url> --no-headless` |

### Download fails

| Solution | Command |
|----------|---------|
| Check FFmpeg | `ffmpeg -version` |
| Install FFmpeg | `sudo apt install ffmpeg` |

### Module not found

| Solution | Command |
|----------|---------|
| Activate venv | `source venv/bin/activate` |
| Reinstall | `pip install -r requirements.txt` |

---

## Links

- [GitHub](https://github.com/Aldo-f/thuis)
- [Report Issues](https://github.com/Aldo-f/thuis/issues)
- [Dutch Documentation](nl/)
