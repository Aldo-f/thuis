# Plan: Thuis Torrent-Uploader & Argument Fix

**Date**: 2026-10-08  
**Branch**: v4/main  
**Status**: Ready for /goal

---

## Problem
- `thuis.sh URL —auto-upload —output-dir DIR` parses flags as URLs (em dash instead of `--`).
- After fixing syntax, download works but `torrent-uploader` plugin produces no `.torrent` file on disk; qBittorrent seed state unknown.
- Need proof that torrent appears at `https://torrent.aldof.duckdns.org` with correct tag.

---

## Target Flow
1. Call with correct flags (`--auto-upload --output-dir`)
2. Download video if missing; skip via dedup if present
3. Post-download: `torrent-uploader` plugin scans dir, creates `.torrent`, adds to qBittorrent via `config.yaml` (`qbittorrent` section: `host: torrent.aldof.duckdns.org`, `api_key`)
4. Verify `.torrent` on disk + qBittorrent torrent entry + accessibility at target URL

---

## Steps
- [1] Confirm `thuis.sh` passes `--` flags correctly (verify `main.py` argparse)
- [2] Remove/prevent duplicate file, run `thuis.sh ... --auto-upload --output-dir ... --dry-run`
- [3] Run real (with `--force` if needed) and confirm video download completes
- [4] Run `thuis torrent-upload` on output dir; check `.torrent` creation
- [5] Verify `qbittorrent` API response (curl to `torrent.aldof.duckdns.org` with `api_key` from `config.yaml`)
- [6] Confirm result with proof (file list / log / screenshot if possible)

---

## Verification Checklist
- [ ] Command parses URL correctly (only `[1/1]`)
- [ ] Video file exists in output dir after download
- [ ] `.torrent` file exists after plugin run
- [ ] qBittorrent reports torrent active (curl to API)
- [ ] No regression on other episodes (217 files scanned, 0 errors)

---

## Risk
- Low: only syntax fix + plugin verification, no code changes to core download logic.
- Dependency: qBittorrent must be running with API enabled (`config.yaml` settings).

---

## Start
Run with `/goal` once files/config are verified.
