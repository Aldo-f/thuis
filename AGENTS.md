# AGENTS.md

This document provides guidelines for agentic coding agents working in the **thuis** repository.

## Project Overview

**thuis** is a Python command-line utility for downloading video content from VRT MAX. It uses Playwright for browser automation to handle authentication and extracts HLS stream URLs from the VRT API, then downloads videos using FFmpeg.

## Build/Lint/Test Commands

### Running the Script

```bash
# First time setup
python thuis.py --setup

# Download a video
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"

# With custom output
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "thuis.mp4"

# Debug mode (shows browser)
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

### Python Syntax Validation

```bash
# Check for syntax errors
python -m py_compile thuis.py

# Run type checking (if mypy is installed)
mypy thuis.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_thuis.py
```

### Linting

```bash
# Check code formatting
black --check thuis.py tests/

# Format code
black thuis.py tests/

# Check with flake8
flake8 thuis.py tests/
```

## Code Style Guidelines

### Naming Conventions

- **Functions**: Use snake_case
  - Good: `download_with_ffmpeg`, `check_ffmpeg`, `setup`
  - Avoid: `downloadWithFFmpeg`, `DownloadVideo`

- **Variables**: Use snake_case for local variables, descriptive names
  - Good: `stream_url`, `output_path`, `cookie_header`
  - Good: `CONFIG_FILE` for constants
  - Avoid: `x`, `temp`, `data1`

- **Parameters**: Use snake_case with type annotations
  ```python
  def download_video(
      video_url: str,
      username: str,
      password: str,
      output_path: Optional[Path] = None,
      headless: bool = True,
  ):
  ```

- **Constants**: Use UPPER_CASE at module level
  - `CONFIG_FILE`, `USER_AGENT`

### Formatting

- **Indentation**: Use 4 spaces (no tabs)
- **Line Length**: Keep lines under 100 characters where practical
- **Blank Lines**: Use single blank lines to separate logical sections and functions
- **Quotes**: Use double quotes for strings

### Imports

Organize imports in this order:
1. Standard library imports
2. Third-party imports
3. Local imports

Example:
```python
import asyncio
import argparse
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright
```

### Type Hints

Use type hints for function parameters and return values:
```python
def download_with_ffmpeg(stream_url: str, output_path: Path, title: str) -> Tuple[bool, Union[int, str]]:
```

### Error Handling

- Use `try/except` blocks for expected errors
- Use `sys.exit(1)` for error conditions with user-friendly messages
- Use `flush=True` on all print statements to ensure output appears during async operations

```python
try:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    return result.returncode == 0
except FileNotFoundError:
    return False
```

### Logging/Output

- Always use `print()` with `flush=True` for output during async operations
- Use Dutch language for user-facing messages
- Keep error messages concise but informative

```python
print("FOUT: ffmpeg is niet geïnstalleerd", flush=True)
print("Stap 1: Inloggen...", flush=True)
```

### Function Documentation

Include docstrings for functions:
```python
def setup():
    """Interactieve configuratie voor eerste keer"""
    ...

async def download_video(
    video_url: str,
    username: str,
    password: str,
    output_path: Optional[Path] = None,
    headless: bool = True,
):
    """Download een VRT MAX video"""
    ...
```

### Async/Await

- Use `async def` for async functions
- Use `await` for async calls
- Run async code with `asyncio.run()` in main

```python
async def download_video(...):
    async with async_playwright() as p:
        browser = await p.chromium.launch(...)
        ...

success = asyncio.run(download_video(...))
```

## Project-Specific Notes

- Credentials are stored in `.env` file (unencrypted, gitignored)
- Default output directory is `media/` (gitignored)
- Uses Playwright with Chromium for browser automation
- Downloads via FFmpeg HLS streams
- All user-facing messages should be in Dutch
- Test with these URLs:
  - `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/`
  - `https://www.vrt.be/vrtmax/a-z/den-elfde-van-den-elfde/1/den-elfde-van-den-elfde-s1a1/`
