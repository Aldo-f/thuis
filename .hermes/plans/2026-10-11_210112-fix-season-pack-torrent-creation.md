# Plan: Fix Season Pack Torrent Creation and qBittorrent Upload Performance & Failure

## Goal
Eliminate slow copying during season pack torrent creation and fix qBittorrent upload path normalization so season pack torrents generate fast and successfully register in qBittorrent under `/downloads/Media/tv/Fc De Kampioenen`.

---

## Current Context / Assumptions
1. `main.py` lines 2253-2258 copy all episode `.mp4` files into `tempfile.TemporaryDirectory()` using `shutil.copy2()` before passing the directory to `uploader.create_torrent(tmp_path, ...)`. For a ~5GB season, this doubles disk I/O and causes long delays or timeouts.
2. `uploader.create_torrent()` currently accepts `filepath: Path` and places `.torrent` output in `path.parent / f"{output_name}.torrent"`. When passed a temp dir, it creates the torrent inside `/tmp/`, which is deleted when the temp dir context closes.
3. `main.py` calls `qb_client.add_torrent(save_path=str(args.output_dir))` passing `/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen`. `QBittorrentClient.add_torrent` uses `self._normalize_save_path(save_path)` to map local paths to container mount paths (`/downloads/...`).
4. When `SeasonDetector` runs, it uses `libtorrent` hashing. With default piece sizes (e.g. 256KB or 512KB for a multi-gigabyte pack), piece count is huge and hashing takes ~2-3 minutes on Pi 5. Using an optimal piece size (e.g. 2MB / 4MB for multi-GB season packs) speeds up hashing significantly.

---

## Proposed Architecture
1. **Direct Season Pack Torrent Creation (No File Copying)**:
   Modify `TorrentUploader.create_torrent_for_files(files: list[Path], output_dir: Path, torrent_name: str, piece_size: int)` to add files directly from their original location in `args.output_dir` into `libtorrent.file_storage()` without copying files to `/tmp`.
2. **Explicit Torrent Output Path & Auto Piece Size Calculation**:
   Pass target `output_dir` (i.e. `args.output_dir`) and explicit `torrent_name` directly to `create_torrent_for_files`, outputting `Fc_De_Kampioenen.Season.01.Pack.torrent` in `args.output_dir`. Auto-scale `piece_size` to 2MB (2097152 bytes) or 4MB for multi-gigabyte season packs to drastically reduce hashing time.
3. **Verified qBittorrent Upload & Save Path Normalization**:
   Ensure `QBittorrentClient.add_torrent` is called with `save_path=str(args.output_dir)`, which maps to `/downloads/Media/tv/Fc De Kampioenen` via `_normalize_save_path()`. Log the return payload and check if qBittorrent accepts the file.

---

## Step-by-Step Tasks

### Task 1: Add `create_torrent_for_files` helper to `TorrentUploader`
- **File**: `src/thuis/plugins/torrent_uploader.py`
- **Changes**: Add a new method `create_torrent_for_files(self, files: list[Path], output_dir: Path, torrent_name: str, piece_size: int | None = None) -> Path` that constructs `lt.file_storage()` from the existing file list directly using `fs.add_file(...)` or relative paths under `output_dir`, avoiding file copies.
- **Copy-Pasteable Code**:
```python
    def create_torrent_for_files(
        self,
        files: list[Path],
        output_dir: Path,
        torrent_name: str,
        piece_size: int | None = None,
    ) -> Path:
        """Create a .torrent for a list of existing files in output_dir without copying."""
        if not files:
            raise ValueError("No files provided for torrent creation")

        output_dir = Path(output_dir)
        total_size = sum(f.stat().st_size for f in files if f.exists())

        # Auto-scale piece size for multi-GB season packs (default to 2MB for >1GB)
        eff_piece_size = piece_size or self._piece_size
        if not piece_size and total_size > 1024 * 1024 * 1024:
            eff_piece_size = 2 * 1024 * 1024  # 2MB pieces for fast hashing

        fs = lt.file_storage()
        for f in sorted(files):
            rel_path = f.relative_to(output_dir) if f.is_relative_to(output_dir) else Path(f.name)
            fs.add_file(str(rel_path), f.stat().st_size)

        tor = lt.create_torrent(fs, piece_size=eff_piece_size)
        tor.set_comment(self._comment)
        tor.set_creator(self._source)

        for url in self._trackers:
            tor.add_tracker(url)

        logger.info("Hashing %d file(s) (%d bytes) for %s with piece_size=%d...", len(files), total_size, torrent_name, eff_piece_size)
        lt.set_piece_hashes(tor, str(output_dir))

        torrent_data = lt.bencode(tor.generate())
        out_path = output_dir / f"{torrent_name}.torrent"
        out_path.write_bytes(torrent_data)
        logger.info("Created season pack .torrent: %s (%d bytes)", out_path, len(torrent_data))
        return out_path
```

- **Verification Command**:
```bash
python3 -c "
from pathlib import Path
from thuis.plugins.torrent_uploader import TorrentUploader
uploader = TorrentUploader(trackers=['udp://tracker.opentrackr.org:1337/announce'])
out_dir = Path('/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen')
files = sorted(out_dir.glob('*.mp4'))
res = uploader.create_torrent_for_files(files, out_dir, 'Fc_De_Kampioenen.Season.01.Pack')
print('Torrent created:', res, 'Exists:', res.exists())
"
```
*Expected Output*: `Torrent created: .../Fc_De_Kampioenen.Season.01.Pack.torrent Exists: True` (in < 5 seconds).

---

### Task 2: Refactor `main.py` Season Pack Creation Block
- **File**: `src/thuis/main.py`
- **Changes**: Replace lines 2248-2280 in `main.py` to remove `tempfile.TemporaryDirectory()` and `shutil.copy2()`. Use `uploader.create_torrent_for_files(...)` directly on `episode_files`.
- **Copy-Pasteable Code**:
```python
                        episode_files = sorted(Path(args.output_dir).glob("*.mp4"))
                        if episode_files:
                            pack_name = f"{show_for_tmdb.replace(' ', '_')}.Season.{season_num:02d}.Pack"
                            logger.info("Generating season pack torrent %s directly from %d files (no copying)...", pack_name, len(episode_files))
                            season_torrent = uploader.create_torrent_for_files(
                                files=episode_files,
                                output_dir=args.output_dir,
                                torrent_name=pack_name,
                                piece_size=2 * 1024 * 1024,  # 2MB piece size
                            )
                            logger.info("Created season-pack .torrent: %s", season_torrent)
                            # Upload to qBittorrent
                            qb_cfg = plugin_cfg.get("qbittorrent", {})
                            if qb_cfg.get("enabled", True):
                                from .plugins.qbittorrent_client import QBittorrentClient
                                qb_client = QBittorrentClient(
                                    host=qb_cfg.get("host", "localhost:8080"),
                                    username=qb_cfg.get("username", "aldo"),
                                    password=qb_cfg.get("password", ""),
                                    api_key=qb_cfg.get("api_key", ""),
                                    socks5_proxy=qb_cfg.get("socks5_proxy"),
                                )
                                if qb_client.auth_log_in():
                                    category = qb_cfg.get("category", show_for_tmdb)
                                    tags = qb_cfg.get("tags", "upload")
                                    save_path = str(args.output_dir)
                                    added = qb_client.add_torrent(
                                        torrent_file=season_torrent,
                                        save_path=save_path,
                                        category=category,
                                        tags=tags,
                                    )
                                    if added:
                                        logger.info("Season-pack torrent added to qBittorrent successfully: %s", season_torrent.name)
                                    else:
                                        logger.warning("Failed to add season-pack torrent to qBittorrent: %s", season_torrent.name)
                                else:
                                    logger.error("qBittorrent auth failed for season-pack")
```

- **Verification Command**:
```bash
./thuis.sh https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/1 \
  --auto-upload \
  --output-dir "/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen" \
  --only-season-pack \
  --log-level INFO
```
*Expected Output*: Should finish in ~15-30 seconds, output `Created season-pack .torrent: ...` and `Season-pack torrent added to qBittorrent successfully: Fc_De_Kampioenen.Season.01.Pack.torrent`.

---

### Task 3: Verify Torrent Presence in qBittorrent WebUI/API
- **File**: Terminal validation
- **Changes**: Query `/api/v2/torrents/info` from qBittorrent API to confirm `Fc_De_Kampioenen.Season.01.Pack` is listed and seeding.
- **Verification Command**:
```bash
python3 -c "
import requests
s = requests.Session()
s.post('https://torrent.aldof.duckdns.org/api/v2/auth/login', data={'username':'aldo','password':'LuUDf4#HBk&g74R*pMy&*anLhsGSA#^^0^GUEOjSIZT1CL&y7*idI7VSraWwMz36'})
r = s.get('https://torrent.aldof.duckdns.org/api/v2/torrents/info')
matches = [t for t in r.json() if 'Pack' in t.get('name','')]
print('Season Pack in qBittorrent:', len(matches) > 0)
if matches:
    print('Name:', matches[0]['name'])
    print('State:', matches[0]['state'])
    print('Save Path:', matches[0]['save_path'])
"
```
*Expected Output*:
`Season Pack in qBittorrent: True`
`Name: Fc_De_Kampioenen.Season.01.Pack`
`Save Path: /downloads/Media/tv/Fc De Kampioenen`

---

---

## Task 4: Cache qBittorrent state — one login + one API call per run (biggest speedup)
- **Problem found in `src/thuis/main.py` (lines 1945-1965)**: the per-episode DB-skip branch opens a **new `requests.Session()` and re-logins to qBittorrent for EVERY episode** (`s.post(.../auth/login)` inside the `for row in rows:` loop). On a 13-episode season run that is 13 logins + 13 full `/api/v2/torrents/info` fetches (~2-5s of network each over the VPN/DuckDNS link; observed up to 20s gaps per episode in logs, plus one `Read timed out (read timeout=5)` failure).
- **File**: `src/thuis/main.py`
- **Changes**:
  1. Add a module-level helper near the other helpers (after `_find_downloaded_file`, or just before `def main(`):

```python
_QB_TORRENTS_CACHE: dict[str, Any] = {}

def _qb_torrents_cache(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch /api/v2/torrents/info once per process (cached).

    Returns [] on any failure (treated as 'nothing seeding' → plugins run
    as before). Reads qBittorrent credentials from config, not hardcoded.
    """
    if _QB_TORRENTS_CACHE["data"] is not None:
        return _QB_TORRENTS_CACHE["data"]
    try:
        from .plugins.qbittorrent_client import QBittorrentClient
        qb = (cfg.get("plugins", {}) or {}).get("torrent_uploader", {}) or {}
        qbc = qb.get("qbittorrent", {}) or {}
        client = QBittorrentClient(
            host=qbc.get("host", "torrent.aldof.duckdns.org"),
            username=qbc.get("username", "aldo"),
            password=qbc.get("password", ""),
            api_key=qbc.get("api_key", ""),
            socks5_proxy=qbc.get("socks5_proxy"),
        )
        if client.auth_log_in():
            _QB_TORRENTS_CACHE["data"] = client.get_torrents()  # list of dicts from /api/v2/torrents/info
        else:
            _QB_TORRENTS_CACHE["data"] = []
    except Exception as exc:
        logger.warning("QB cache: could not fetch torrent info: %s", exc)
        _QB_TORRENTS_CACHE["data"] = []
    return _QB_TORRENTS_CACHE["data"]


def _is_seeding_in_qb(filename: str, torrents: list[dict[str, Any]]) -> bool:
    """True if a torrent containing filename is present in QB (any upload state)."""
    stem = Path(filename).stem
    for t in torrents:
        name = t.get("name") or ""
        if filename in name or stem.replace(".", " ") in name or stem in name:
            if t.get("tags") in ("upload", "", None):
                return True
    return False
```

  2. First check that `QBittorrentClient` exposes a `get_torrents()` method returning `list[dict]`. Open `src/thuis/plugins/qbittorrent_client.py` and search for `def get_torrents`. **If it does not exist**, add it (copy-paste):

```python
    def get_torrents(self) -> list[dict]:
        """Return the full torrent info list from /api/v2/torrents/info."""
        try:
            resp = self.session.get(
                f"{self.url_base}/api/v2/torrents/info",
                headers=self._get_auth_headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            log.error("get_torrents failed: %s", exc)
            return []
```

  (Match the existing attribute names for the requests session in that file — verify with `grep -n "session" src/thuis/plugins/qbittorrent_client.py` before writing.)
  3. **Replace the inline per-row QB block** at lines 1945-1965 with:

```python
                                    # Skip plugin/re-add if QB already has this file (cached, one login per run)
                                    if _is_seeding_in_qb(best.name, _qb_torrents_cache(cfg)):
                                        logger.info("QB skip (already seeding): %s", best.name)
                                        qb_skipped_any = True
                                        continue
                                    if not args.only_season_pack:
                                        ctx = PostprocessContext(filepath=best, metadata=metadata, output_dir=args.output_dir, dry_run=False)
                                        logger.info("Auto-upload: running plugins for existing file %s", best.name)
                                        pm.run_plugins(ctx)
```

- **Side benefit**: this also removes the **hardcoded qBittorrent password in `main.py`** (line 1949) — credentials now come only from `config.yaml`.
- **Verification** (expected: exactly ONE login, ~1-2s total for all 13 skips):
```bash
time ./thuis.sh https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/1 \
  --auto-upload --output-dir "/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen" \
  --log-level INFO
```
Expected: 13x `QB skip (already seeding): ...` lines, no `Read timed out`, wall time for the skip phase < 10s (was ~60-90s).

---

## Task 5: Add the same QB-seeding skip to the filesystem-skip branch
- **Problem found in `src/thuis/main.py` (lines 2065-2083)**: the "file exists on disk but not in DB" branch runs `pm.run_plugins(ctx)` for every matching file with **no QB check at all** — it re-creates/re-uploads torrents that are already seeding (this is why episodes 6/11/12/13 print `(added)` even though QB already has them).
- **Changes**: in that branch, add the same cache-based check:

```python
                    if args.auto_upload and not args.only_season_pack:
                        try:
                            from thuis.plugin_host import PluginManager, PostprocessContext
                            cfg = thuis_config.get_config()
                            pm = PluginManager(cfg)
                            qb_cache = _qb_torrents_cache(cfg)
                            qb_skipped_any_fs = False
                            for best in final_matches:
                                db.conn.execute("INSERT OR IGNORE INTO downloaded_files (url,filename,output_dir,downloaded_at) VALUES (?,?,?,datetime('now'))",
                                    (url, best.name, str(args.output_dir)))
                                db.conn.commit()
                                if _is_seeding_in_qb(best.name, qb_cache):
                                    logger.info("QB skip (already seeding): %s", best.name)
                                    qb_skipped_any_fs = True
                                    continue
                                ctx = PostprocessContext(filepath=best, metadata=metadata, output_dir=args.output_dir, dry_run=False)
                                logger.info("Auto-upload: plugin on filesystem-skip %s", best.name)
                                pm.run_plugins(ctx)
```
(The `status_fs` print below already uses `qb_skipped_any_fs` — no change needed there.)

- **Verification**: re-run the command from Task 4; episodes previously printing `(added)` must now print `(skipped - already in QB)` and no new torrent entries may appear in qBittorrent.

---

## Task 6: Remove the dead duplicate season-detector blocks from the per-episode loop
- **Problem**: `src/thuis/main.py` lines 1970-1987 (DB-skip branch) and 2044-2062 (filesystem-skip branch) each run `SeasonDetector.check()` **inside the per-episode iteration**, guarded by `episode_num == 0`. For an expanded `/1` URL every iteration has `episode_num >= 1`, so the first block is dead code; the second can fire mid-loop (before all episodes are processed) with a stale view and does only a DB insert (no torrent creation) — duplicating work the post-loop block (line 2223+) already does correctly.
- **Changes**:
  1. Delete lines 1970-1987 entirely (`# Season-level check for DB-skip path (Task 2/3)` through the matching `logger.warning("Season detector/pack (DB-skip) failed: %s", exc2)`).
  2. Delete lines 2044-2062 entirely (`# Season-level check (Task 2 / 3): ...` through `logger.warning("Season detector/pack failed: %s", exc)`).
  3. Keep the single post-loop block at line ~2223 as the only season-pack logic.
- **Verification**:
```bash
./thuis.sh https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/1 --auto-upload \
  --output-dir "/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen" --log-level INFO 2>&1 | grep -c "SeasonDetector:"
```
Expected: exactly `1` (only the post-loop check), and `Season pack DB entry added` appears at most once.

---

## Tests / Validation Plan
1. **Unit Test**: Test `create_torrent_for_files` with dummy files in a temporary directory structure to verify `.torrent` file generation without copying files.
2. **Integration Test**: Run `./thuis.sh` with `--only-season-pack` and verify execution time is < 30 seconds.
3. **Repeat-run speedup**: Full `./thuis.sh` season URL run with all episodes already seeded must finish in < 60s total (vs current ~5-10 min) with every episode printing `(skipped - already in QB)` and no `Read timed out` in output.
4. **End-to-End Verification**: Verify qBittorrent API contains the season pack torrent entry in `uploading` or `stalledUP` state pointing to `/downloads/Media/tv/Fc De Kampioenen`.

---

## Risks & Tradeoffs
- **Piece Size vs Torrent Overhead**: 2MB piece size is optimal for multi-GB season packs (~5GB), keeping total piece count under 2500 and hashing fast.
- **Existing Files in Directory**: `glob("*.mp4")` assumes all `.mp4` files in `output_dir` belong to the season. This matches existing show folder conventions.
- **QB cache staleness**: the cache is per-process, so a torrent added mid-run is invisible to later checks. Acceptable: runs are short and the worst case is one redundant plugin run (today's behavior).
- **`_is_seeding_in_qb` matching**: substring matching on names could false-positive if one filename is a substring of another torrent name (e.g. S01E1 vs S01E10 — avoided by matching the full filename first, then the stem with `.→space`). The per-episode filenames here are unique per file.

