# Thuis - VRT MAX Downloader

Download video's van VRT MAX met automatische authenticatie.

## Vereisten

- Python 3.9+
- ffmpeg
- VRT MAX account

## Installatie

```bash
# Maak virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# of: .\venv\Scripts\activate  # Windows

# Installeer dependencies
pip install -r requirements.txt

# Installeer Playwright browsers
playwright install chromium
```

## Eerste keer setup

```bash
python thuis.py --setup
```

Dit vraagt om je VRT MAX email en wachtwoord, en slaat deze op in `.env`.

**Let op:** Je wachtwoord wordt ongecodeerd opgeslagen in `.env`!

## Gebruik

```bash
# Download een video
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"

# Met custom output naam
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "thuis.mp4"

# Toon browser venster (voor debugging)
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

Video's worden automatisch opgeslagen in de `media/` map.

## Tests

```bash
# Snelle tests (standaard, alleen DRM detectie)
pytest tests/ -v

# Alle tests inclusief downloads (langzaam)
pytest tests/ -v -m ""
```

### Test URLs

| Type | Programma | DRM |
|------|-----------|-----|
| Kort DRM-vrij | Flikken Maastricht trailer | Nee |
| Lang DRM-vrij | Thuis aflevering | Nee |
| DRM beschermd | De camping S1 E1 | Ja |

## Hoe het werkt

1. **Login**: Automatisch inloggen op VRT MAX via Playwright
2. **Stream extractie**: Haalt de HLS stream URL op via de VRT API
3. **Download**: Gebruikt ffmpeg om de video te downloaden

## Problemen?

### Login werkt niet
- Controleer credentials in `.env`
- Probeer met `--no-headless` om te zien wat er gebeurt

### Download faalt
- Controleer of ffmpeg geïnstalleerd is: `ffmpeg -version`
