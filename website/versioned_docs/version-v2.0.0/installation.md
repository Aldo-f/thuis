---
sidebar_position: 2
---

# Installation (v2.0.0)

## Getting Started

Version 2.0.0 of thuis represented a major architectural shift from the original PowerShell-based implementation to a Python application with proper dependency management.

## System Requirements

- **Python**: 3.8 or newer
- **Git**: For cloning the repository (optional if downloading ZIP)
- **Internet connection**: To download dependencies from PyPI

## Installation Steps

1. **Download the release** - Get the v2.0.0 source code from the [releases page](https://github.com/Aldo-f/thuis/releases/tag/v2.0.0)
2. **Extract the files** - Unzip the downloaded archive to your desired location
3. **Create a virtual environment** (recommended):
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

To verify your installation works, run:
```bash
python -m thuis.main --help
```

You should see the help output for the thuis command-line interface.

## What's in requirements.txt

The `requirements.txt` file in v2.0.0 included:
- `yt-dlp` (patched version for VMR MAX support)
- `python-dotenv` (for environment variable management)
- `pytest` (for testing)
- Other dependencies needed for the core functionality

## Important Notes

- This version requires a VRT MAX account to access content
- You'll need to set up your credentials via environment variables or a .env file
- The patched yt-dlp version included provides VRT MAX authentication support
