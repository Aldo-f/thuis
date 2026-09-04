---
slug: drm-mp4decrypt-cdm-guide
status: approved
intent: clear
review_required: false
approach: Add mp4decrypt (Bento4) installation, comprehensive DRM-decoding requirements docs, and create a helper script for CDM extraction guidance from Android devices
---

# Plan: DRM Decoding Requirements Docs + CDM Extraction Helper

## Objective
Make the thuis tool's DRM decoding requirements fully documented and discoverable: every binary/engine needed for decryption, how to install it per-OS, how to obtain the Widevine CDM (.wvd) to actually unlock DRM content, plus a helper script that guides .wvd extraction from a rooted Android device. This unblocks real end-to-end decryption once the user installs the pieces (currently `get_available_decryption_engine()` fails: no mp4decrypt/shaka/ffmpeg installed, and `~/.thuis/cdm/` empty because all `CDM_SOURCES` URLs are 404).

## Context / Why
- `drm_decrypt.py:40-48` — `DECRYPTION_ENGINES = ["MP4DECRYPT","SHAKA_PACKAGER","FFMPEG"]`, `REQUIRED_BINARIES` maps to `mp4decrypt`, `shaka-packager`, `ffmpeg`. `get_available_decryption_engine()` (97-123) raises `DecryptionEngineError` listing all 3 with an install hint.
- `cdm.py:24-30` — `CDM_SOURCES` all return 404; auto-fetch fails → no CDM → decryption blocked. `.env.example:16-18` has `WVD_CDM_PATH` commented but zero guidance on where a .wvd comes from.
- README already has a DRM section (README.md:360-388) but lists engines without install instructions.
- `requirements.txt:1-4` — python deps only; no system-binary install hints.
- User wants **comprehensive docs covering ALL requirements for DRM decoding** (not just mp4decrypt), plus a CDM extraction guidance helper script.

## Deliverables
| id | File | Change |
|----|------|--------|
| C1 | `docs/REQUIREMENTS.md` **(new, authoritative)** | Full DRM-decoding requirements: engines + per-OS install, pywidevine L3 CDM, .wvd acquisition paths, validation checklist, legal disclaimer |
| C2 | `README.md` | Trim DRM section → concise quick-start + link to `docs/REQUIREMENTS.md` |
| C3 | `scripts/extract_cdm.py` **(new)** | Prints wvdumper/Frida step-by-step .wvd extraction guide + validates existing .wvd in cache path; never auto-runs adb/frida |
| C4 | `requirements.txt` | Add commented install hints for system binaries (bento4/mp4decrypt, shaka-packager, ffmpeg) |
| C5 | `.env.example` | Comment referencing `docs/REQUIREMENTS.md` + `scripts/extract_cdm.py` |
| C6 | `src/thuis/cdm.py` | Auto-fetch failure warning references `scripts/extract_cdm.py` |
| C7 | `tests/test_extract_cdm.py` **(new)** | Assert helper prints key steps + validates .wvd |

## Steps

### 1. Create `docs/REQUIREMENTS.md` (authoritative DRM-decoding doc)
Sections:
- **Overview** — what is needed end-to-end to decrypt VRT MAX DRM (s16a2/Widevine L3): decryption engine + Widevine L3 CDM (.wvd) + pywidevine.
- **Decryption Engine (required — one of)**, mirroring `DECRYPTION_ENGINES` order with mp4decrypt primary:
  - **mp4decrypt (Bento4)** — *recommended* (primary in engine chain)
    - Linux: `sudo apt install bento4-utils` (Debian/Ubuntu) or download from bento4.com → put `mp4decrypt` on PATH
    - macOS: `brew install bento4`
    - Windows: download zip from bento4.com → add `bin/` to PATH
  - **shaka-packager** (alt)
    - Linux/macOS: from Google shaka-packager releases, `chmod +x`, on PATH
    - Windows: release zip
  - **ffmpeg** (alt, last resort)
    - Linux: `sudo apt install ffmpeg`; macOS: `brew install ffmpeg`; Windows: from ffmpeg.org or `winget install ffmpeg`
- **Verify** — `mp4decrypt --help` / `shaka-packager --version` / `ffmpeg -version` produce output; thuis auto-detects via `find_binary()` (drm_decrypt.py:76-94).
- **Widevine L3 CDM (.wvd) — required for content that uses Widevine**
  - What a `.wvd` is (Widevine device file with client ID + private key).
  - **Recommended path: extract your own L3 CDM from a rooted Android device** using `wvdumper/dumper` (Frida script).
    - Prereqs: rooted/bootloader-unlocked Android device, ADB, `frida-server` matching device, Frida tools (`pip install frida-tools`).
    - Steps: enable USB debugging → push `frida-server` → `adb forward` → run `frida` hooking `libwvhidl`/omx IL Widevine → wvdumper extracts L3 CDM → produces `.wvd`.
    - Note: on devices retaining L1 (e.g. Xiaomi), a liboemcrypto-disabler module is needed to drop to L3.
  - **Alternative (riskier, links rot)**: community-published L3 CDMs (cdm-project.com, highbitrate/Widevine_L3_CDMs, noballsben/Widevine_L3_CDMs). Use at your own risk.
  - **Place the .wvd** in `~/.thuis/cdm/` (default) or set `WVD_CDM_PATH` in `.env`.
- **pywidevine** (already in requirements.txt) — used for license acquisition; no action needed.
- **Environment variables** — `DECRYPT_DRM=yes`, `WVD_CDM_PATH` (optional override).
- **Validation checklist** — engine present + .wvd present + `DECRYPT_DRM=yes` → run `./thuis.sh <drm-url>` → expect decrypted mp4.
- **Legal disclaimer** — DRM circumvention may violate DMCA §1201 / EU Directive 2001/29 Art.6 / Belgian Art.XI.330-331; extract/use only for content you have rights to. Distribution of CDMs is illegal; keep yours private.

### 2. Update `README.md` DRM section (C2)
- Replace the existing detailed DRM requirement listing (README.md:360-388) with a concise quick-start: engines needed, .wvd needed, "Full details: see `docs/REQUIREMENTS.md`" + "Extract your CDM: `python scripts/extract_cdm.py`".

### 3. Create `scripts/extract_cdm.py` (C3)
- `main()` prints step-by-step wvdumper/Frida .wvd extraction guide (same content as REQUIREMENTS.md CDM section, condensed).
- Validates existing .wvd: scans `~/.thuis/cdm/` (or `WVD_CDM_PATH`) for `*.wvd`; prints found file(s) + whether a valid WVD header exists; if none, prints extraction instructions.
- **Must NOT** execute adb/frida/wvdumper or download CDMs — guidance only (legal/consent).
- Add `-h/--help`, clear exit codes (0 ok, non-zero if no .wvd found).
- Make executable (`chmod +x scripts/extract_cdm.py`).

### 4. Update `requirements.txt` (C4)
- Add commented lines (not pip deps) hinting the system binaries:
  `# System deps (not pip): mp4decrypt (Bento4: apt install bento4-utils / brew install bento4), shaka-packager, ffmpeg — see docs/REQUIREMENTS.md`

### 5. Update `.env.example` (C5)
- Expand the `WVD_CDM_PATH` comment: point to `docs/REQUIREMENTS.md` and `scripts/extract_cdm.py` for obtaining a `.wvd`.

### 6. Update `src/thuis/cdm.py` (C6)
- When auto-fetch fails / no CDM available, interpolate the existing warning to include: `See docs/REQUIREMENTS.md and run python scripts/extract_cdm.py to extract a CDM from your Android device.`
- Keep existing behavior (still raises/returns gracefully → `drm` status).

### 7. Create `tests/test_extract_cdm.py` (C7)
- Unit tests (mock filesystem / `Path`):
  - `test_prints_extraction_steps` — run script (capsys), assert output contains key tokens (`wvdumper`, `frida`, `adb`, `libwidevine`, `.wvd`, legal notice).
  - `test_validates_existing_wvd` — monkeypatch a fake `~/.thuis/cdm/device.wvd`; assert script reports it and exits 0.
  - `test_no_wvd_reports_and_exits_nonzero` — empty cache; assert exits non-zero + shows guide.
- Run: `pytest tests/test_extract_cdm.py` → all pass.

## Test / Verify
- `pytest tests/test_extract_cdm.py` → pass.
- `pytest tests/test_drm*.py` → still 78 pass (no regressions in cdm.py/drm_decrypt.py).
- `python scripts/extract_cdm.py` → prints guide, validates cache.
- `./thuis.sh <drm-url>` → still fails on missing engine/CDM (expected), but warning now points to the docs/helper. Full decrypt remains blocked until user installs engine + provides .wvd (out of scope).

## Scope OUT (Must NOT Have)
- ❌ Bundle or download any .wvd / CDM files.
- ❌ Auto-execute Frida/adb/wvdumper commands.
- ❌ Add system binaries to pip `requirements.txt` (they are OS packages) — comments only.
- ❌ Change `drm_decrypt.py` engine logic / `DECRYPTION_ENGINES` ordering.
- ❌ Auto-fetch from community CDM repos.
- ❌ Implement actual decryption (that requires a real CDM, which is user-side).

## Explicit Constraints
- All should go automatically — no `input()`/prompts added anywhere.
- Planner (Prometheus) does not implement; worker executes this plan via `/start-work`.
- **Do NOT auto-proceed after verification — wait for user's explicit approval before marking complete.**

## Acceptance
- `docs/REQUIREMENTS.md` exists, covers all decoding requirements (engines per-OS, CDM/.wvd, pywidevine, env vars, validation, legal).
- `scripts/extract_cdm.py` exists (executable), prints guide + validates .wvd, never auto-runs device commands.
- README/.env.example/requirements.txt/cdm.py all reference the new doc+helper consistently.
- New tests pass; existing DRM tests still pass.
- Warning on failed DRM decrypt points user to the doc + helper.
