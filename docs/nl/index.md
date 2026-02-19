# Thuis - VRT MAX Downloader

Download video's van VRT MAX met automatische authenticatie.

[Beginnen](#snel-starten) · [Gebruik](#gebruik) · [Tests](#tests) · [English](../)

---

## Kenmerken

- **Automatische Login**: Authenticatie via Playwright browser automation
- **HLS Stream Download**: HLS streams ophalen en downloaden met FFmpeg
- **DRM Detectie**: Herkent DRM-beschermde content
- **Eenvoudige CLI**: Makkelijk te gebruiken command line interface

---

## Snel Starten

```bash
# Setup (eerste keer)
python thuis.py --setup

# Download een video
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

---

## Vereisten

| Vereiste | Beschrijving |
|----------|--------------|
| Python 3.9+ | Nodig voor async/await ondersteuning |
| ffmpeg | Nodig voor video download |
| VRT MAX account | Nodig voor authenticatie |

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

## Gebruik

### Basis Download

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

### Custom Output

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "mijn_video.mp4"
```

### Debug Modus

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

### Commando's

| Commando | Beschrijving |
|----------|--------------|
| `python thuis.py --setup` | Credentials configureren |
| `python thuis.py <url>` | Video downloaden |
| `python thuis.py <url> -o <bestand>` | Download met custom naam |
| `python thuis.py <url> --no-headless` | Browser venster tonen |
| `python thuis.py --help` | Help tonen |

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

## Hoe Het Werkt

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  VRT MAX    │ ────── │  Playwright │ ────── │   Cookies   │
│  Login      │        │  Browser    │        │   + Token   │
└─────────────┘        └─────────────┘        └──────┬──────┘
                                                     │
                    ┌────────────────────────────────┘
                    ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  VRT API    │ ────── │  HLS Stream │ ────── │   FFmpeg    │
│  /videos/   │        │  URL        │        │   Download  │
└─────────────┘        └─────────────┘        └─────────────┘
```

1. **Login**: Automatisch inloggen op VRT MAX via Playwright
2. **Stream Extractie**: Haalt HLS stream URL op via VRT API
3. **Download**: Gebruikt FFmpeg om de video te downloaden

---

## DRM Bescherming

VRT MAX gebruikt DRM (Digital Rights Management) op sommige content. De tool herkent dit:

| Stream Type | URL Patroon | Downloadbaar |
|-------------|-------------|--------------|
| DRM-vrij | `..._nodrm_...` | Ja |
| DRM-beschermd | `..._drm_...` | Nee |

Bij een poging om DRM-beschermde content te downloaden, faalt de download met een foutmelding.

---

## Probleemoplossing

### Login werkt niet

| Oplossing | Commando |
|-----------|----------|
| Controleer credentials | `cat .env` |
| Debug modus | `python thuis.py <url> --no-headless` |

### Download faalt

| Oplossing | Commando |
|-----------|----------|
| Controleer FFmpeg | `ffmpeg -version` |
| Installeer FFmpeg | `sudo apt install ffmpeg` |

### Module niet gevonden

| Oplossing | Commando |
|-----------|----------|
| Activeer venv | `source venv/bin/activate` |
| Herinstalleer | `pip install -r requirements.txt` |

---

## Links

- [GitHub](https://github.com/Aldo-f/thuis)
- [Issues melden](https://github.com/Aldo-f/thuis/issues)
- [English Documentation](../)
