---
sidebar_position: 5
---

# Development

## Setup

Follow the [installation](./installation.md) steps to set up your environment. The same virtual environment is used for development.

## Running tests

```bash
.venv/bin/python -m pytest tests/ -v
```

Tests are located in the `tests/` directory at the project root.

## Pre-commit hook

The project uses a pre-commit hook that automatically runs the test suite before each commit. Ensure your virtual environment is set up correctly so the hook can find the Python interpreter and dependencies.

## Project structure

```
thuis/
├── src/thuis/main.py      Main entry point
├── thuis.sh               Linux wrapper script
├── thuis.bat              Windows wrapper script
├── requirements.txt       Python dependencies (patched yt-dlp)
├── tests/                 Test suite
├── media/                 Downloaded videos (gitignored)
└── website/               Docusaurus documentation site
```

## Patched yt-dlp

thuis requires a patched version of yt-dlp that supports VRT MAX authentication. The minimum required version is **2026.06.09**, available from the [Aldo-f/yt-dlp](https://github.com/Aldo-f/yt-dlp) fork (tag `v2026.06.09-patch1`). It is installed automatically via `requirements.txt`.
