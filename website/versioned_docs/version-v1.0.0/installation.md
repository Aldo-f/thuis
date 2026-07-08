---
sidebar_position: 2
---

# Installation

## Requirements

- Python 3.8 or newer
- git
- A VRT MAX account (free or paid)

## Steps

Open a terminal and run:

```bash
# Clone the repository
git clone https://github.com/Aldo-f/thuis.git
cd thuis

# Create a virtual environment (recommended)
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

This installs a [patched version of yt-dlp](https://github.com/Aldo-f/yt-dlp) (tag `v2026.06.09-patch1`) that can handle VRT MAX's login flow.

## Verify the installation

```bash
.venv/bin/yt-dlp --version
```

You should see:

```
2026.06.09
```
