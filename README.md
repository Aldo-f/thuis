# thuis -- VRT MAX downloader (proof of concept)

A simple tool to download videos from VRT MAX using yt-dlp. It wraps yt-dlp with the right settings and credentials so you can start downloading with minimal setup.

This is a proof of concept. It works for basic use cases but comes with no guarantees.

## Requirements

- Python 3.8 or newer
- git
- A VRT MAX account (free or paid)

## Installation

Open a terminal and run these commands:

```bash
# Clone the repository
git clone <repository-url> thuis
cd thuis

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

This installs a patched version of yt-dlp that can handle VRT MAX's login flow.

## Usage

You can run the tool in two ways.

### Option 1: Wrapper scripts (easiest)

Linux:

```bash
./thuis.sh https://www.vrt.be/vrtmax/a/show/...
```

Windows:

```cmd
thuis.bat https://www.vrt.be/vrtmax/a/show/...
```

### Option 2: Direct Python

If you prefer calling the Python module directly (or the wrapper scripts are not working):

```bash
python -m thuis.main https://www.vrt.be/vrtmax/a/show/...
```

Or from the project root:

```bash
python src/thuis/main.py https://www.vrt.be/vrtmax/a/show/...
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

### Video resolution profile

```bash
./thuis.sh --profile 720 https://www.vrt.be/vrtmax/a/show/...
```

Limits the video resolution to a specific value (e.g. 720, 1080). The tool selects the best available stream at or below that resolution.

```bash
./thuis.sh -p 1080 https://www.vrt.be/vrtmax/a/show/...
```

The short form `-p` works the same way.

### Retry mode

```bash
./thuis.sh --retry https://www.vrt.be/vrtmax/a/show/...
```

Skips URLs whose output file already exists. Useful for resuming an interrupted batch without re-downloading files that already finished.

### Normalize video filenames

Renames downloaded video files to a scene-compatible format and optionally cleans up leftover files.

```bash
python -m thuis.main normalize /path/to/media --dry-run
python -m thuis.main normalize /path/to/media --cleanup
```

Options:

- `--dry-run` -- Show what would be renamed without making changes.
- `--cleanup` -- Remove duplicate files (with `_1` suffixes) and stale `.part` files.

The `normalize` subcommand runs separately from downloads. Point it at a directory of already-downloaded files.

### Download a full season

Pass a season URL to download every episode in that season:

```bash
# By season number in path
./thuis.sh https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/

# By query parameter
./thuis.sh 'https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/?seizoen=seizoen-2'
```

The tool expands the season URL to individual episode URLs by querying the VRT MAX GraphQL API, falling back to HEAD-request guessing if the API returns no results. Combine with `--dry-run` to preview what would be downloaded:

```bash
./thuis.sh --dry-run 'https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/?seizoen=seizoen-2'
```

Limit the number of episodes processed per season with `--max-episodes`:

```bash
# Download only the first 5 episodes of a season
./thuis.sh --max-episodes 5 https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/
```

### Download all seasons of a show

Pass a bare show URL (without a season number) to automatically discover and download every season:

```bash
./thuis.sh https://www.vrt.be/vrtmax/a-z/thuis
```

The tool queries the show page, detects all available seasons, and expands each into its episodes. Combine with `--dry-run` to preview:

```bash
./thuis.sh --dry-run https://www.vrt.be/vrtmax/a-z/thuis
```

Limit episodes per season with `--max-episodes`:

```bash
# Download at most 10 episodes per season, across all seasons
./thuis.sh --max-episodes 10 https://www.vrt.be/vrtmax/a-z/thuis
```

## Credentials

The tool uses default credentials out of the box. You do not need to set up anything to get started.

If you want to use your own VRT MAX account, set these environment variables:

```bash
export VRT_EMAIL="your-email@example.com"
export VRT_PASSWORD="your-password"
```

You can also add them to a `.env` file in the project root:

```
VRT_EMAIL=your-email@example.com
VRT_PASSWORD=your-password
```

The tool checks environment variables first, then the `.env` file (if python-dotenv is installed), and falls back to the built-in defaults.

## Output

Videos are saved in the `media/` directory by default. Each file is named after the video title. You can change this with `--output-dir`.

Logs are written to `logs/` in date-based files (e.g. `logs/2026-07-07.log`). Use `--log-level` to control verbosity (e.g. `--log-level DEBUG` for detailed output).

To tail the current log in real-time:

```bash
./thuis.sh --follow
# or
./thuis.sh -f
```

## Transcoding to 720p

After downloading, you can transcode videos to a target resolution (e.g. 720p). This is useful for:

- Reducing file size for storage or streaming
- Ensuring consistent resolution across your library
- Upscaling lower-resolution downloads

### Transcode during download

Use `--transcode` to automatically transcode files after download:

```bash
./thuis.sh --transcode 720p https://www.vrt.be/vrtmax/a/z/fc-de-kampioenen/1/
```

Options:

- `--transcode TARGET` - Target resolution (e.g., `720p`, `1080p`). Files already at this resolution are skipped.
- `--allow-upscale` - Allow upscaling lower resolutions (e.g., 540p → 720p).
- `--keep-original` - Keep both original and transcoded files.
- `--transcode-preset PRESET` - FFmpeg preset: `fast` (default), `medium`, `slow`, etc.
- `--transcode-crf CRF` - Quality setting (0-51, lower = better quality, default: 23).

**Smart source selection**: If multiple resolutions exist (e.g., 1080p and 540p), the highest available is used for transcoding (1080p → 720p is preferred over 540p → 720p).

### Batch transcode existing files

Use `--input-dir` to transcode files without downloading:

```bash
# Transcode FC De Kampioenen files to 720p
python -m thuis.main --input-dir /path/to/media/tv/seed/ \
    --transcode 720p \
    --filter "kampioenen" \
    --allow-upscale \
    --keep-original \
    --recursive \
    --parallel 2

# Preview without transcoding
python -m thuis.main --input-dir /path/to/media/tv/seed/ \
    --transcode 720p \
    --filter "kampioenen" \
    --recursive \
    --dry-run
```

Options:

- `--input-dir DIR` - Directory containing video files to transcode.
- `--filter PATTERN` - Filter files by name (substring match, case-insensitive). Can be used multiple times.
- `--recursive` - Scan subdirectories recursively.
- `--parallel N` - Number of concurrent transcoding jobs (default: 2).

### Examples

```bash
# Transcode all downloaded FC De Kampioenen episodes to 720p, keep originals
python -m thuis.main --input-dir ~/media/tv/seed/ \
    --transcode 720p \
    --filter "kampioenen" \
    --allow-upscale \
    --keep-original \
    --recursive

# Transcode a single show with higher quality (CRF 18 = larger file, better quality)
python -m thuis.main --input-dir ~/media/tv/ \
    --transcode 720p \
    --filter "thuis" \
    --transcode-crf 18 \
    --transcode-preset medium

# Batch transcode with dry-run first
python -m thuis.main --input-dir ~/media/ \
    --transcode 720p \
    --recursive \
    --dry-run
```

## Interrupt handling

- Pressing Ctrl + C now exits cleanly with "Interrupted by user" and no traceback.

[Contributing Guidelines](CONTRIBUTING.md)

Website documentation: `website/docs/`

## How it works

The tool finds the patched yt-dlp binary, passes it your VRT MAX URLs along with the right settings (best video + audio, merged to MP4), and lets yt-dlp handle the actual download. It uses your VRT MAX credentials to log in so the videos are accessible.

## Disclaimer

This is a proof of concept. It may break if VRT MAX changes their website or login flow. The default credentials are shared demo credentials. Respect VRT's terms of service.
