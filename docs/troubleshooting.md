# Troubleshooting

## Login Issues

### Login fails

**Symptom:** Authentication fails or browser doesn't proceed past login page.

**Solutions:**

1. Check credentials in `.env`:
   ```bash
   cat .env
   ```

2. Run with debug mode to see what's happening:
   ```bash
   python thuis.py <url> --no-headless
   ```

3. Make sure your VRT MAX subscription is active.

---

## Download Issues

### Download fails

**Symptom:** Download starts but fails with an error.

**Solutions:**

1. Check if FFmpeg is installed:
   ```bash
   ffmpeg -version
   ```

2. Install FFmpeg if missing:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

3. Check available disk space.

---

## Module Errors

### Module not found

**Symptom:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Browser Issues

### Playwright fails to launch

**Solution:**
```bash
# Reinstall Playwright browsers
playwright install chromium
```

---

## Still Having Issues?

- [Open an issue](https://github.com/Aldo-f/thuis/issues)
- [Check existing issues](https://github.com/Aldo-f/thuis/issues)
