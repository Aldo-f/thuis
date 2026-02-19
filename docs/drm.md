# DRM Protection

VRT MAX uses DRM (Digital Rights Management) on some content. The tool detects this and handles it appropriately.

## How DRM Detection Works

The tool checks the stream URL for specific patterns:

| Stream Type | URL Pattern | Downloadable |
|-------------|-------------|--------------|
| DRM-free | `..._nodrm_...` | Yes |
| DRM-protected | `..._drm_...` | No |

## Behavior

### DRM-free Content
- Videos with `_nodrm_` in the URL can be downloaded successfully
- HLS streams are extracted and processed by FFmpeg

### DRM-protected Content
- Videos with `_drm_` in the URL will fail to download
- The tool will show an error message indicating DRM protection

## Examples

### Downloadable Content
```
URL: https://vod.vrtcdn.be/.../pl-xxx_nodrm_xxx.ism/.m3u8
Result: ✅ Success
```

### Protected Content
```
URL: https://vod.vrtcdn.be/.../pl-xxx_drm_xxx.ism/.m3u8
Result: ❌ Failed - DRM protected
```

## Note

Most on-demand content on VRT MAX is DRM-free. Only some newer series may have DRM protection.
