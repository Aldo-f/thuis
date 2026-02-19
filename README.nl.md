# Thuis - VRT MAX Downloader

Download video's van VRT MAX met automatische authenticatie.

[Beginnen](#installatie) · [Gebruik](#gebruik) · [Documentatie](https://aldo-f.github.io/thuis/nl/) · [English](README.md)

---

## Kenmerken

- **Automatische Login**: Authenticatie via Playwright browser automation
- **HLS Stream Download**: HLS streams ophalen en downloaden met FFmpeg
- **DRM Detectie**: Herkent DRM-beschermde content
- **Eenvoudige CLI**: Makkelijk te gebruiken command line interface

---

## Vereisten

- Python 3.9+
- ffmpeg
- VRT MAX account

---

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

---

## Setup

```bash
python thuis.py --setup
```

Dit vraagt om je VRT MAX email en wachtwoord, opgeslagen in `.env`.

**Let op:** Je wachtwoord wordt ongecodeerd opgeslagen in `.env`!

---

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

---

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

---

## Hoe het werkt

1. **Login**: Automatisch inloggen op VRT MAX via Playwright
2. **Stream extractie**: Haalt HLS stream URL op via VRT API
3. **Download**: Gebruikt FFmpeg om de video te downloaden

---

## Probleemoplossing

### Login werkt niet
- Controleer credentials in `.env`
- Probeer met `--no-headless` om te zien wat er gebeurt

### Download faalt
- Controleer of FFmpeg geïnstalleerd is: `ffmpeg -version`

---

## Links

- [Documentatie](https://aldo-f.github.io/thuis/nl/)
- [GitHub](https://github.com/Aldo-f/thuis)
- [Issues melden](https://github.com/Aldo-f/thuis/issues)
