---
sidebar_position: 1
---

# What is thuis?

**thuis** is a proof-of-concept tool for downloading videos from [VRT MAX](https://www.vrt.be/vrtmax/), the Flemish public broadcaster's streaming platform.

It wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) — a powerful video downloader — with the correct settings and VRT MAX credentials so you can start downloading with minimal setup. Behind the scenes, thuis uses a [patched version of yt-dlp](https://github.com/Aldo-f/yt-dlp) that handles VRT MAX's login flow properly.

## Key features

- **Single command** — download a video with one command, no configuration needed
- **Batch downloads** — pass multiple URLs or a file full of them
- **Dry-run mode** — preview what would be downloaded without actually fetching anything
- **Custom output** — choose where your videos are saved
- **Built-in credentials** — works out of the box with default demo credentials

## Limitations

This is a proof of concept. It works for basic use cases but comes with no guarantees. VRT MAX may change their website or login flow at any time, which could break the tool.

Respect VRT's terms of service when using this tool.
