# Testing

## Run Tests

```bash
# Fast tests (default, DRM detection only)
pytest tests/ -v

# All tests including downloads (slow)
pytest tests/ -v -m ""
```

## Test URLs

| Type | Program | DRM |
|------|---------|-----|
| Short DRM-free | Flikken Maastricht trailer | No |
| Long DRM-free | Thuis episode | No |
| DRM protected | De camping S1 E1 | Yes |

## Test Details

### DRM Detection Tests

These tests verify that the tool correctly identifies:
- DRM-free content (can be downloaded)
- DRM-protected content (cannot be downloaded)

### Download Tests

These tests actually download videos to verify the download functionality works correctly.

!!! warning "Download tests are slow"
    Download tests can take several minutes to complete.
