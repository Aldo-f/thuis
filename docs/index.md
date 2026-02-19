# Thuis - VRT MAX Downloader

Download videos from VRT MAX with automatic authentication.

![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Automatic Login** - Authenticate via Playwright browser automation
- **HLS Stream Download** - Extract and download HLS streams with FFmpeg
- **DRM Detection** - Detects DRM-protected content
- **Simple CLI** - Easy-to-use command line interface

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

## Links

- [Installation](installation.md)
- [Usage](usage.md)
- [Testing](testing.md)
- [DRM Protection](drm.md)
- [Troubleshooting](troubleshooting.md)
- [GitHub](https://github.com/Aldo-f/thuis)
