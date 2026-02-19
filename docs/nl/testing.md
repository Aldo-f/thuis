# Tests

## Draai Tests

```bash
# Snelle tests (standaard, alleen DRM detectie)
pytest tests/ -v

# Alle tests inclusief downloads (langzaam)
pytest tests/ -v -m ""
```

## Test URLs

| Type | Programma | DRM |
|------|-----------|-----|
| Kort DRM-vrij | Flikken Maastricht trailer | Nee |
| Lang DRM-vrij | Thuis aflevering | Nee |
| DRM beschermd | De camping S1 E1 | Ja |

## Test Details

### DRM Detectie Tests

Deze tests verifiëren dat de tool correct identificeert:
- DRM-vrije content (kan gedownload worden)
- DRM-beschermde content (kan niet gedownload worden)

### Download Tests

Deze tests downloaden daadwerkelijk video's om te verifiëren dat de download functionaliteit werkt.

!!! warning "Download tests zijn langzaam"
    Download tests kunnen enkele minuten duren om te voltooien.
