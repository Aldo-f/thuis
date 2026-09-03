---
slug: vrtmax-drm-handling
status: approved
intent: clear
review_required: false
pending-action: .omo/plans/vrtmax-drm-handling.md written
approach: full auto escalation — DRM detected → prefer non-DRM source (fork patch) → auto-provision L3 CDM (WVD_CDM_PATH) → pywidevine license + N_m3u8DL-RE decrypt/mux → playable file; graceful degrade + persisted drm status at every stage
---

# Draft: vrtmax-drm-handling (v3 — APPROVED, all forks closed)

## User decisions (final — supersede earlier drafts)
- **Pipeline**: DRM-source → Find non-DRM source → (no prompts — fully automatic) → Attempt real DRM decryption. Goal: "DRM protected videos like flikken-maastricht-s17a2 can be downloaded and played."
- **Creds**: `kuxelu@ipdeer.com` / `Els123456` ARE the real creds (match repo defaults main.py:127-128). My earlier "dead creds" probe was a naive REST call; the fork's real login flow (patch1) works. Execution must reuse fork login internals, never re-derive.
- **CDM**: fully automatic provisioning. Auto-fetch a ready-to-use L3 CDM on first need → assemble `.wvd` (pywidevine create-device) → validate → cache at WVD_CDM_PATH (tool-managed default). User-set WVD_CDM_PATH to an existing file is honored. KeyDive-based automated extraction = documented fallback only.
- **Automatic**: DECRYPT_DRM default `yes` (no ask prompts); `.env` override retained.
- **Tests**: tests-after; agent-executed QA (incl. real-run on s17a2 producing a playable file) always included.

## Components (final topology)
| id | outcome | status |
|----|---------|--------|
| C1 | DRM detection: Popen stderr-pipe tee (live + captured), classifier on `This video is DRM protected`, persist `drm` status, scheduled-skip, `--now` retry, exit-0 batch semantics | to build (explore lane confirmed main.py:1464-1468 no capture; metadata_fetcher.py:104-110 capture precedent) |
| C2 | Fork vrt.py patch2: prefer non-DRM targets when present; else emit `_vrt_drm_*` metadata (VUDRM token, MPD url, init-segment url) instead of aborting; tag v2026.06.09-patch2 + requirements bump | blocked by C3 proof |
| C3 | Probe helper importing the fork's VRTIE internals (login + aggregator JSON dump) — proves: do DRM titles ship non-DRM targets? + yields VUDRM/MPD inputs; uses real .env creds | first execution gate |
| C4 | Decrypt worker: pywidevine 1.9.0 (X-VUDRM-TOKEN header, PSSH from init segment, privacy-mode service cert via VUDRM proxy) → content keys → N_m3u8DL-RE subprocess (`--key KID:KEY`, engine mp4decrypt/shaka) → playable mp4 | after C2/C6 |
| C5 | Policy gate: DECRYPT_DRM default yes, .env override, NO prompts (user: all automatic) | trivial |
| C6 | CDM provisioner: auto-download L3 CDM (VideoHelp 413719 AVD zip / .wvd mirror) → create-device → `pywidevine test` validate → cache ~/.thuis/cdm/l3.wvd; honor WVD_CDM_PATH override; failure → clear error + degrade, never crash | after C4 lib confirmed |

## Key external findings (researched 2026-09-01)
- pywidevine 1.9.0 (2025-12-22), Py3.13 OK, GPL-3.0. API: Device.load→Cdm.from_device→open→get_license_challenge(pssh, STREAMING, privacy) → parse_license → get_keys("CONTENT").
- VRT license: POST challenge to `https://widevine-proxy.drm.technology/proxy` with `X-VUDRM-TOKEN: <drm field>` (plugin.video.vrt.nu streamservice.py:42,74). VUDRM first needs a service certificate from the same endpoint.
- PSSH NOT in VRT MPD (forum.videohelp.com #419558) → parse from DASH init segment (Widevine system ID edef8ba9-...).
- N_m3u8DL-RE (MIT, active): does MPD/HLS download + Widevine key decrypt + mux in one binary; `--key KID:KEY`; engines MP4DECRYPT (default) / SHAKA_PACKAGER / FFMPEG. Chosen as decrypt/mux engine (battle-tested, avoids hand-rolling segment decryption).
- Ready-to-use L3 CDMs: VideoHelp thread 413719 hosts ~30 AVD L3 CDMs (pem+bin zips → `pywidevine create-device`); some revoked — validate with `pywidevine test`. No official source; legal exposure (DMCA §1201/WV ToS) is user-side, documented in README.
- devine archived (2025-07-09) → excluded. KeyDive (MIT, `pip install keydive`) = automated personal-device dump fallback.

## Decisions
- D1 stderr tee via Popen; classifier on marker; non-DRM errors keep exit-1 path.
- D2 `drm` status in WatchlistDB.entries.last_status; scheduled skip; `--now` retry; no schema migration.
- D3 all-DRM batch → exit 0 + summary.
- D4 escalation order (user-locked, automatic): normal → non-DRM fallback → CDM/decrypt attempt → any failure = graceful skip + drm status.
- D5 no prompts; DECRYPT_DRM default yes.
- D6 CDM provisioning IS in scope (user decision) — but repo never embeds a CDM; only downloads/assembles/caches at runtime; override honored.
- D7 DRM metadata bridge: ONE fork patch2 (non-DRM preference + `_vrt_drm_*` emission) reused by C3 and C4; `-J` dump consumes it.
- D8 tests-after; QA incl. real s17a2 playable-file check.
- D9 decrypt engine = N_m3u8DL-RE subprocess (binary resolved at runtime; engines tried in order MP4DECRYPT→SHAKA_PACKAGER); pycenc per-track only if engine missing.
- D10 no watchlist/infra/compose/scene-template changes.

## Approval gate
status: approved (user answered all forks; no new open questions). Loop guard: resume from this file or the written plan.

## Scope OUT (still hard)
- NO CDM file embedded in repo; NO DRM bypass in the yt-dlp fork's download path (fork only prefers non-DRM + reports metadata).
- NO new services, cron, infra/ or docker-compose edits, watchlist format, scene-template changes.
- NO silent data loss (never recorded as downloaded), NO retry spam.