# DRM Bescherming

VRT MAX gebruikt DRM (Digital Rights Management) op sommige content. De tool detecteert dit en handelt het correct af.

## Hoe DRM Detectie Werkt

De tool controleert de stream URL op specifieke patronen:

| Stream Type | URL Patroon | Downloadbaar |
|-------------|-------------|--------------|
| DRM-vrij | `..._nodrm_...` | Ja |
| Mogelijk beschermd | `..._drm_...` | Meestal Ja |

## Gedrag

### DRM-vrije Content
- Video's met `_nodrm_` in de URL kunnen succesvol gedownload worden
- HLS streams worden geëxtraheerd en verwerkt door FFmpeg

### Content met `_drm_` in URL
- VRT is DRM aan het afbouwen - de meeste content downloadt nu succesvol
- Als download mislukt, zie je een foutmelding

## Opmerking

De meeste on-demand content op VRT MAX is nu DRM-vrij. Het `_drm_` patroon in URL's betekent niet altijd dat downloaden zal mislukken.
