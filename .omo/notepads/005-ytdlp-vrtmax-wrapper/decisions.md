# Decisions — 005-ytdlp-vrtmax-wrapper

## 2026-06-24 — Architecture Decisions

- yt-dlp wrapper will be a new `packages/ytdlp-service/` package (not modifying `packages/core` directly)
- The package will export `YtDlpProviderAdapter` that implements the existing `ProviderAdapter` interface
- Existing custom VRT provider is preserved as fallback
- Cookie store integrates with existing credential vault (PBKDF2+AES-256-GCM)
- Download management uses yt-dlp subprocess (SIGSTOP/SIGCONT for pause/resume)
- Provider selection toggle stored in IndexedDB user preferences
