# Plan: Embed all source subtitles into MP4 (default ON) + FC De Kampioenen re-import

- Date: 2026-10-12
- Repo: `/mnt/HDD1/dev/06-apps-thuis-v4` (branch `v4/main`)
- Status: IN PROGRESS — Task 1 (probe) COMPLETE

## Goal

Make thuis download **all subtitle tracks the VRT MAX source offers** and mux them into the final MP4 as `mov_text` (toggleable in players), **enabled by default**; then remove all FC De Kampioenen torrents from qBittorrent and re-add the 3 seasons with subtitles embedded.

## Verified context (from codebase reads + real probes — trust these, do not re-derive)

1. **VRT MAX serves exactly ONE subtitle language: `nl` (Dutch)** for FC De Kampioenen.
   Probed with real creds:
   ```
   .venv/bin/python -m yt_dlp --write-subs --sub-langs all --convert-subs vtt --simulate \
     --no-color --username <creds.email> --password <creds.password> \
     'https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/3/f-c--de-kampioenen-s3a1/'
   ```
   → output: `[info] pbs-pub-...: Downloading subtitles: nl`. That is the only track.
   The VRT extractor hardcodes the key: `.venv/lib/python3.13/site-packages/yt_dlp/extractor/vrt.py`
   line 87 `subtitles.setdefault('nl', ...)` (CLOSED captions only).
2. **Credentials:** `src/thuis/main.py:152-153` — `DEFAULT_EMAIL = "kuxelu@ipdeer.com"`,
   `DEFAULT_PASSWORD = "Els123456"`, merged over `config.local.yaml` `credentials.email/password`.
   (The `VRT_EMAIL`/`VRT_PASSWORD` env vars are EMPTY on this machine — do not use them.)
3. **Subtitle file naming:** yt-dlp writes `<video-stem>.nl.vtt` next to the MP4,
   e.g. `FC.De.Kampioenen.S03E01.1080p.WEB-DL.AAC.x264.nl.vtt`.
   A plain `*.vtt` glob WOULD also match, but stem-scoped matching is required
   (shared output dir holds many episodes).
4. **ffmpeg 7.1.5 + ffprobe** at `/usr/bin/ffmpeg`. `src/thuis/transcoder.py` already
   shells out to ffmpeg (subprocess + logger style, `check_ffmpeg()` helper exists).
5. **Existing FC De Kampioenen files:** 21 episodes, **FLAT** in
   `/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen/`
   (NO `Season N/` subdirs — the old plan's glob `*/Season */` is wrong).
   All `1080p`, streams = `h264, aac` ONLY, **no subtitle stream, no loose .vtt**.
6. **Episode DB** (`~/.thuis/state.db`, table `downloaded_files`) marks all episodes
   downloaded → a normal run skips them ("last seen") and no `.vtt` is produced.
   Re-download therefore needs `--force` (flag exists in `src/thuis/cli/args.py`).
7. **Real CLI path:** `thuis.sh` → `python -m thuis.main`.
   `build_yt_dlp_args` at `src/thuis/main.py:484` — signature
   `(urls, dry_run=False, output_dir=Path(DEFAULT_OUTPUT_DIR), output_template=None,
   email=None, password=None, resolution=None)`. Podcast detected via
   `is_podcast = output_template is not None and "podcast" in str(output_template).lower()`.
   Single real call site: `main.py` line ~2177
   `url_args_list = build_yt_dlp_args([download_url], dry_run=args.dry_run,
   output_dir=args.output_dir, output_template=scene_template, email=email,
   password=password, resolution=args.profile_str)`.
   `src/thuis/cli/orchestrator.py:65` calls it with WRONG kwargs
   (`url=, args=, content_type=`) — dead/broken code, watchlist-runner path only.
   **Do NOT fix it in this plan.**
8. **Transcode is OFF by default** — commands below use no `--transcode`, so yt-dlp
   writes the MP4 directly and no re-encode runs.
9. **PostprocessContext** (`src/thuis/plugin_host.py:22`, frozen dataclass):
   `filepath, metadata, output_dir, dry_run, category="", default_tag=""`.
10. **`pm.run_plugins(ctx)` call sites in main.py:** lines ~2045 (fs-skip season
    pack, file var `best`), ~2127 (fs-skip, `best`), ~2263 (auto-upload fresh
    download, `filepath`), plus "already exists" skip at ~2150 (`output_file`,
    `continue` before plugins).
11. **Config:** `src/thuis/config.py` `get_config()` deep-merges `config.yaml` +
    gitignored `config.local.yaml`. Non-secret keys → `config.yaml`.
    Never commit `config.local.yaml`; never put secrets in `config.yaml`.
12. **qBittorrent** at `torrent.aldof.duckdns.org` (creds in `config.local.yaml`
    `plugins.torrent_uploader.qbittorrent`). **IP ban (403) was recently active** —
    Task 7 probes auth ONCE and hard-stops if banned.
13. **QBittorrentClient** (`src/thuis/plugins/qbittorrent_client.py`): `url_base`
    (line 34), `auth_log_in()` (83), `add_torrent` (180), `torrents_info` (250).
    No delete method — use `client.session.post(f"{url_base}/api/v2/torrents/delete",
    data={"hashes": csv, "deleteFiles": "false"})`.
14. **Test runner:** `.venv/bin/pytest -q` from repo root. Baseline **433 passed**
    (tests live in `tests/` flat, per `pyproject.toml [tool.pytest.ini_options]`).
    `tests/thuis/` subdir does NOT exist — do not assume it.

## Architecture

Three small additions:
1. `build_yt_dlp_args()` gains `--write-subs --sub-langs all --convert-subs vtt`
   for video content when subtitles are enabled (config `subtitles.embed`,
   default true; CLI `--no-subtitles` disables).
2. `transcoder.py` gains `find_subtitle_files()` / `video_has_subtitle_stream()` /
   `embed_subtitles()` — muxes sibling `<stem>.<lang>.vtt` into the MP4 as
   `mov_text` with `-c copy` (no re-encode), atomic via temp file, idempotent.
3. `main.py` calls `embed_subtitles()` on the resolved file after the download/
   transcode step and **before** every `pm.run_plugins(ctx)` so the `.torrent`
   always hashes the final subbed file.

## Step-by-step tasks

### Task 1 — Probe real subtitle output (DONE)

Real download of S03E01 to `/home/aldo/.hermes/cache/scratch/subs-probe/`
produced a 1.2 GB MP4 with **no** `.vtt` (current code requests no subs).
`--simulate` with `--write-subs --sub-langs all --convert-subs vtt` + real
creds prints `Downloading subtitles: nl` — one track, Dutch. Findings 1-3 above.

### Task 2 — Config: `subtitles` section, default enabled (~5 min)

**Files:** `config.yaml` and `config.yaml.example` (keep in sync).

Add top-level section after the `network:` block in `config.yaml`:

```yaml
# Subtitle settings
subtitles:
  # Download + mux all source subtitle tracks into the MP4 as mov_text
  # (toggleable track). Missing section = enabled.
  embed: true
  # Which languages to write: "all" = every language the source provides
  langs: "all"
```

Same block in `config.yaml.example`.

Verify:
```
.venv/bin/python -c "from thuis.config import get_config; print(get_config().get('subtitles'))"
```
Expected: `{'embed': True, 'langs': 'all'}`

Commit: `git add config.yaml config.yaml.example && git commit -m "feat: add subtitles config section (embed: true default)"`

### Task 3 — `build_yt_dlp_args`: write all subtitles (TDD, ~15 min)

**Files:** `src/thuis/main.py` (function at line 484), `src/thuis/cli/args.py` (flag).

**Step 3a — failing tests.** New file `tests/test_subtitles_args.py`:

```python
from pathlib import Path
from thuis.main import build_yt_dlp_args


def test_video_gets_all_subtitles_by_default(tmp_path):
    a = build_yt_dlp_args(["https://www.vrt.be/x"],
                          output_dir=tmp_path,
                          output_template="Show.S01E01.%(ext)s",
                          subtitles_enabled=True)
    assert "--write-subs" in a
    assert a[a.index("--sub-langs") + 1] == "all"
    assert "--convert-subs" in a
    assert a[a.index("--convert-subs") + 1] == "vtt"


def test_podcast_never_gets_subtitles(tmp_path):
    a = build_yt_dlp_args(["https://www.vrt.be/x"],
                          output_dir=tmp_path,
                          output_template="podcast.S01E01.%(ext)s",
                          subtitles_enabled=True)
    assert "--write-subs" not in a


def test_subtitles_disabled(tmp_path):
    a = build_yt_dlp_args(["https://www.vrt.be/x"],
                          output_dir=tmp_path,
                          output_template="Show.S01E01.%(ext)s",
                          subtitles_enabled=False)
    assert "--write-subs" not in a
```

Run: `.venv/bin/pytest tests/test_subtitles_args.py -q` → **expected FAIL**
(`TypeError: unexpected keyword 'subtitles_enabled'`).

**Step 3b — implementation.** In `src/thuis/main.py`:

Signature becomes:
```python
def build_yt_dlp_args(urls, dry_run=False, output_dir=Path(DEFAULT_OUTPUT_DIR),
                      output_template=None, email=None, password=None,
                      resolution=None, subtitles_enabled=True):
```

In the video (else) branch, after the existing
`args += ["-f", fmt, ..., "--no-color"]` block, add:
```python
    if subtitles_enabled and not is_podcast:
        args += ["--write-subs", "--sub-langs", "all", "--convert-subs", "vtt"]
```

At the single real call site (line ~2177) add the parameter:
```python
            url_args_list = build_yt_dlp_args(
                [download_url], dry_run=args.dry_run, output_dir=args.output_dir,
                output_template=scene_template, email=email, password=password,
                resolution=args.profile_str,
                subtitles_enabled=not args.no_subtitles and _subs_embed_enabled(),
            )
```

Add helper near `build_yt_dlp_args`:
```python
def _subs_embed_enabled() -> bool:
    # Top-level `subtitles.embed` config; default True.
    try:
        from thuis import config as _tc
        return bool((_tc.get_config().get("subtitles") or {}).get("embed", True))
    except Exception:
        return True
```

In `src/thuis/cli/args.py`, add the flag in the download group (next to `--force`):
```python
    parser.add_argument("--no-subtitles", action="store_true",
                        help="Skip subtitle download/embedding (default: embed all source subtitles)")
```

Run: `.venv/bin/pytest tests/test_subtitles_args.py -q` → 3 passed.
Full: `.venv/bin/pytest -q` → all pass (433 + 3).

Commit: `git add -A && git commit -m "feat: yt-dlp writes all source subtitles by default (--no-subtitles to disable)"`

### Task 4 — `embed_subtitles()` in transcoder (TDD, ~20 min)

**File:** `src/thuis/transcoder.py` (append; style = subprocess + logger).

**Step 4a — failing tests.** New file `tests/test_subtitle_embed.py`:

```python
import subprocess
from pathlib import Path
from unittest.mock import patch

from thuis.transcoder import (
    find_subtitle_files, video_has_subtitle_stream,
    embed_subtitles, _subtitle_lang_tag,
)


def _mk(tmp_path, name):
    p = tmp_path / name
    p.write_bytes(b"x")
    return p


class TestFindSubtitleFiles:
    def test_finds_matching_siblings_only(self, tmp_path):
        v = _mk(tmp_path, "Fc.De.Kampioenen.S03E01.1080p.WEB-DL.mp4")
        _mk(tmp_path, "Fc.De.Kampioenen.S03E01.1080p.WEB-DL.nl.vtt")
        _mk(tmp_path, "Other.S01E01.mp4")
        _mk(tmp_path, "Other.S01E01.nl.vtt")
        names = [f.name for f in find_subtitle_files(v)]
        assert names == ["Fc.De.Kampioenen.S03E01.1080p.WEB-DL.nl.vtt"]

    def test_no_subs(self, tmp_path):
        assert find_subtitle_files(_mk(tmp_path, "Show.mp4")) == []


class TestLangTag:
    def test_nl(self):
        assert _subtitle_lang_tag(Path("a.nl.vtt")) == "nld"

    def test_plain(self):
        assert _subtitle_lang_tag(Path("a.vtt")) == "und"


class TestEmbed:
    def test_no_sub_files_is_success_noop(self, tmp_path):
        ok, err = embed_subtitles(_mk(tmp_path, "Show.mp4"), dry_run=False)
        assert ok and "no subtitle" in err.lower()

    def test_already_embedded_skips_and_cleans(self, tmp_path):
        v = _mk(tmp_path, "Show.mp4")
        _mk(tmp_path, "Show.nl.vtt")
        with patch("thuis.transcoder.video_has_subtitle_stream", return_value=True):
            ok, err = embed_subtitles(v, dry_run=False)
        assert ok and "already" in err.lower()
        assert not (tmp_path / "Show.nl.vtt").exists()

    def test_mux_is_copy_mov_text(self, tmp_path):
        v = _mk(tmp_path, "Show.mp4")
        _mk(tmp_path, "Show.nl.vtt")
        with patch("thuis.transcoder.video_has_subtitle_stream", return_value=False), \
             patch("thuis.transcoder.check_ffmpeg", return_value=True), \
             patch("subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, stdout="", stderr="")) as m:
            ok, err = embed_subtitles(v, dry_run=False)
        assert ok, err
        cmd = m.call_args[0][0]
        assert "-c" in cmd and "copy" in cmd
        assert "mov_text" in cmd
        assert not (tmp_path / "Show.nl.vtt").exists()

    def test_dry_run_changes_nothing(self, tmp_path):
        v = _mk(tmp_path, "Show.mp4")
        _mk(tmp_path, "Show.nl.vtt")
        with patch("thuis.transcoder.video_has_subtitle_stream", return_value=False):
            ok, err = embed_subtitles(v, dry_run=True)
        assert ok
        assert (tmp_path / "Show.mp4").exists()
        assert (tmp_path / "Show.nl.vtt").exists()  # untouched in dry-run
```

Run: `.venv/bin/pytest tests/test_subtitle_embed.py -q` → **expected FAIL**
(ImportError).

**Step 4b — implementation.** Append to `src/thuis/transcoder.py`
(add `import json` / `import re` at top if missing):

```python
SUBTITLE_EXTS = (".vtt", ".srt")


def find_subtitle_files(video: Path) -> list[Path]:
    """Sibling subtitle files belonging to ``video`` (stem-scoped, sorted)."""
    video = Path(video).resolve()
    stem = video.name[: -len(video.suffix)]
    out = []
    try:
        entries = sorted(video.parent.iterdir())
    except OSError:
        return out
    for f in entries:
        if f.suffix.lower() not in SUBTITLE_EXTS:
            continue
        base = f.name[: -len(f.suffix)]
        if base == stem or base.startswith(stem + "."):
            out.append(f)
    return out


def video_has_subtitle_stream(video: Path) -> bool:
    """True if the container already contains at least one subtitle stream."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-select_streams", "s", str(video)],
            capture_output=True, text=True, timeout=15)
        return r.returncode == 0 and len(json.loads(r.stdout).get("streams", [])) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return False


def _subtitle_lang_tag(sub: Path) -> str:
    """3-letter language tag from yt-dlp naming; 'nld' for nl, 'und' fallback."""
    name = sub.name
    for ext in SUBTITLE_EXTS:
        if name.lower().endswith(ext.lower()):
            name = name[: -len(ext)]
            break
    tail = name.rsplit(".", 1)[-1]
    if re.fullmatch(r"[a-zA-Z]{2,3}(-[a-zA-Z]{2,4})?", tail):
        tag = tail.split("-")[0].lower()
        return {"nl": "nld", "en": "eng", "fr": "fra", "de": "ger"}.get(tag, tag[:3])
    return "und"


def embed_subtitles(video: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Mux all sibling subtitle files into the MP4 as mov_text (toggleable).

    Video/audio are copied, never re-encoded. Atomic: writes
    `<name>.submux.mp4` then replaces. Returns (ok, message);
    no subtitle files is a success no-op.
    """
    video = Path(video).resolve()
    subs = find_subtitle_files(video)
    if not subs:
        return True, "no subtitle files found"
    if video_has_subtitle_stream(video):
        if not dry_run:
            for s in subs:
                s.unlink(missing_ok=True)
        return True, "subtitles already embedded"
    if not check_ffmpeg():
        return False, "ffmpeg not available"
    if dry_run:
        logger.info("[DRY-RUN] would embed %d subtitle(s) into %s", len(subs), video.name)
        return True, "dry-run"

    tmp_out = video.with_name(video.name + ".submux.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(video)]
    for s in subs:
        cmd += ["-i", str(s)]
    cmd += ["-map", "0"] + [f"{i + 1}:0" for i in range(len(subs))]
    cmd += ["-c", "copy", "-c:s", "mov_text"]
    for i, s in enumerate(subs):
        cmd += ["-metadata", f"s:t:{i}:language={_subtitle_lang_tag(s)}"]
    cmd.append(str(tmp_out))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        tmp_out.unlink(missing_ok=True)
        return False, "ffmpeg timed out"
    if r.returncode != 0:
        tmp_out.unlink(missing_ok=True)
        last = (r.stderr or "").strip().splitlines()
        return False, last[-1] if last else "ffmpeg failed"
    tmp_out.replace(video)
    for s in subs:
        s.unlink(missing_ok=True)
    logger.info("Embedded %d subtitle track(s) into %s", len(subs), video.name)
    return True, ""
```

NOTE on `-metadata s:t:{i}:language=`: subtitle streams appear in input order
after `-map 0`; verify the index math against a real ffprobe in Task 6
(single `nl` track → `s:t:0`).

Run: `.venv/bin/pytest tests/test_subtitle_embed.py -q` → all pass.
Full: `.venv/bin/pytest -q` → all pass.

Commit: `git add src/thuis/transcoder.py tests/test_subtitle_embed.py && git commit -m "feat: embed sibling VTT subtitles into MP4 as mov_text (ffmpeg -c copy)"`

### Task 5 — Wire embed into download + auto-upload flow (~15 min)

**File:** `src/thuis/main.py`.

1. **Fresh download path** — after the yt-dlp subprocess for a video URL
   succeeds, before the auto-upload `PostprocessContext` (line ~2248, variable
   `filepath`), insert:

```python
                    if not args.dry_run and filepath is not None and filepath.suffix == ".mp4" and not args.no_subtitles:
                        from thuis import transcoder as _trans
                        ok, msg = _trans.embed_subtitles(filepath, dry_run=False)
                        if ok:
                            logger.info("Subtitles: %s (%s)", filepath.name, msg)
                        else:
                            logger.warning("Subtitle embedding failed for %s: %s", filepath.name, msg)
```

2. **Existing-file skip path** (line ~2143, `output_file` before `continue`):
   same block using `output_file`, guarded by
   `not args.no_subtitles and not args.dry_run and output_file.suffix == ".mp4"`.

3. **fs-skip season-pack paths** (before `pm.run_plugins(ctx)` at ~2045 and
   ~2127, variable `best`): same block with `best`, guarded by
   `best.suffix == ".mp4"`.

Rules:
- Embed failure → warn, never abort (torrent then hashes the sub-less file;
  the warning is loud in the log).
- Audio files (`.mp3`) are never passed (suffix guard; subs are video-only).
- Dry-run: guard with `args.dry_run` so nothing is touched.

Full suite: `.venv/bin/pytest -q` → all pass.
Commit: `git commit -am "feat: embed subtitles after download/skip, before auto-upload plugins"`

### Task 6 — E2E on one episode (~10 min)

```
OUT=/home/aldo/.hermes/cache/scratch/subs-e2e && rm -rf $OUT && mkdir -p $OUT
./thuis.sh "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/3/f-c--de-kampioenen-s3a1/" --output-dir $OUT --force
ffprobe -v quiet -print_format json -show_streams $OUT/*.mp4 \
  | .venv/bin/python -c "import json,sys; print([(s.get('codec_type'),s.get('codec_name'),(s.get('tags') or {}).get('language')) for s in json.load(sys.stdin)['streams']])"
ls $OUT
```
Expected: exactly one `.mp4`, no loose `.vtt`, streams
`[('video','h264',...), ('audio','aac',...), ('subtitle','mov_text','nld')]`.

`--no-subtitles` variant: same run + flag → no `mov_text` stream, no `.vtt`.

### Task 7 — qBittorrent auth probe (HARD GATE, ~2 min)

```
cd /mnt/HDD1/dev/06-apps-thuis-v4 && .venv/bin/python - <<'EOF'
import yaml, sys
from pathlib import Path
sys.path.insert(0, "src")
cfg = yaml.safe_load(Path("config.yaml").read_text())
def deep(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep(a[k], v)
        else:
            a[k] = v
deep(cfg, yaml.safe_load(Path("config.local.yaml").read_text()))
qb = cfg["plugins"]["torrent_uploader"]["qbittorrent"]
from thuis.plugins.qbittorrent_client import QBittorrentClient
c = QBittorrentClient(host=qb["host"], username=qb["username"],
                      password=qb["password"], api_key=qb["api_key"])
print("auth:", c.auth_log_in())
EOF
```
- `auth: True` → continue.
- `auth: False` / 403 → **STOP and report to the user.** No retry loop.
  (Ban lifts after cooldown or manual unban in the WebUI.)

### Task 8 — Delete ALL FC De Kampioenen torrents (~5 min)

Only after Task 7 `auth: True`. Same config-load preamble as Task 7, then:

```python
assert c.auth_log_in()
def is_fc(t):
    blob = (str(t.get("name", "")) + " " + str(t.get("tags", ""))).lower()
    return "kampioenen" in blob
targets = [t for t in c.torrents_info() if is_fc(t)]
print("removing", len(targets))
for t in targets:
    print(" -", t["name"][:70], t["hash"][:12])
ids = [t["hash"] for t in targets]
if ids:
    r = c.session.post(c.url_base + "/api/v2/torrents/delete",
                       data={"hashes": "|".join(ids), "deleteFiles": "false"})
    print("delete status:", r.status_code)
left = [t["hash"] for t in c.torrents_info() if t["hash"] in ids]
print("remaining:", left)
```

**`deleteFiles: false`** — local MP4s survive; they are re-muxed/re-downloaded
in Task 9, not destroyed. Independent verification: `remaining: []`.
If any remain, stop and report which hash failed.

### Task 9 — Re-add FC De Kampioenen seasons 1-3 with subtitles (~60-90 min)

Existing MP4s have no subtitle stream. `--force` re-downloads and writes the
`.nl.vtt`; Task 5's embed step muxes it in; `--auto-upload` then torrents the
FINAL subbed file.

Per-season, sequentially (foreground, long timeout; ~1.2 GB per episode):

```
OUT="/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen"
for S in 1 2 3; do
  timeout 7200 ./thuis.sh "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/$S" \
    --auto-upload --output-dir "$OUT" --force
done
```

After ALL three runs, verify EVERY file:

```
for f in "$OUT"/*.mp4; do
  n=$(ffprobe -v quiet -select_streams s -show_entries stream=codec_name -of csv=p=0 "$f" | grep -c mov_text)
  echo "$n  $(basename "$f")"
done
```
Expected: 21 lines, each starting with `1`. A `0` = that source episode
genuinely has no subs (acceptable — list it in the report); a `0` with a
logged `Subtitle embedding failed` = fix before reporting.

**Final independent verification** (same preamble as Task 7):

```python
for t in c.torrents_info():
    blob = (str(t.get("name", "")) + " " + str(t.get("tags", ""))).lower()
    if "kampioenen" in blob:
        print(t["hash"][:12], "| tags:", t.get("tags"), "| cat:", t.get("category"), "|", t["name"][:70])
```
Expected: FC De Kampioenen torrents present, each tagged `Thuis`
(`default_tag`), save path under `/downloads/Media/tv` (container path —
`_normalize_save_path` handles host→container; never send host paths).

### Task 10 — README + final regression (~5 min)

`README.md` CLI options, add:
```
--no-subtitles  Skip subtitle download/embedding. By default all source
                subtitle tracks are downloaded and embedded into the MP4 as a
                toggleable track (mov_text: toggleable in VLC/Kodi/QuickTime/iOS,
                not in browsers).
```
Commit: `git add README.md && git commit -m "docs: subtitle embedding in README"`

```
.venv/bin/pytest -q    # expected: 433 + 3 + 4 = 440 passed (adjust to actual count)
git log --oneline -8
git status             # clean except gitignored config.local.yaml
```

Report: episodes re-imported, subtitle track per episode (any with zero source
subs listed), final torrent list with tags, test count.

## Tests / validation summary (TDD checkpoints)

| Task | Red | Green | Commit |
|---|---|---|---|
| 2 | — | config prints `{'embed': True, 'langs': 'all'}` | subtitles config |
| 3 | 3 fail (no `subtitles_enabled` kwarg) | 3 pass; suite green | sub args |
| 4 | 8 fail (ImportError) | 8 pass; suite green | embed_subtitles |
| 5 | — (wiring; covered by E2E + suite) | suite green | wiring |
| 6 | — | ffprobe shows `mov_text` (`nld`) | — |
| 7 | — | auth probe (hard gate) | — |
| 8 | — | independent `torrents_info()` → 0 remaining | — |
| 9 | — | 21/21 files with `mov_text`; torrents back with `Thuis` tag | — |

Every commit leaves the full suite green. Never trust printed "(added)"/
"(skipped)" — verify via independent `torrents_info()` query.

## Risks, tradeoffs, and open questions

1. **Browser playback** — `mov_text` toggle works in VLC/Kodi/QuickTime/iOS;
   HTML5 video ignores it. User accepted MP4-only; documented in README.
2. **Only ONE source track (`nl`)** — "all subtitles" = 1 track for this show.
   Code is language-generic; no change if VRT adds more.
3. **Orchestrator signature mismatch** (`src/thuis/cli/orchestrator.py:65`) —
   pre-existing, dead on the CLI path, deliberately NOT touched. Flag to user.
4. **qBittorrent IP ban** — Task 7 hard-stops; code is verified up to Task 6
   even if banned.
5. **Re-download cost** — `--force` re-fetches 21 episodes (~25 GB). Chosen
   over a subs-only hack: it exercises the real pipeline end-to-end.
6. **Transcoded files lose subs** — `--transcode` re-encodes without
   subtitle mapping. Not used in the commands above; noted for later.
7. **Order matters** — embed strictly BEFORE `create_torrent`/`run_plugins` so
   the `.torrent` hashes the final file.
8. **Save path rule** — qBittorrent `save_path` stays the container path
   `/downloads/Media/tv`; never host paths.
9. **Never commit** `config.local.yaml`; no secrets in `config.yaml`.
