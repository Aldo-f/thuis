# Implementation Plan: yt-dlp VRT MAX Integration

- [x] Plan created

**Branch**: `005-ytdlp-vrtmax-wrapper` | **Date**: 2026-06-24 | **Spec**: specs/005-ytdlp-vrtmax-wrapper/spec.md

**Input**: Feature specification for yt-dlp VRT MAX integration

---

## Summary

Add a yt-dlp wrapper service as an alternative VRT MAX backend in the thuis monorepo. The wrapper provides login (cookie extraction), episode metadata retrieval, HLS stream resolution, and download management — all through the existing `ProviderAdapter` interface. The existing custom VRT API integration is preserved as a fallback.

---

## Technical Context

**Language**: TypeScript 5.6+ (strict mode)

**Primary Dependencies**:
- `yt-dlp` binary (system install, checked at startup)
- `@thuis/core` (existing types, ProviderAdapter interface, credential vault)
- `zod` (output validation)
- `hls.js` (already in web-app for playback)
- Node.js child_process (yt-dlp subprocess management)

**Existing Architecture**:
- `packages/core/src/providers/vrt/VrtProviderAdapter.ts` — existing custom VRT adapter
- `packages/core/src/auth/VrtAuthService.ts` — custom VRT auth (GraphQL)
- `packages/core/src/episode/VrtEpisodeService.ts` — custom episode service
- `packages/core/src/download/StreamResolver.ts` — custom stream resolver
- `packages/core/src/providers/ProviderAdapter.ts` — interface to implement
- `packages/core/src/providers/ProviderRegistry.ts` — registry for adapter lookup
- `packages/web-app/src/pages/EpisodeDetail.tsx` — HLS player page
- `packages/web-app/src/pages/DownloadQueuePage.tsx` — download queue page

**New Package**: `packages/ytdlp-service/` — yt-dlp wrapper service

**Storage**: yt-dlp cookies stored in existing credential vault (encrypted via PBKDF2+AES-256-GCM or Electron safeStorage)

**Testing**: Jest (unit tests with mocked yt-dlp binary), Playwright (component tests)

**Target Platform**: Linux (dev), Electron (desktop), Web (streaming only)

**Constraints**:
- Must follow constitution: Dutch UI, Zod validation, ProviderAdapter pattern
- No `as any` or `@ts-ignore`
- yt-dlp binary is external dependency (not bundled)
- Graceful fallback to existing custom provider when yt-dlp unavailable

---

## Project Structure

```text
packages/ytdlp-service/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts                  # Public exports
│   ├── YtDlpService.ts           # Core yt-dlp subprocess manager
│   ├── YtDlpProviderAdapter.ts   # ProviderAdapter implementation
│   ├── DownloadManager.ts        # Download queue management
│   ├── DownloadJob.ts            # Single download tracking
│   ├── CookieStore.ts            # Cookie vault integration
│   ├── types.ts                  # yt-dlp output types & Zod schemas
│   └── __tests__/
│       ├── YtDlpService.test.ts
│       ├── YtDlpProviderAdapter.test.ts
│       ├── DownloadManager.test.ts
│       └── CookieStore.test.ts
```

---

## Tasks

### Wave 1 — Foundation (parallel where possible)

- [x] **T1**: Create `packages/ytdlp-service/` package scaffold
  - package.json with dependencies (zod, @thuis/core)
  - tsconfig.json extending base
  - Basic index.ts with exports

- [x] **T2**: Implement yt-dlp output type schemas (`types.ts`)
  - Zod schemas for yt-dlp `--dump-json` output (episode, playlist, format info)
  - Zod schemas for `-g` output (stream URL)
  - Export TypeScript types derived from schemas

- [x] **T3**: Implement `YtDlpService` core class
  - `isAvailable()` — check yt-dlp binary exists and version
  - `getVersion()` — return installed yt-dlp version
  - `extractMetadata(url)` — run `yt-dlp --dump-json` and parse output
  - `extractStreamUrl(url)` — run `yt-dlp -g --dump-single-json` and return HLS URL
  - `extractPlaylist(url)` — run `yt-dlp --dump-json --flat-playlist` for series
  - `login(email, password)` — run `yt-dlp --username --password --cookies` to extract cookies
  - Error handling for missing binary, network errors, invalid output

- [x] **T4**: Implement `CookieStore` for yt-dlp cookie vault integration
  - `saveCookies(cookies)` — encrypt and store cookies in credential vault
  - `loadCookies()` — decrypt and return stored cookies
  - `clearCookies()` — remove stored cookies
  - `ensureValidSession()` — check if stored cookies are still valid, re-auth if needed
  - Netscape cookie format conversion for yt-dlp compat

### Wave 2 — Provider Adapter & Download Management (parallel)

- [x] **T5**: Implement `YtDlpProviderAdapter` (implements ProviderAdapter)
  - `init()` — check yt-dlp availability
  - `login(credentials)` — delegate to YtDlpService.login + CookieStore.saveCookies
  - `search(query)` — use YtDlpService.extractMetadata/search
  - `getEpisode(url)` — use YtDlpService.extractMetadata
  - `resolveStream(episode)` — use YtDlpService.extractStreamUrl
  - Register in ProviderRegistry at startup

- [x] **T6**: Implement `DownloadJob`
  - URL, file path, progress state (queued/downloading/paused/completed/failed)
  - Progress tracking (percentage, speed, ETA, bytes downloaded)
  - Pause/resume via yt-dlp signal handling (SIGSTOP/SIGCONT)
  - Cancellation (delete partial file)
  - Event emitter pattern for UI updates

- [x] **T7**: Implement `DownloadManager`
  - Queue management (add, remove, reorder, clear)
  - Concurrent download limit (configurable, default 2)
  - Automatic retry on transient failures (3 attempts)
  - Queue persistence across sessions (IndexedDB on web, JSON file on Electron)
  - Global progress aggregation

### Wave 3 — Front-end Integration (parallel)

- [x] **T8**: Create yt-dlp provider selection UI
  - Toggle in settings/vault to choose between "Custom VRT" and "yt-dlp" provider
  - Show yt-dlp version and availability status
  - Show which provider is currently active
  - Provider option stored in user preferences (IndexedDB)

- [x] **T9**: Update EpisodeDetail page for yt-dlp integration
  - Stream resolution uses selected provider (custom vs yt-dlp)
  - Download button triggers DownloadManager instead of raw stream save
  - Show download progress inline on episode page
  - Handle DRM detection and geographic restrictions from yt-dlp output

- [x] **T10**: Update DownloadQueuePage for yt-dlp download management
  - List all active/completed/failed downloads
  - Show progress bar, speed, ETA for each active download
  - Pause/resume/cancel buttons per download
  - Clear completed and retry failed actions
  - Open downloaded file location button

- [x] **T11**: Add yt-dlp series browsing page
  - Input VRT MAX series URL
  - Display all episodes from yt-dlp playlist output
  - Season filter
  - Episodic thumbnail grid with title, date, duration
  - Bulk download selection

### Wave 4 — Verification & Polish

- [x] **T12**: Unit tests for all yt-dlp service modules
  - YtDlpService: mock child_process.spawn, test all methods
  - CookieStore: test encrypt/decrypt/clear with mock vault
  - DownloadJob: test state transitions, progress calculation
  - DownloadManager: test queue operations, concurrency limits, persistence
  - YtDlpProviderAdapter: test against mocked service

- [x] **T13**: Component tests for yt-dlp UI
  - Provider selection component
  - Download progress component
  - Series browser component
  - Queue management component

- [x] **T14**: Integration test & verification
  - Verify yt-dlp binary detection on the system
  - Verify provider fallback works when yt-dlp is absent
  - Full typecheck (`tsc --noEmit`) across all packages
  - Verify Dutch language compliance in all new UI strings

---

## Final Verification Wave

- **F1**: Code Review — all code follows constitution principles (Zod validation, no `as any`, ProviderAdapter pattern, Dutch UI)
- **F2**: Type Safety — `tsc --noEmit` passes with zero errors across all packages
- **F3**: Tests — All unit and component tests pass (coverage: 80%+ branch coverage for ytdlp-service)
- **F4**: Integration — yt-dlp binary detection, provider fallback, download queue all work correctly end-to-end
