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
./thuis.sh -S ~/Videos https://www.vrt.be/vrtmax/a/show/...
```

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
