---
sidebar_position: 4
---

# Credentials (v1.0.0)

## No Authentication Required

**Version 1.0.0 of thuis does not require any credentials or authentication.**

This version was designed as a simple utility for processing .mpd (Media Presentation Description) links directly, without integration with any streaming service or login system.

## Why No Credentials?

In v1.0.0:
- The tool accepts .mpd links as direct input
- No communication with VRT MAX or any other streaming platform occurs
- All processing is done locally using the provided .mpd manifest
- No user accounts, API keys, or authentication tokens are involved

## Comparison with Later Versions

Starting with v2.0.0, thuis added VRT MAX integration which requires credentials. However, in v1.0.0:
- ✅ No email or password required
- ✅ No environment variables needed
- ✅ No .env file usage
- ✅ No login flow handling
- ✅ Works with any publicly accessible .mpd link

## Usage Without Credentials

Simply provide an .mpd link to the tool:
```bash
.\thuis.ps1 "https://example.com/content.mpd"
```

The tool will process the manifest and initiate the download based on the information contained within the .mpd file itself.

## Security Note

Since no credentials are used or stored, there are no credential-related security concerns with this version. The tool only processes the URLs and manifests you provide to it.
