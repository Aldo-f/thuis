---
sidebar_position: 3
---

# Usage

You can run thuis in two ways: using the wrapper script or by calling the Python module directly.

## Wrapper script (easiest)

```bash
./thuis.sh https://www.vrt.be/vrtmax/a/show/...
```

## Direct Python

```bash
python -m thuis.main https://www.vrt.be/vrtmax/a/show/...
```

## Examples

### Download a single video

```bash
./thuis.sh https://www.vrt.be/vrtmax/a/show/...
```

### Download multiple videos at once

```bash
./thuis.sh https://www.vrt.be/vrtmax/a/show/1/ https://www.vrt.be/vrtmax/a/show/2/ https://www.vrt.be/vrtmax/a/show/3/
```

### Download videos from a URL file

Create a text file with one URL per line (blank lines and lines starting with `#` are ignored):

```
# my-list.txt
https://www.vrt.be/vrtmax/a/show/1/
https://www.vrt.be/vrtmax/a/show/2/
```

Then run:

```bash
./thuis.sh --file my-list.txt
```

### Dry run (see what would be downloaded)

```bash
./thuis.sh --dry-run https://www.vrt.be/vrtmax/a/show/...
```

### Custom output directory

```bash
./thuis.sh --output-dir ~/Videos https://www.vrt.be/vrtmax/a/show/...
```

### Download a full season

Pass a season URL to download every episode in that season:

```bash
# By season number in path
./thuis.sh https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/

# By query parameter
./thuis.sh 'https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/?seizoen=seizoen-2'
```

### Download all seasons of a show

Pass a bare show URL (without a season number) to automatically discover and download every season:

```bash
./thuis.sh https://www.vrt.be/vrtmax/a-z/thuis
```

The tool queries the show page, detects all available seasons via the VRT MAX GraphQL API, and expands each into its episodes.

### Limit episodes

Use `--max-episodes` to limit the number of episodes processed per season:

```bash
# Download at most 5 episodes per season
./thuis.sh --max-episodes 5 https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/

# Limit across all seasons (show-level URL)
./thuis.sh --max-episodes 10 https://www.vrt.be/vrtmax/a-z/thuis
```

### Enable console logging

By default, logs are written to `logs/` directory only. Use `--log-level` to see them in the console:

```bash
./thuis.sh --log-level DEBUG https://www.vrt.be/vrtmax/a/show/...
```

### Follow log output

To tail the latest log file in real-time:

```bash
./thuis.sh --follow
```

### Limit video resolution

Use `--profile` (or `-p`) to cap the output resolution. Valid values are 720, 1080, 1440, and 2160:

```bash
./thuis.sh --profile 720 https://www.vrt.be/vrtmax/a/show/...
```

This restricts the best video format to the given height. For example, `--profile 720` downloads 720p max even if higher resolutions are available.

### Retry mode

Use `--retry` to skip downloads where the output file already exists:

```bash
./thuis.sh --retry https://www.vrt.be/vrtmax/a/show/...
```

When set, the tool checks if the destination file is already on disk and skips the download instead of overwriting. This is useful for re-running on a partially completed list without re-downloading existing files.

### Normalize video files

The `normalize` subcommand renames video files in a directory to a consistent scene format:

```bash
thuis normalize /path/to/videos
```

Options:

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would happen without making changes |
| `--cleanup` | Remove duplicates (files with `_1` suffix) and stale `.part` files |

```bash
# Preview changes
thuis normalize --dry-run /path/to/videos

# Normalize and clean up
thuis normalize --cleanup /path/to/videos
```

### Watchlists

Process multiple URLs from a text file with optional scheduling:

```bash
./thuis.sh --watchlist watchlists/Fc_De_Kampioenen.txt --now
```

- `--watchlist FILE`: Path to the watchlist file.
- `--now`: Force run all entries regardless of their schedule or last-run status.

See `AGENTS.md` for full watchlist format and scheduling details.

## Example output

```
$ ./thuis.sh --dry-run https://www.vrt.be/vrtmax/a/show/some-episode
[thuis] Using default credentials (kuxelu@ipdeer.com)
[thuis] Running: .venv/bin/yt-dlp --username o-auth2 --password '***' \
  --format 'bestvideo[height<=?1080]+bestaudio/best[height<=?1080]' \
  --merge-output-format mp4 \
  --print filename \
  --dry-run \
  'https://www.vrt.be/vrtmax/a/show/some-episode'
[thuis] Output: Some Episode (2025-04-07) [some-episode].mp4
```
