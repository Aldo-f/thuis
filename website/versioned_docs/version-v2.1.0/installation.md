---
sidebar_position: 2
---

# Installation (v2.1.0)

## Overview

Version 2.1.0 of thuis is an incremental update to v2.0.0, focusing on stability improvements and compatibility updates for the VRT MAX platform. The installation process remains largely unchanged from v2.0.0.

## System Requirements

- **Python**: 3.8 or newer
- **Git**: For cloning the repository (optional)
- **Internet connection**: Required for downloading dependencies and accessing VRT MAX

## Installation Steps

1. **Download the release** - Get the v2.1.0 source code from the [releases page](https://github.com/Aldo-f/thuis/releases/tag/v2.1.0)
2. **Extract the files** - Unzip the downloaded archive to your desired location
3. **Set up a virtual environment** (strongly recommended):
   ```bash
   python3 -m venv .venv
   ```
4. **Activate the virtual environment**:
   - Linux/macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Verification

To confirm your installation is working correctly:
```bash
python -m thuis.main --help
```

You should see the help output showing all available options for v2.1.0.

## Dependencies

The `requirements.txt` file for v2.1.0 includes:

- `yt-dlp` (patched version with VRT MAX support) - Updated for v2.1 API compatibility
- `python-dotenv` - For loading environment variables from .env file
- `requests` - For HTTP communication with VRT MAX API
- `urllib3` - HTTP library with connection pooling
- `certifi` - For SSL certificate validation
- `isodate` - For parsing ISO 8601 date/time formats

## Important Notes

- A valid VRT MAX subscription is required to access most content
- The program will prompt for credentials if not found in environment variables or .env file
- This version includes specific updates to maintain compatibility with VRT API v2.1
- If you encounter authentication issues, ensure your credentials are correct and your account is active
- This release focuses on stability and compatibility rather than major new features
