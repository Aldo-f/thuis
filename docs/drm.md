# DRM Protection

VRT MAX uses DRM (Digital Rights Management) on some content. The tool detects this and handles it appropriately.

## How DRM Detection Works

The tool checks the stream URL for specific patterns:

| Stream Type | URL Pattern | Downloadable |
|-------------|-------------|--------------|
| DRM-free | `..._nodrm_...` | Yes |
| Potentially protected | `..._drm_...` | Usually Yes |

## Behavior

### DRM-free Content
- Videos with `_nodrm_` in the URL can be downloaded successfully
- HLS streams are extracted and processed by FFmpeg

### Content with `_drm_` in URL
- VRT has been phasing out DRM - most content now downloads successfully
- If download fails, you'll see an error message

## Note

Most on-demand content on VRT MAX is now DRM-free. The `_drm_` pattern in URLs doesn't always mean download will fail.
