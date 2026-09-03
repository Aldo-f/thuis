# thuis-v4 CLI UX Improvements Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Improve `--help` clarity (group related flags), save podcasts as `.m4a` instead of `.mp4`, and make long `--output-dir` paths easier to enter correctly.

**Architecture:** All three changes live in the thuis-v4 repo (`aldo-f/thuis`, branch `v4/main`, checked out at `~/dev/06-apps-thuis-v4/`). Help text is pure argparse restructuring in `src/thuis/main.py`. The podcast fix adds a yt-dlp ExtractAudio postprocessor for podcast downloads. Path convenience is solved outside the app (env default + symlink) since the app already supports `OUTPUT_DIR` env.

**Tech Stack:** Python 3 argparse, yt-dlp postprocessors, bash completion.

---

## Context found during exploration

- CLI is defined in `src/thuis/main.py` (~line 420 `build_yt_dlp_args`, ~line 1355-1387 podcast branch).
- Podcast branch already strips `--merge-output-format mp4` and swaps format to `bestaudio`, but the HLS stream is MPEG-TS wrapped, so yt-dlp's `[FixupM3u8]` remuxes it into an **mp4** container — hence `.mp4` files for audio-only content.
- `OUTPUT_DIR` env var is already a supported default for `--output-dir`.
- Tests live in `tests/`; existing podcast tests in `tests/test_podcast_urls.py`.

---

## Task 1: Group argparse options and add epilog examples

**Objective:** Make `./thuis.sh --help` show which flags belong together (watchlist-only vs download vs transcode).

**Files:**
- Modify: `src/thuis/main.py` (argparse setup section)

**Step 1: Restructure the parser**

Use `argparse.ArgumentParser(..., epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)` and `add_argument_group()`:

```python
parser = argparse.ArgumentParser(
    prog="thuis",
    description="Download VRT MAX videos using yt-dlp",
    epilog="""examples:
  ./thuis.sh https://www.vrt.be/vrtmax/...            # single URL
  ./thuis.sh --transcode 720p --input-dir media       # batch transcode
  ./thuis.sh --watchlist watchlists/podcast.txt --now # run watchlist now

Watchlist mode requires --watchlist; --now only applies there.""",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
g_dl = parser.add_argument_group("download options")
g_tr = parser.add_argument_group("transcode options")
g_wl = parser.add_argument_group("watchlist options (require --watchlist)")
```

Move arguments into groups:
- **download options**: `urls`, `--file`, `--profile/-p`, `--dry-run`, `--retry`, `--max-episodes`, `--output-dir`
- **transcode options**: `--transcode`, `--allow-upscale`, `--keep-original`, `--transcode-preset`, `--transcode-crf`, `--input-dir`, `--filter`, `--recursive`, `--parallel`
- **watchlist options**: `--watchlist` ("Process a watchlist file …"), `--now` ("Only together with --watchlist: also run entries without a [schedule] line")
- **general** (stay on parser): `--log-level`

Also update help strings: `--now` must literally say "requires --watchlist".

**Step 2: Verify**

Run: `cd ~/dev/06-apps-thuis-v4 && ./thuis.sh --help`
Expected: three labelled sections; no behavior change.

**Step 3: Run existing tests**

Run: `.venv/bin/python3 -m pytest tests/ -x -q`
Expected: all pass (argparse structure change only; if any test parses `--help` text, update it).

**Step 4: Commit**

```bash
git add src/thuis/main.py
git commit -m "cli: group help output and document flag relationships"
```

---

## Task 2: Audio-only streams saved as .m4a instead of .mp4

**Objective:** Any audio-only stream (detected from the HLS manifest, NOT the URL) is downloaded as `.m4a` via lossless remux.

**Detection — manifest-based:** after `_resolve_podcast_stream_url()` returns the HLS URL (or for any resolved stream), inspect the m3u8 master/media playlist: if all variants are audio-only (`CODECS=` contains no `avc1`/`hvc1`/video codec, or the media playlist has no `#EXT-X-STREAM-INF` with video and only AACL/mp4a FourCC), treat it as audio. Implement as:

```python
def is_audio_only_stream(hls_url: str) -> bool:
    """Fetch the m3u8 and decide audio-only purely from codecs/FourCC."""
    # GET manifest; parse CODECS attribute(s)
    # video codecs: avc1, hvc1, hev1, hvc2 → False
    # audio-only codecs: mp4a, AACL, ac-3, ec-3 → True
```

The current VRT podcast m3u8 URLs already carry this in their filter query (`type=="audio"&&FourCC!="AACL"`) and the format id 272 is an AACL audio rendition — the parser must read the actual manifest, not the query string. Cache/short-circuit: one extra HTTP GET per episode is acceptable.

Note: the `/vrtmax/podcasts/` check REMAINS only for stream resolution + title naming (that code path exists because yt-dlp's VRT extractor can't handle podcast pages); it no longer decides the output container.

**Best approach (recommended):** add yt-dlp's `ExtractAudio` postprocessor with `--audio-format m4a` (actually pass `-x --audio-format m4a` equivalents programmatically). The source HLS is AAC (AACL FourCC — visible in the filter query param), so extraction is a lossless container remux: fast, no quality loss. This also removes the `[FixupM3u8]` mp4 remux step.

Alternative rejected: `--remux-video m4a` doesn't apply cleanly here (it's video-oriented); raw ffmpeg remux would duplicate what the postprocessor already does well.

**Files:**
- Modify: `src/thuis/main.py:1375-1387` (podcast branch of the download loop)
- Test: `tests/test_podcast_audio.py` (new)

**Step 1: Write failing test**

```python
"""Podcast downloads should request audio extraction to m4a."""
from unittest.mock import patch

import pytest

from thuismain import build_yt_dlp_args  # adjust import to actual module name


def test_podcast_branch_adds_extract_audio():
    args_list = ["prog", "-f", "bestvideo+bestaudio", "--merge-output-format", "mp4", "url"]
    # call the same transformation used in main() for podcast URLs;
    # factor that block out into a helper first (see Step 2)
    from thuismain import apply_podcast_audio_flags
    result = apply_podcast_audio_flags(args_list)
    assert "-x" in result
    assert "--audio-format" in result
    assert "m4a" in result
    assert "--merge-output-format" not in result
```

(Adjust import names to match how `main.py` exposes things; if `main.py` isn't importable, extract the helper into it anyway — see Step 2.)

**Step 2: Run test to verify failure**

Run: `.venv/bin/python3 -m pytest tests/test_podcast_audio.py -v`
Expected: FAIL — `apply_podcast_audio_flags` not defined.

**Step 3: Implement**

In `src/thuis/main.py`, extract the podcast branch (~lines 1375-1387) into:

```python
def apply_podcast_audio_flags(url_args_list: list[str]) -> list[str]:
    """For audio-only podcast HLS streams: pick bestaudio, drop video merge,
    and remux the TS-wrapped AAC into a proper .m4a container (lossless)."""
    try:
        idx = url_args_list.index("bestvideo+bestaudio")
        url_args_list[idx] = "bestaudio"
    except ValueError:
        pass
    try:
        mi = url_args_list.index("--merge-output-format")
        del url_args_list[mi:mi + 2]
    except ValueError:
        pass
    url_args_list += ["-x", "--audio-format", "m4a"]  # ExtractAudio = container remux only (AAC source)
    return url_args_list
```

Replace the inline block in `main()` with `url_args_list = apply_podcast_audio_flags(url_args_list)`.

Note: the output template already uses `%(ext)s`, so filenames become `.m4a` automatically. Check whether the dedupe/state DB lookups elsewhere hard-code `.mp4` for podcasts (grep showed `.mp4` in `scene_namer.py` / `watchlist.py` fallbacks — those are video paths, verify podcast titles flow through `safe_title.%(ext)s` and are unaffected).

**Step 4: Verify against real runtime (mandatory)**

Run:
```bash
rm -f "/mnt/HDD1/nextcloud/data/aldo/files/Media/podcasts/_seed/2..De.'miljonairsrondgang'.mp4"
./thuis.sh "https://www.vrt.be/vrtmax/podcasts/radio-1/d/de-gifmenger" \
  --filter "miljonairsrondgang" \
  --output-dir /mnt/HDD1/nextcloud/data/aldo/files/Media/podcasts/_seed
ls -la <output-dir> | grep miljonairs
```
Expected: file ends in `.m4a`; log shows `ExtractAudio` postprocessor, no `[FixupM3u8]` mp4 output. Confirm playability: `ffprobe <file>` shows codec `aac`.

**Step 5: Full test suite + commit**

Run: `.venv/bin/python3 -m pytest tests/ -q` → all pass.
```bash
git add src/thuis/main.py tests/test_podcast_audio.py
git commit -m "podcast: save episodes as m4a via lossless ExtractAudio instead of mp4"
```

---

## Task 3: Easier/correct --output-dir entry

**Objective:** Avoid typos in the very long HDD1 Nextcloud path.

**Approach (no app code needed — app already supports `OUTPUT_DIR`):**
1. Set the default once in `~/.bashrc`: `export OUTPUT_DIR=/mnt/HDD1/nextcloud/data/aldo/files/Media` — then `./thuis.sh <url>` just works, and you only append short subpaths like `/podcasts/_seed` (tab-completable because they're real directories).
2. Create a symlink for quick navigation/typing: `ln -s /mnt/HDD1/nextcloud/data/aldo/files/Media ~/media-hdd` — then `--output-dir ~/media-hdd/podcasts` is short and tab-completes.
3. Optional nicety (only if Aldo wants app-side support): add a small config file `~/.thuis/config.toml` with `default_output_dir` used when neither flag nor env is set. YAGNI unless requested.

**Steps:**
1. Add export line to `~/.bashrc`; `source ~/.bashrc`.
2. Create symlink; verify `./thuis.sh --help` shows the env default hint: extend the `--output-dir` help string to mention `(default: media or OUTPUT_DIR env)` — already present, optionally append example value shape.
3. Verify: `./thuis.sh --dry-run <some-url>` prints destination under the env-derived dir without typing the long path.

**Commit:** none needed (shell-only), except optional help-string tweak in Task 1's commit.

---

## Risks / tradeoffs

- **m4a vs mp3:** m4a/AAC keeps original quality with zero re-encode cost on a Pi 5. If some player needs mp3, that would require real transcoding — not recommended.
- **State DB dedupe:** previously downloaded episodes recorded with `.mp4` filenames may re-download once after this change (filename differs). Mitigate by deleting old `.mp4` podcast files or accepting one-time re-fetch.
- **Argparse grouping** changes `--help` layout only; positional `urls` must remain top-level (groups don't affect parsing).
- **Importability of main.py** for testing: if `main.py` has heavy import side effects, place the helper in a small module or guard with `if __name__ == "__main__"` (check current state before Task 2).

## Open questions

- Should the m4a change also apply to watchlist-driven podcast entries? Yes — they go through the same `main()` branch, so covered automatically.
- Prefer `.m4a` or `.mp3`? Plan assumes `.m4a` (lossless passthrough).
