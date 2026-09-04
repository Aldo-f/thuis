---
slug: drm-mp4decrypt-cdm-guide
status: approved
intent: clear
review_required: false
pending-action: none — plan written to .omo/plans/drm-mp4decrypt-cdm-guide.md
approach: Add mp4decrypt (Bento4) installation, comprehensive DRM-decoding requirements docs, and create a helper script for CDM extraction guidance from Android devices
---

# Draft: drm-mp4decrypt-cdm-guide

## Components (topology ledger)
| id | outcome (one line) | status | evidence path |
|----|-------------------|--------|---------------|
| C1 | Requirements.md (new) — complete DRM decoding requirements doc: engines, binaries, install per-OS, validation | active | README.md:360-388, src/thuis/drm_decrypt.py:40-48 |
| C2 | README DRM section updated — link to Requirements.md + concise quick-start | active | README.md:360-388 |
| C3 | Helper script `scripts/extract_cdm.py` — wvdumper/Frida guidance + existing .wvd validation | active | src/thuis/cdm.py:24-30, .env.example:16-18 |
| C4 | requirements.txt — commented install hints for system deps (Bento4, shaka, ffmpeg) | active | requirements.txt:1-4 |
| C5 | .env.example — comment pointing to Requirements.md + extract_cdm.py | active | .env.example:16-18 |
| C6 | src/thuis/cdm.py — warning references helper script on auto-fetch failure | active | src/thuis/cdm.py:24-30 |
| C7 | Tests for extract_cdm.py output content | active | tests/ |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|------------|----------------|-----------|-------------|
| Engine coverage | Document ALL three engines (mp4decrypt, shaka-packager, ffmpeg), mp4decrypt primary | Matches DECRYPTION_ENGINES list in drm_decrypt.py:40-48 | Yes |
| Install source | Per-OS: Linux apt/pip, macOS Homebrew, Windows Bento4 binaries | Realistic platform coverage | Yes |
| Requirement doc | New `docs/REQUIREMENTS.md` (move/replace DRM section in README) | Keeps README concise, doc is authoritative | Yes |
| Helper script | `scripts/extract_cdm.py` prints wvdumper steps + validates .wvd | Reusable, testable, no auto-exec (legal) | Yes |
| Legal disclaimer | Prominent in Requirements.md + script output | DRM circumvention gray area | Yes |

## Findings (cited - path:lines)
| finding | citation |
|---------|----------|
| requirements.txt only has 4 python deps; no system binary install guidance | requirements.txt:1-4 |
| README DRM section lists engines as requirements but gives no install instructions | README.md:360-388 |
| drm_decrypt.py DECRYPTION_ENGINES: MP4DECRYPT, SHAKA_PACKAGER, FFMPEG; REQUIRED_BINARIES map | src/thuis/drm_decrypt.py:40-48, find_binary:76-94 |
| get_available_decryption_engine() error message lists all 3 + install hint | src/thuis/drm_decrypt.py:114-123 |
| cdm.py CDM_SOURCES all 404 (dead URLs); no extraction guidance | src/thuis/cdm.py:24-30 |
| .env.example WVD_CDM_PATH commented; no .wvd acquisition guidance | .env.example:16-18 |
| DECRYPT_DRM=yes default; decryption blocked only by missing CDM + engine | .env.example:14, src/thuis/main.py |
| requirements.txt uses yt-dlp fork + pywidevine (python-side CDM ready) | requirements.txt:1-4 |

## Decisions (with rationale)
| decision | rationale |
|----------|-----------|
| Create `docs/REQUIREMENTS.md` as authoritative DRM-decoding requirements doc | One place covering engines, binaries, install per-OS, pywidevine, CDM/.wvd, validation |
| Document all 3 engines (mp4decrypt primary, shaka-packager / ffmpeg alternatives) | Mirrors engine fallback chain; user may have any available |
| Per-OS install: Linux (apt bento4 / ffmpeg), macOS (brew bento4 / shaka-packager / ffmpeg), Windows (Bento4 zip / N_m3u8DL-RE) | Practical, tested install paths |
| Helper script validates + prints wvdumper extraction steps; never auto-runs adb/frida | Legal + consent safe; reversible |
| Update cdm.py + .env.example + README to all point at Requirements.md and extract_cdm.py | Single source of truth, discoverable at every failure point |
| requirements.txt: add commented system-dep hints (not pip deps) | Keeps pip deps clean, documents non-pip needs |
| Tests assert extract_cdm.py prints key steps + validates .wvd | Regression guard on guidance content |

## Scope IN
- New `docs/REQUIREMENTS.md` covering: decryption engine options + install per OS (mp4decrypt/Bento4, shaka-packager, ffmpeg), pywidevine/pywidevine L3, WVD CDM acquisition (wvdumper/Frida Android path + community options), environment vars, full validation checklist, legal disclaimer
- README.md: replace/reduce DRM section → concise quick-start + link to REQUIREMENTS.md
- requirements.txt: commented install hints for system binaries
- .env.example: comment referencing REQUIREMENTS.md + extract_cdm.py
- New `scripts/extract_cdm.py`: prints wvdumper step-by-step guide + validates existing .wvd in cache path
- src/thuis/cdm.py: warning references extract_cdm.py on auto-fetch failure
- Tests for extract_cdm.py (output contains key steps, validates .wvd)

## Scope OUT (Must NOT have)
- Do NOT bundle/download .wvd or CDM files
- Do NOT auto-execute Frida/adb/wvdumper commands
- Do NOT add binary deps to pip requirements.txt (system packages)
- Do NOT modify drm_decrypt.py engine logic or DECRYPTION_ENGINES ordering
- Do NOT auto-fetch from community CDM repos
- Do NOT add shaka-packager/ffmpeg executable changes — documentation only

## Open questions
None — grounded in existing codebase patterns and engine fallback chain.

## Approval gate
status: approved
Approach approved by user ("Very thoughtful docs to get all requirements for the decoding of the DRM"). Plan written to .omo/plans/drm-mp4decrypt-cdm-guide.md.