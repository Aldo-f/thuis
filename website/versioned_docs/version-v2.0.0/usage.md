---
sidebar_position: 3
---

# Usage (v2.0.0)

## How to Run

Version 2.0.0 of thuis is designed to be run as a Python module. It provides two equivalent ways to execute the program:

### Method 1: Python Module (Recommended)

```bash
python -m thuis.main [OPTIONS] <URL>
```

### Method 2: Wrapper Script

For convenience, a wrapper script is also provided:

```bash
./thuis.sh [OPTIONS] <URL>
```

Both approaches are functionally identical - the wrapper script simply calls `python -m thuis.main` internally.

## Basic Usage

The primary way to use thuis is to provide a VRT MAX content URL:

```bash
python -m thuis.main https://www.vrt.be/vrtmax/a/show/...
```

## Command Line Options

Version 2.0.0 introduced a comprehensive set of command-line options:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show program version and exit |
| `--no-cache` | Disable filesystem cache |
| `--ignore-errors` | Continue on download errors |
| `--max-downloads INTEGER` | Maximum number of files to download |
| `--skip-unavailable-files` | Skip unavailable files |
| `--no-abort-on-error` | Continue with next URL on error |
| `--output DIRECTORY` | Output directory for downloads |
| `--output-template TEMPLATE` | Output filename template |
| `--restrict-filenames` | Restrict filenames to ASCII characters |
| `--no-overwrites` | Do not overwrite existing files |
| `--continue` | Resume partially downloaded files |
| `--no-part` | Do not use .part files |
| `--no-mtime` | Do not use Last-modified header |
| `--write-description` | Write video description to .description file |
| `--write-info-json` | Write video metadata to .info.json file |
| `--write-annotations` | Write annotations to .annotations.xml file |
| `--write-sub` | Write subtitle file |
| `--write-auto-sub` | Write automatic subtitle file |
| `--list-subs` | List available subtitles |
| `--sub-format FORMAT` | Subtitle format (srt, ass, vtt, etc.) |
| `--sub-lang LANGS` | Subtitle languages (comma-separated) |
| `--skip-unavailable-subs` | Skip unavailable subtitles |
| `--auth-stdin` | Read credentials from stdin |
| `--network-timeout SECONDS` | Network timeout in seconds |
| `--socket-timeout SECONDS` | Socket timeout in seconds |
| `--batch-file FILE` | File containing URLs to process |
| `--include-ads` | Include advertisements in download |
| `--include-pretrailers` | Include pretrailers in download |

## Common Use Cases

### Download with Custom Output Directory

```bash
python -m thuis.main --output ./Downloads https://www.vrt.be/vrtmax/a/show/...
```

### Download Best Quality Available

```bash
python -m thuis.main --format best https://www.vrt.be/vrtmax/a/show/...
```

### Download Audio Only

```bash
python -m thuis.main --format "bestaudio" https://www.vrt.be/vrtmax/a/show/...
```

### Download with Specific Video Quality

```bash
python -m thuis.main --format "best[height<=720]" https://www.vrt.be/vrtmax/a/show/...
```

### Download Subtitles

```bash
python -m thuis.main --write-sub --sub-lang nl,en https://www.vrt.be/vrtmax/a/show/...
```

### Download with Metadata

```bash
python -m thuis.main --write-info-json --write-description https://www.vrt.be/vrtmax/a/show/...
```

### Batch Processing from File

Create a file `urls.txt` with one URL per line:

```
https://www.vrt.be/vrtmax/a/show/1/
https://www.vrt.be/vrtmax/a/show/2/
https://www.vrt.be/vrtmax/a/show/3/
```

Then run:

```bash
python -m thuis.main --batch-file urls.txt
```

### Resume Interrupted Downloads

```bash
python -m thuis.main --continue https://www.vrt.be/vrtmax/a/show/...
```

### Disable Certificate Verification (for testing only)

```bash
python -m thuis.main --no-check-certificate https://www.vrt.be/vrtmax/a/show/...
```

## Credentials Handling

Version 2.0.0 introduced secure credentials handling:

### Environment Variables (Recommended)

```bash
export VRT_EMAIL="your-email@example.com"
export VRT_PASSWORD="your-password"
```

### .env File

Create a `.env` file in the project root:

```
VRT_EMAIL=your-email@example.com
VRT_PASSWORD=your-password
```

### Prompt Input

If credentials aren't provided via environment variables or .env file, the program will prompt for them securely.

## Output Files

By default, downloaded files are saved with descriptive names based on the content title. The output directory can be customized with the `--output` option.

## Logging

Logs are written to the `logs/` directory by default. To see logs in the console, use:

```bash
python -m thuis.main --log-level DEBUG https://www.vrt.be/vrtmax/a/show/...
```

Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Important Notes

- This version requires a valid VRT MAX account to access content
- The program will automatically handle token refresh and session management
- Downloaded files are saved as MP4 containers with appropriate video/audio codecs
- Temporary `.part` files are used during downloads and renamed on completion
