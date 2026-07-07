# VRT DLP Downloader Spec

## Commands

- `python src/thuis/main.py` (or `python -m thuis.main`): Main CLI entry point.
- `./thuis.sh` (Linux/macOS): Shell wrapper that calls `src/thuis/main.py`.
- `thuis.bat` (Windows): Batch wrapper that calls `src\thuis\main.py`.

## Inputs

- `urls` (positional, one or more strings): VRT MAX URL(s) to download. Accepts multiple URLs separated by spaces.
- `--file FILE` (file path): Path to a file containing URLs, one per line. Blank lines and lines starting with `#` are ignored.
- `--dry-run` (flag): Simulate the download process without actually downloading any files. Prints what would be downloaded.
- `--output-dir OUTPUT_DIR` (directory path): Directory where downloaded files will be saved (default: `media`).

## Outputs

- Video files (`.mp4`) saved in the specified output directory.

## Environment Requirements

- `VRT_EMAIL` (optional): VRT MAX account email. Checked first from environment variable.
- `VRT_PASSWORD` (optional): VRT MAX account password. Checked first from environment variable.
- `.env` file (optional): If `python-dotenv` is installed, a `.env` file in the project root is loaded as a fallback.
- Hardcoded defaults (last fallback): `kuxelu@ipdeer.com` / `Els123456` for demonstration and testing.

Priority order: environment variables > `.env` file > hardcoded defaults.

## Test Strategy

- Unit tests for each module.
- Integration tests with mocked yt-dlp binary.

## Usage Instructions

```bash
# Download a single video
python src/thuis/main.py https://www.vrt.be/vrtmax/a/show/...

# Download multiple videos at once
python src/thuis/main.py https://www.vrt.be/vrtmax/a/show/1/ https://www.vrt.be/vrtmax/a/show/2/

# Download videos from a URL file (one URL per line, # for comments)
python src/thuis/main.py --file my-list.txt

# Dry run (simulate, no download)
python src/thuis/main.py --dry-run https://www.vrt.be/vrtmax/a/show/...

# Custom output directory
python src/thuis/main.py --output-dir ~/Videos https://www.vrt.be/vrtmax/a/show/...

# Using wrapper scripts (recommended)
./thuis.sh https://www.vrt.be/vrtmax/a/show/...
thuis.bat https://www.vrt.be/vrtmax/a/show/...
```
