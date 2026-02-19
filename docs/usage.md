# Usage

## Basic Download

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

## Custom Output

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "my_video.mp4"
```

## Debug Mode

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

## Command Options

| Option | Description |
|--------|-------------|
| `python thuis.py --setup` | Configure credentials |
| `python thuis.py <url>` | Download video |
| `python thuis.py <url> -o <file>` | Download with custom name |
| `python thuis.py <url> --no-headless` | Show browser window |
| `python thuis.py --help` | Show help |

## Output

Videos are automatically saved to the `media/` directory.
