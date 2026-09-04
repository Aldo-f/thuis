---
slug: thuis-doctor
status: approved
intent: clear
review_required: false
pending-action: none — plan written to .omo/plans/thuis-doctor.md
approach: Add a `doctor` and `doctor --fix` CLI subcommand that diagnoses DRM pipeline readiness, reports issues with doc links, and auto-fixes installable dependencies
---

# Draft: thuis-doctor

## Components (topology ledger)
| id | outcome (one line) | status | evidence path |
|----|-------------------|--------|---------------|
| C1 | `thuis.doctor` module: check functions for all DRM pipeline components | active | src/thuis/main.py (CLI entry), src/thuis/drm_decrypt.py, src/thuis/cdm.py |
| C2 | CLI subcommand registration: `thuis doctor` and `thuis doctor --fix` | active | src/thuis/main.py argument parsing |
| C3 | Check functions: engines, N_m3u8DL-RE, CDM, pywidevine, env vars, .env | active | Reuses find_binary(), ensure_cdm(), get_decrypt_policy() |
| C4 | Report formatter: colored output, pass/fail, docs links, actionable hints | active | Uses existing logging, adds rich terminal output |
| C5 | Auto-fix logic: install packages (apt/brew/scoop), set DECRYPT_DRM=yes | active | Requires sudo detection, package manager detection |
| C6 | Tests for doctor command (unit + integration) | active | tests/test_doctor.py |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|------------|----------------|-----------|-------------|
| Package manager detection | apt (Debian/Ubuntu), brew (macOS), scoop (Windows) | Covers 95%+ of users | Yes - user can override |
| Auto-fix requires sudo | Prompt for sudo when needed, skip if not available | Safety - don't run sudo silently | Yes - --fix is opt-in |
| Output format | Rich colored text (no external deps) | Zero new dependencies | Yes |
| Exit codes | 0 = all OK, 1 = issues found, 2 = usage error | Standard CLI convention | Yes |
| CDM auto-fix | NOT attempted (legal/hardware) | Must guide to extract_cdm.py | N/A |

## Findings (cited - path:lines)
| finding | citation |
|---------|----------|
| CLI entry at src/thuis/main.py uses argparse with subcommands | src/thuis/main.py:1-50 |
| DRM engine detection: find_binary() in drm_decrypt.py:76-94 | src/thuis/drm_decrypt.py |
| CDM provisioning: ensure_cdm() in cdm.py:237-289 | src/thuis/cdm.py |
| Policy gate: get_decrypt_policy() in main.py | src/thuis/main.py |
| Env loading: dotenv at main.py:108-112 | src/thuis/main.py |
| Requirements: pywidevine, pymp4 in requirements.txt | requirements.txt:1-6 |
| Scripts/extract_cdm.py exists for CDM guidance | scripts/extract_cdm.py |

## Decisions (with rationale)
| decision | rationale |
|----------|-----------|
| New module src/thuis/doctor.py | Keeps CLI clean, separates concerns |
| Reuse existing detection functions | No duplication, single source of truth |
| --fix installs via system package manager | Only way to install mp4decrypt/ffmpeg/N_m3u8DL-RE |
| --fix writes DECRYPT_DRM=yes to .env | Simple, reversible, user-visible |
| --fix does NOT attempt CDM extraction | Legal/hardware constraints |
| Output includes links to docs/REQUIREMENTS.md and scripts/extract_cdm.py | Self-documenting, guides user |

## Scope IN
- New src/thuis/doctor.py with check_* functions for each component
- CLI subcommand in main.py: `doctor` and `doctor --fix`
- Checks: decryption engines (mp4decrypt, shaka-packager, ffmpeg), N_m3u8DL-RE, CDM (.wvd), pywidevine, pymp4, DECRYPT_DRM env, .env file
- Report: colored pass/fail, docs links (REQUIREMENTS.md, extract_cdm.py), actionable hints
- Auto-fix: install packages via detected package manager (apt/brew/scoop), write DECRYPT_DRM=yes to .env
- Exit codes: 0=ready, 1=issues, 2=error
- Tests: unit tests for check functions, integration test for CLI

## Scope OUT (Must NOT have)
- Do NOT auto-extract CDM (legal/hardware)
- Do NOT modify download pipeline logic
- Do NOT add new Python dependencies (rich, colorama) - use ANSI codes
- Do NOT run sudo without explicit user consent (prompt)
- Do NOT change existing CLI behavior

## Open questions
None - all decisions grounded in existing codebase patterns.

## Approval gate
status: awaiting-approval
Approach: New CLI subcommand module + main.py integration + tests. Reuses all existing detection logic. Auto-fix limited to package installs + env var. CDM extraction guided to existing helper.