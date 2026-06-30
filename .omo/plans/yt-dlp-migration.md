# YT‑DLP Migration Plan (v4)

## TL;DR
> Replace the ffmpeg‑based downloader with a yt‑dlp‑only implementation (as defined in the original `poc.py`). Enable the CLI to accept multiple VRT‑MAX URLs in one call.

## Context
The current `thuis` package uses `thuis/downloader.py` to invoke `ffmpeg` for converting HLS streams to MP4. The repository already contains a proof‑of‑concept script (`poc.py`) that downloads the `yt‑dlp.exe` binary and uses it to fetch the same streams. Moving to yt‑dlp removes the external `ffmpeg` dependency and simplifies installation on Windows/macOS/Linux.

## Work Objectives
1. **Introduce yt‑dlp downloader** – new helper `download_with_yt_dlp`.
2. **Remove ffmpeg wrapper** – delete `thuis/downloader.py` or mark it obsolete.
3. **Update stream orchestration** – `download_video` and `download_season` call the yt‑dlp helper.
4. **CLI multi‑URL support** – allow `thuis <url1> <url2> …` and process each sequentially (re‑using login cookies).
5. **Tests adaptation** – ensure existing tests still pass (they import `download_video`). Adjust any expectations about the output path if needed.
6. **Documentation** – update `README.md` and MkDocs pages to reflect the new dependency on yt‑dlp instead of ffmpeg.

## Verification Strategy
- **Unit‑level**: mock `subprocess.run` to confirm the correct yt‑dlp command line is built (includes `--format`, `--output`, `--restrict-filenames`).
- **Integration**: run a *quick* test against a known short trailer URL (the repository’s test suite already does this). Verify that the output file is created and its size > 1 MB.
- **CI**: add a step in `.github/workflows/test.yml` to check that `yt-dlp` is present after the `poc.py` download step.

## Execution Strategy (parallel waves)
```
Wave 1 (setup & utilities) – 3 tasks (can run in parallel)
  - [x] 1.1  Create `thuis/downloader_yt.py` with `download_with_yt_dlp` implementation (includes binary download helper).
  - [x] 1.2  Add a small helper to download the `yt-dlp.exe` binary if missing (same logic as `poc.py`).
  - [x] 1.3  Write unit tests for the new helper (mock subprocess).

Wave 2 (core migration) – 3 tasks (sequential, depend on Wave 1)
  - [x] 2.1  Replace all imports of `download_with_ffmpeg` with the new yt‑dlp helper in `thuis/stream.py`.
- [x] 2.2  Remove extra triple quote at end of `thuis/stream.py` (fix syntax).
- [x] 2.3  Remove/disable the old `thuis/downloader.py` file.

Wave 3 (CLI & multi‑URL) – 2 tasks (can run in parallel after Wave 2)
- [x] 3.1  Extend `thuis/cli.py` argument parser to accept `nargs='+'` for URLs.
   - [x] 3.2  Loop over the provided URLs, re‑using the same login cookies for each.

Wave 4 (docs & final checks) – 2 tasks (sequential)
  - [x] 4.1  Update README and MkDocs usage sections to mention yt‑dlp and multi‑URL syntax.
  - [x] 4.2  Run full test suite; ensure CI passes.
```

## Granularity
Each task touches a single file or a single logical change, ensuring it can be completed with one `edit` or `task` call.

## Final Verification Wave
- Verify that `thuis --help` shows the new multi‑URL usage example.
- Run `thuis <url1> <url2>` on a fresh clone; both videos should download to `media/…`.
- Ensure the `yt-dlp.exe` binary lives in `poc.py`'s `bin/` directory after the first run.

---