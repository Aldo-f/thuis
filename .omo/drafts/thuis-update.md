# Draft: thuis.sh - Resolution & Retry updates

## Requirements (confirmed)

1. **Resolution profile (`-p` / `--profile`)**:
   - Add CLI flag to specify video resolution: `-p 1080p`, `-p 720p`, `-p 2160p`
   - Insert resolution into output filename (after SxxExx, before WEB-DL):
     `Fc.De.Kampioenen.S07E08.1080p.WEB-DL.mp4`
   - Override yt-dlp format string: `bestvideo[height<=1080]+bestaudio/best[height<=1080]`
   - When `-p` is **not** given: keep current behavior (best quality from metadata)

2. **Retry / missing episode support (`--retry` flag)**:
   - Adding `--retry` should re-process all given URLs
   - For each URL: generate expected filename (via metadata fetch + scene_namer)
   - Skip download if output file already exists in output-dir
   - Only download files that are missing
   - This handles the "Season 4 episode 4,6,7 missing" use case

## Technical Decisions

- `-p` value format: expects string like `"1080"` or `"1080p"` (strip trailing `p` if present)
- yt-dlp format string when `-p` is set:
  `-f bestvideo[height<={height}]+bestaudio/best[height<={height}]`
- Resolution injected into scene_namer calls as authoritative (overrides metadata height)
- `--retry` is NOT a separate mode - it's a modifier flag. Normal flow + skip-if-exists.
- File existence check: `os.path.exists(output_dir / expected_filename)`
- Expected filename generated BEFORE download attempt (reuse existing scene_template logic)

## Scope Boundaries
- INCLUDE: `-p` flag in Python CLI + thuis.sh passthrough + naming + yt-dlp format
- INCLUDE: `--retry` flag with file-exists check before download
- EXCLUDE: Batch rename of already-downloaded files
- EXCLUDE: Database or state file for tracking downloads
- EXCLUDE: Changing scene_namer logic (already supports resolution)
- EXCLUDE: Advanced format selection (e.g., codec priority, HDR)
