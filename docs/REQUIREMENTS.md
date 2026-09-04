# DRM Decoding Requirements

**Authoritative reference for Widevine L3 decryption of VRT MAX content.**

This document covers every requirement to decrypt DRM-protected streams: decryption engines, CDM provisioning, environment setup, validation, and legal boundaries. Read completely before enabling `DECRYPT_DRM=yes`.

---

## 1. Overview — End-to-End DRM Decryption Pipeline

VRT MAX uses Widevine DRM (s17a2 license scheme) delivered over DASH. The tool automates the full pipeline:

```
MPD manifest + init segment
         │
         ▼
   PSSH Extraction (Widevine system ID: edef8ba9-79d6-4ace-a3c8-27dcd51d21ed)
         │
         ▼
   License Acquisition via pywidevine + VUDRM proxy
   (requires valid L3 ANDROID CDM .wvd + VUDRM token from yt-dlp)
         │
         ▼
   Content Keys (KID:KEY pairs)
         │
         ▼
   N_m3u8DL-RE download + decrypt + mux → playable MP4
   (uses MP4DECRYPT / SHAKA_PACKAGER / FFMPEG as decryption engine)
```

**Graceful degradation:** If any step fails (missing engine, revoked CDM, network error, bad PSSH), the URL is marked `drm` in `state.db` and skipped. No crash. No prompts.

---

## 2. Decryption Engines — Primary to Fallback Order

The code tries engines in this exact order (see `src/thuis/drm_decrypt.py:41`):

| Priority | Engine | Binary | Source | Notes |
|----------|--------|--------|--------|-------|
| 1 | **MP4DECRYPT** | `mp4decrypt` | Bento4 | **Primary recommended** — purpose-built for CENC decryption, most reliable |
| 2 | **SHAKA_PACKAGER** | `shaka-packager` | Shaka Packager | Good alternative, Google-maintained |
| 3 | **FFMPEG** | `ffmpeg` | FFmpeg | Last resort — general-purpose, may need specific compile flags |

All three are invoked **through N_m3u8DL-RE** via `--decryption-engine` flag. N_m3u8DL-RE must be installed and in PATH (see Section 4).

### 2.1 Per-OS Install Instructions

#### Linux (Debian/Ubuntu/Mint)

```bash
# mp4decrypt (Bento4) — PRIMARY
sudo apt update && sudo apt install -y bento4

# shaka-packager — ALTERNATIVE
# No native .deb; use pre-built binary from GitHub Releases
wget https://github.com/shaka-project/shaka-packager/releases/download/v3.0.0/packager-linux-x64 -O /usr/local/bin/shaka-packager
chmod +x /usr/local/bin/shaka-packager

# ffmpeg — LAST RESORT
sudo apt install -y ffmpeg

# N_m3u8DL-RE (required for all engines)
# Download latest release from https://github.com/nilaoda/N_m3u8DL-RE/releases
wget https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_linux_x64 -O /usr/local/bin/N_m3u8DL-RE
chmod +x /usr/local/bin/N_m3u8DL-RE
```

#### macOS (Homebrew)

```bash
# mp4decrypt (Bento4) — PRIMARY
brew install bento4

# shaka-packager — ALTERNATIVE
brew install shaka-packager

# ffmpeg — LAST RESORT
brew install ffmpeg

# N_m3u8DL-RE (required for all engines)
brew install nilaoda/tap/n_m3u8dl-re
# Or download from GitHub Releases:
# wget https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_macos_x64 -O /usr/local/bin/N_m3u8DL-RE
# chmod +x /usr/local/bin/N_m3u8DL-RE
```

#### Windows (PowerShell / Scoop / Chocolatey)

```powershell
# mp4decrypt (Bento4) — PRIMARY
# Option A: Scoop (recommended)
scoop install bento4

# Option B: Chocolatey
choco install bento4

# Option C: Manual — download Bento4 ZIP from https://github.com/axiomatic-systems/Bento4/releases
# Extract and add bin/ to PATH

# shaka-packager — ALTERNATIVE
# Manual: download from https://github.com/shaka-project/shaka-packager/releases
# Extract packager-win64.exe → rename to shaka-packager.exe, add to PATH

# ffmpeg — LAST RESORT
scoop install ffmpeg
# or: choco install ffmpeg

# N_m3u8DL-RE (required for all engines)
scoop install n_m3u8dl-re
# or: choco install n_m3u8dl-re
# or: download N_m3u8DL-RE_win64.exe from GitHub Releases, add to PATH
```

### 2.2 Verify Installation

Run each to confirm they are in PATH and functional:

```bash
# Primary engine
mp4decrypt --help
# Expected: usage output showing CENC decryption options

# Alternative engine
shaka-packager --help
# or (Windows): shaka-packager.exe --help

# Last resort
ffmpeg -version

# N_m3u8DL-RE (REQUIRED — orchestrates the decryption)
N_m3u8DL-RE --help
# Expected: shows --decryption-engine option with MP4DECRYPT, SHAKA_PACKAGER, FFMPEG
```

**Troubleshooting:** If `mp4decrypt` not found but Bento4 installed, check `/usr/local/bin` or `/opt/homebrew/bin` is in PATH. On Windows, restart shell after PATH changes.

---

## 3. Widevine L3 CDM (.wvd) — What, Why, How

### 3.1 What Is a CDM?

A **Content Decryption Module (CDM)** is the cryptographic component that Widevine uses to derive content keys from license responses. The `.wvd` file is a portable serialization of a Widevine device containing:

- **Private key** — device-specific RSA/ECC key for license challenge signing
- **Client ID** — unique device identifier
- **Device metadata** — type (ANDROID), security level (L3 = 3), system ID

The tool **only supports L3 ANDROID CDMs** (software-based, security level 3). L1 hardware-backed CDMs cannot be extracted and are not supported.

### 3.2 Automatic Provisioning (Default Behavior)

The tool auto-fetches a valid L3 ANDROID CDM on first DRM decryption attempt:

1. Checks `~/.thuis/cdm/widevine_l3_android.wvd` (or `WVD_CDM_PATH`)
2. Validates with `pywidevine.device.Device.load()` — must be ANDROID type, security_level=3
3. If missing/invalid, downloads from known sources (see `src/thuis/cdm.py:24-30`)
4. Caches validated CDM for reuse

**No manual action required** if auto-fetch works. The CDM sources are community-hosted pre-built `.wvd` files or key material zips.

### 3.3 Manual CDM Extraction (Rooted Android / Advanced)

For users who want to extract their own CDM from a rooted Android device (more durable, device-specific):

#### Prerequisites

- Rooted Android device (Magisk/KernelSU)
- ADB access (`adb shell` as root)
- Frida server running on device (`frida-server` matching architecture)
- Python 3.8+ with `frida-tools`, `pywidevine`

#### Extraction via wvdumper (Recommended)

```bash
# On host machine
pip install frida-tools

# On device (via ADB)
# 1. Push frida-server matching device arch (arm64/arm/x86)
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# 2. Run wvdumper (Python script using Frida)
# See: https://github.com/keyset/wvdumper
git clone https://github.com/keyset/wvdumper
cd wvdumper
pip install -r requirements.txt

# 3. Dump CDM from Widevine process
# Target process: com.google.android.gms (or com.widevine for older)
python wvdumper.py -p com.google.android.gms -o my_cdm.wvd

# 4. Pull to host
adb pull /data/local/tmp/my_cdm.wvd ~/.thuis/cdm/widevine_l3_android.wvd
```

#### Extraction via Frida Script (Alternative)

```bash
# Direct Frida injection to hook CdmFactory
frida -U -f com.google.android.gms -l extract_cdm.js --no-pause
# Where extract_cdm.js hooks CdmFactory.create() and dumps device blob
```

#### Xiaomi L1 Note

Some Xiaomi devices ship with **L1 CDMs that can be extracted via software** (unlike most L1 which require hardware TEE). If you have a Xiaomi device with extractable L1:
- The resulting `.wvd` will have `security_level=1`
- **pywidevine will reject it** (tool validates `security_level == 3`)
- To use L1, you would need to modify validation logic — not recommended for this tool

### 3.4 Community CDM Alternatives (Use at Own Risk)

Pre-built `.wvd` files circulate in various repositories:

| Source | URL | Risk |
|--------|-----|------|
| nicko170/video-devices | `github.com/nicko170/video-devices` | **Current default** — auto-fetched by tool |
| keyset/wvdumper dumps | Various gists/Telegram | Unknown provenance, may be revoked |
| Private trackers/forums | N/A | Often stale, may contain malware |

**Warnings:**
- Community CDMs are **shared across users** — higher revocation risk
- No guarantee of longevity; Widevine revokes device certificates periodically
- **Never commit `.wvd` files to any repository** (gitignored by default)
- Consider extracting your own (Section 3.3) for production use

### 3.5 CDM Placement & Environment Variable

| Method | Path / Variable |
|--------|-----------------|
| **Default cache** | `~/.thuis/cdm/widevine_l3_android.wvd` |
| **Custom location** | Set `WVD_CDM_PATH=/custom/path/to/cdm` in `.env` or shell |

The tool searches: `$WVD_CDM_PATH/widevine_l3_android.wvd` → `~/.thuis/cdm/widevine_l3_android.wvd`

---

## 4. Required External Tools Summary

| Tool | Purpose | Install Priority |
|------|---------|------------------|
| **N_m3u8DL-RE** | HLS/DASH downloader + decryption orchestrator | **REQUIRED** (all DRM flows) |
| **mp4decrypt** (Bento4) | Primary CENC decryption engine | **HIGH** (first in fallback chain) |
| **shaka-packager** | Alternative decryption engine | **MEDIUM** (fallback #2) |
| **ffmpeg** | Last-resort decryption engine | **LOW** (fallback #3) |
| **pywidevine** | License acquisition + CDM handling | Python package (in `requirements.txt`) |

**All system packages (N_m3u8DL-RE, mp4decrypt, shaka-packager, ffmpeg) must be installed manually per OS.** Only `pywidevine` is a Python dependency.

---

## 5. Python Dependencies (Already in requirements.txt)

```text
pywidevine>=1.0.0   # Widevine CDM + license client
pymp4>=0.2.0        # MP4 box parsing for PSSH extraction
```

Install via:
```bash
uv pip install -r requirements.txt --python .venv/bin/python
# or
pip install -r requirements.txt
```

---

## 6. Environment Variables

Add to `.env` file in project root (or export in shell):

```bash
# Enable automatic DRM decryption (default: yes)
DECRYPT_DRM=yes

# Optional: Custom CDM cache directory
# WVD_CDM_PATH=/mnt/secure/cdm

# VRT credentials (optional; built-in defaults work)
VRT_EMAIL=your-email@example.com
VRT_PASSWORD=your-password
```

**Behavior:**
- `DECRYPT_DRM=yes` (default): Auto-decrypt DRM content when detected
- `DECRYPT_DRM=no`: Skip DRM URLs entirely (mark `drm` in state.db)
- `WVD_CDM_PATH`: Overrides default `~/.thuis/cdm/` cache location

---

## 7. Validation Checklist

Run through this checklist after setup to confirm DRM decryption works:

### 7.1 Prerequisites
- [ ] Python 3.8+ with virtual environment active
- [ ] `requirements.txt` installed (`pywidevine`, `pymp4`)
- [ ] `.env` has `DECRYPT_DRM=yes`
- [ ] VRT credentials configured (env or `.env`)

### 7.2 System Binaries
- [ ] `N_m3u8DL-RE --help` → shows usage, `--decryption-engine` option present
- [ ] `mp4decrypt --help` → shows CENC options (PRIMARY engine)
- [ ] `shaka-packager --help` → shows usage (fallback #2)
- [ ] `ffmpeg -version` → shows version (fallback #3)

### 7.3 CDM Provisioning
- [ ] Run `python -m thuis.cdm` → prints `CDM ready: /path/to/widevine_l3_android.wvd`
- [ ] Verify CDM validates: `python -c "from pywidevine.device import Device; d=Device.load('~/.thuis/cdm/widevine_l3_android.wvd'); print(d.type, d.security_level)"` → `ANDROID 3`

### 7.4 End-to-End Test
- [ ] Run a known DRM URL with `--dry-run` first:
  ```bash
  ./thuis.sh --dry-run "https://www.vrt.be/vrtmax/a/show/drm-protected-content/"
  ```
- [ ] Check logs: `tail -f logs/$(date +%F).log` — should show:
  - `Using decryption engine: MP4DECRYPT (/usr/bin/mp4decrypt)`
  - `Extracted Widevine PSSH (xxx bytes)`
  - `Acquired N content key(s)`
  - `N_m3u8DL-RE produced: /path/to/output.mp4`
- [ ] Verify output file plays: `ffprobe output.mp4` shows video+audio streams

### 7.5 Failure Modes to Recognize
| Log Message | Cause | Fix |
|-------------|-------|-----|
| `No decryption engine found` | None of mp4decrypt/shaka-packager/ffmpeg in PATH | Install per Section 2.1 |
| `CDM validation failed` | `.wvd` corrupt, wrong type, or revoked | Delete `~/.thuis/cdm/` and re-run; or extract fresh CDM |
| `License request failed: HTTP 403` | VUDRM token expired or CDM revoked | Re-run (new token from yt-dlp); if persistent, extract new CDM |
| `No CONTENT keys returned` | License response empty or CDM mismatch | Verify CDM is ANDROID L3; try different CDM source |
| `N_m3u8DL-RE exited with code X` | Decryption engine error | Try next engine in chain (auto); check engine version compatibility |

---

## 8. Legal Disclaimer ⚠️

### 8.1 Anti-Circumvention Laws Apply

**This tool implements DRM decryption for interoperability purposes. You are responsible for complying with all applicable laws in your jurisdiction.**

| Jurisdiction | Statute | Key Provision |
|--------------|---------|---------------|
| **United States** | DMCA §1201 (17 U.S.C. §1201) | Prohibits circumventing "technological measures that effectively control access" to copyrighted works. Limited exceptions for interoperability, security research, and libraries/archives. |
| **European Union** | InfoSoc Directive 2001/29/EC Art. 6 + DSM Directive (EU) 2019/790 | Prohibits circumvention of effective technological measures. Art. 6(4) requires member states to ensure beneficiaries of exceptions (e.g., private copy, quotation) can actually benefit — but does not create a general right to circumvent. |
| **Belgium** | Wet van 30 juni 1994 / Loi du 30 juin 1994 (Auteurswet / Droit d'auteur) Art. XI.330–331 | Implements InfoSoc Art. 6. Circumvention prohibited; limited exceptions for interoperability (Art. XI.331 §2) and private copy (Art. XI.188) but private copy exception **does not** authorize circumvention of effective DRM. |

### 8.2 What This Means for You

- **Personal use ≠ legal shield.** Format-shifting or private copying exceptions **do not** automatically permit DRM circumvention in the EU/BE or US.
- **Interoperability exception** (EU Art. 6(4), BE Art. XI.331 §2, US §1201(f)): May apply if decryption is strictly necessary for interoperability of an independently created program. This tool's purpose (downloading for personal archival) may or may not qualify — untested in courts.
- **No warranty.** This is a proof of concept. Use at your own legal risk.
- **VRT MAX Terms of Service** prohibit automated downloading and circumvention. Respect them.

### 8.3 Practical Guidance

1. **Only decrypt content you have lawful access to** (your own VRT MAX subscription).
2. **Do not distribute** decrypted files, CDM files (`.wvd`), or extracted keys.
3. **Do not use commercially.** This tool is for personal, non-commercial archival only.
4. **Check your local law.** This disclaimer is not legal advice. Consult an attorney if uncertain.

---

## 9. Quick Reference — Commands at a Glance

```bash
# 1. Install system deps (Linux example)
sudo apt install -y bento4 ffmpeg
wget -O /usr/local/bin/N_m3u8DL-RE https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_linux_x64
chmod +x /usr/local/bin/N_m3u8DL-RE

# 2. Install Python deps
uv pip install -r requirements.txt --python .venv/bin/python

# 3. Enable DRM
echo "DECRYPT_DRM=yes" >> .env

# 4. Validate CDM auto-fetch
python -m thuis.cdm

# 5. Test DRM download (dry run)
./thuis.sh --dry-run "https://www.vrt.be/vrtmax/a/show/..."

# 6. Actual download
./thuis.sh "https://www.vrt.be/vrtmax/a/show/..."
```

---

## 10. Files Referenced

| File | Purpose |
|------|---------|
| `src/thuis/drm_decrypt.py` | Core decryption pipeline (PSSH → license → N_m3u8DL-RE) |
| `src/thuis/cdm.py` | CDM auto-fetch, validation, caching (`ensure_cdm()`) |
| `src/thuis/main.py` | CLI entry; wires DRM path via `DECRYPT_DRM` env |
| `requirements.txt` | Python deps (`pywidevine`, `pymp4`) |
| `.env` | Runtime config (`DECRYPT_DRM`, `WVD_CDM_PATH`, credentials) |

---

*Last updated: 2026-09-04 — Keep this document synchronized with code changes in `drm_decrypt.py` and `cdm.py`.*