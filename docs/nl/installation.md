# Installatie

## Vereisten

Installeer de benodigde systeem dependencies:

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
# Clone de repository
git clone https://github.com/Aldo-f/thuis.git
cd thuis

# Maak virtual environment
python3 -m venv venv

# Activeer virtual environment
source venv/bin/activate  # Linux/Mac
# of: .\venv\Scripts\activate  # Windows

# Installeer dependencies
pip install -r requirements.txt

# Installeer Playwright browsers
playwright install chromium

# Configureer credentials
python thuis.py --setup
```

## Verifieer Installatie

```bash
# Check ffmpeg
ffmpeg -version

# Check Python
python --version

# Run help
python thuis.py --help
```
