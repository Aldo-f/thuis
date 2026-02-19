# DRM Bescherming

VRT MAX gebruikt DRM (Digital Rights Management) op sommige content. De tool detecteert dit en handelt het correct af.

## Hoe DRM Detectie Werkt

De tool controleert de stream URL op specifieke patronen:

| Stream Type | URL Patroon | Downloadbaar |
|-------------|-------------|--------------|
| DRM-vrij | `..._nodrm_...` | Ja |
| DRM-beschermd | `..._drm_...` | Nee |

## Gedrag

### DRM-vrije Content
- Video's met `_nodrm_` in de URL kunnen succesvol gedownload worden
- HLS streams worden geëxtraheerd en verwerkt door FFmpeg

### DRM-beschermde Content
- Video's met `_drm_` in de URL zullen niet downloaden
- De tool toont een foutmelding die DRM bescherming aangeeft

## Voorbeelden

### Downloadbare Content
```
URL: https://vod.vrtcdn.be/.../pl-xxx_nodrm_xxx.ism/.m3u8
Resultaat: ✅ Succes
```

### Beschermde Content
```
URL: https://vod.vrtcdn.be/.../pl-xxx_drm_xxx.ism/.m3u8
Resultaat: ❌ Mislukt - DRM beschermd
```

## Opmerking

De meeste on-demand content op VRT MAX is DRM-vrij. Alleen sommige nieuwere series kunnen DRM bescherming hebben.
