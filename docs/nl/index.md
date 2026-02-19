# Thuis - VRT MAX Downloader

Download video's van VRT MAX met automatische authenticatie.

![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Kenmerken

- **Automatische Login** - Authenticatie via Playwright browser automation
- **HLS Stream Download** - HLS streams ophalen en downloaden met FFmpeg
- **DRM Detectie** - Herkent DRM-beschermde content
- **Eenvoudige CLI** - Makkelijk te gebruiken command line interface

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

## Links

- [Installatie](installation.md)
- [Gebruik](usage.md)
- [Tests](testing.md)
- [DRM](drm.md)
- [Probleemoplossing](troubleshooting.md)
- [GitHub](https://github.com/Aldo-f/thuis)
