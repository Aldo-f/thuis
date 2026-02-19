# Gebruik

## Basis Download

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/"
```

## Custom Output

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" -o "mijn_video.mp4"
```

## Debug Modus

```bash
python thuis.py "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/" --no-headless
```

## Opties

| Optie | Beschrijving |
|--------|-------------|
| `python thuis.py --setup` | Credentials configureren |
| `python thuis.py <url>` | Video downloaden |
| `python thuis.py <url> -o <bestand>` | Download met custom naam |
| `python thuis.py <url> --no-headless` | Browser venster tonen |
| `python thuis.py --help` | Help tonen |

## Output

Video's worden automatisch opgeslagen in de `media/` map.
