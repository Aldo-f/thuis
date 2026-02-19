# Installation

## Prerequisites

Install the required system dependencies:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg python3-venv

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

## Setup

```bash
# Clone the repository
git clone https://github.com/Aldo-f/thuis.git
cd thuis

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure credentials
python thuis.py --setup
```

## Verify Installation

```bash
# Check ffmpeg
ffmpeg -version

# Check Python
python --version

# Run help
python thuis.py --help
```
