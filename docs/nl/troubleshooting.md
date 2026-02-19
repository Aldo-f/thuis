# Probleemoplossing

## Login Problemen

### Login mislukt

**Symptoom:** Authenticatie mislukt of browser gaat niet voorbij login pagina.

**Oplossingen:**

1. Check credentials in `.env`:
   ```bash
   cat .env
   ```

2. Draai met debug modus om te zien wat er gebeurt:
   ```bash
   python thuis.py <url> --no-headless
   ```

3. Zorg dat je VRT MAX abonnement actief is.

---

## Download Problemen

### Download mislukt

**Symptoom:** Download start maar faalt met een fout.

**Oplossingen:**

1. Check of FFmpeg geïnstalleerd is:
   ```bash
   ffmpeg -version
   ```

2. Installeer FFmpeg als het ontbreekt:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

3. Check beschikbare schijfruimte.

---

## Module Fouten

### Module niet gevonden

**Symptoom:** `ModuleNotFoundError: No module named 'xxx'`

**Oplossing:**
```bash
# Activeer virtual environment
source venv/bin/activate

# Herinstalleer dependencies
pip install -r requirements.txt
```

---

## Browser Problemen

### Playwright faalt te starten

**Oplossing:**
```bash
# Herinstalleer Playwright browsers
playwright install chromium
```

---

## Nog Steeds Problemen?

- [Open een issue](https://github.com/Aldo-f/thuis/issues)
- [Bestaande issues bekijken](https://github.com/Aldo-f/thuis/issues)
