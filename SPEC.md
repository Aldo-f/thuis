# SPEC: Thuis-V2 – Multi-Provider Content Platform

**Version**: 0.3.0
**Status**: Draft
**Author**: Aldo Fieuw

---

## 0. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | — | Initial draft: VRT MAX Content Monitor |
| 0.2.0 | 2026-06-22 | Full Thuis web downloader spec + Multi-provider platform + Video viewer specs |
| 0.3.0 | 2026-06-22 | Build matrix (APK/EXE/AppImage/DMG), master password vault, offline mode, mobile architecture, cross-provider dedup, all gaps filled |

---

## 1. Project Overview

Thuis is a unified platform for watching and downloading video content from Belgian TV providers (VRT MAX, VTM GO, Play.TV) — one interface, one credential vault, all your shows.

| Build | Platform | Tech Stack | Distribution |
|-------|----------|------------|--------------|
| **Web App** | Browser (Chrome, Firefox, Safari, Edge) | Vite + React 19 + HLS.js + Tailwind 4 | Self-hosted at `https://thuis.aldof.duckdns.org` |
| **Documentation** | Browser | Docusaurus | GitHub Pages (`https://aldof.github.io/thuis`) |
| **Electron Desktop** | Windows, Linux, macOS | Electron 31 + Vite + React (same web UI) + FFmpeg + `safeStorage` | GitHub Releases: `.exe` (NSIS), `.deb`, `.rpm`, `.AppImage`, `.dmg` |
| **Core Library** | All (shared) | Pure TypeScript + Zod + Zustand | pnpm workspace (`@thuis/core`) — not distributed standalone |
| **CI/CD** | — | GitHub Actions | Lint → Test → Build → Deploy (web: duckdns, docs: gh-pages, electron: releases) |

---

## 2. Domain & Scope

**Primary Domain**: `CONTENT-DOWNLOAD` – authenticating, browsing, viewing, and downloading video-on-demand content from Belgian media providers.

**Boundaries**
- **In Scope**: VRT MAX authentication (email/password), GraphQL metadata queries, HLS stream resolution, FFmpeg download, episode browser UI, download queue management, multi-provider credential management (VTM, Play.TV), in-app video player.
- **Out of Scope**: VRT-API backend logic, GitHub Pages infrastructure, OS-level distribution, DRM circumvention (DRM-protected content is detected and reported, not decrypted), third-party provider API reverse-engineering beyond documented endpoints.

---

## 3. Architectural Vision

- **Monorepo (pnpm Workspaces)**: Code organized into `packages/*` for maximum reuse.
- **Single Point of Truth**: The `core` package is the only source of data fetching and business logic.
- **Strict Type Safety**: All I/O validated via Zod schemas.
- **State Isolation**: Shared Zustand state layer used across both Electron and Web.
- **Provider Plugin Architecture**: Each video provider (VRT, VTM, Play.TV) implements a common `ProviderAdapter` interface, enabling uniform search, metadata, and download across all sources.
- **Secure Credential Storage**: Provider credentials stored encrypted (Electron: OS keychain; Web: `crypto.subtle` + session-only memory, never localStorage).
- **TDD / Spec-First**: Architecture defined in `SPEC.md` and `.specify/` before implementation.

---

## 4. Technology Stack

| Layer | Web | Electron (Win/Lin/Mac) |
|-------|------|----------------------|
| **Deployment** | `https://thuis.aldof.duckdns.org` (self-hosted) | GitHub Releases |
| **UI Framework** | React 19 + Tailwind 4 | Same as web |
| **Runtime** | Browser (V8/SpiderMonkey) | Node.js 20 + Chromium |
| **State** | Zustand 4.5 | Zustand 4.5 |
| **Validation** | Zod 3.23 | Zod 3.23 |
| **API clients** | `@thuis/core` (`fetch`) | `@thuis/core` (`fetch`/`node:http`) |
| **HLS Playback** | HLS.js | HLS.js |
| **Download Engine** | HLS stream capture via MediaRecorder (fallback) or copy HLS URL | FFmpeg `child_process.spawn` |
| **Credential Storage** | `crypto.subtle` + IndexedDB (master password required) | Electron `safeStorage` (OS keychain) or master password mode |
| **Packaging** | Vite + Docker / reverse proxy (nginx) | electron-builder 24 (NSIS/deb/rpm/AppImage/dmg) |
| **Auto-update** | N/A (SPA, loads fresh) | `electron-updater` + GitHub Releases |
| **Testing** | Jest + Playwright | Jest + Playwright |
| **CI/CD** | GitHub Actions → rsync/deploy to duckdns VPS | GitHub Actions → GitHub Release |

---

## 5. Feature Highlights

| Feature | Priority | Platforms | Description |
|---------|----------|-----------|-------------|
| **VRT MAX Auth** | P0 | Web, Electron | Email/password login with automatic token refresh |
| **VRT Episode Browser** | P0 | Web, Electron | Browse seasons and episodes with metadata |
| **Stream Resolution** | P0 | Web, Electron | Resolve HLS manifest URLs from episode IDs |
| **Download Engine** | **P0** | Electron | FFmpeg `child_process.spawn` — download HLS streams as MP4 files |
| **Download Queue** | **P0** | Web, Electron | Persistent queue with progress, pause/resume, cross-session persistence |
| **In-App Video Player** | **P1** | Web, Electron | HLS.js — watch directly without downloading. Play/pause/seek/fullscreen |
| **Secure Credential Vault** | P0 | Web, Electron | One master password protects all provider credentials; OS keychain on Electron |
| **Master Password Setup** | P0 | Web, Electron | First-run flow: create master password with recovery warning |
| **Multi-Provider Support** | **P2** | Web, Electron | VTM GO, Play.TV integration via adapter interface |
| **Cross-Provider Search** | P2 | Web, Electron | Unified search across all configured providers |
| **Auto-Next Episode** | P2 | Web, Electron | Seamless binge-watching: next episode loads automatically |
| **Offline Cache** | P2 | Web, Electron | Metadata + search history cached for offline browsing |
| **Web Player Download** | P1 | Web | Download via server proxy or HLS stream capture (Electron has native FFmpeg) |
| **Responsive UI** | P1 | Web, Electron | Tailwind 4 mobile-first design (Electron reuses web UI) |
| **Documentation Site** | P1 | GitHub Pages | Docusaurus site at `https://aldof.github.io/thuis` |

---

## 6. Data Model

### 6.1 Episode

```ts
const EpisodeSchema = z.object({
  id: z.string(),                              // Provider-internal ID
  title: z.string(),                           // Episode title (e.g. "Aflevering 105")
  seriesTitle: z.string(),                     // Series/program name (e.g. "Thuis")
  season: z.number(),                          // Season number
  episode: z.number(),                         // Episode number within season
  episodeCode: z.string(),                     // URL slug (e.g. "thuis-s31a105")
  duration: z.string(),                        // ISO 8601 duration (e.g. "PT30M")
  durationSeconds: z.number().optional(),      // Duration in seconds
  imageUrl: z.string().url().optional(),       // Thumbnail/poster URL
  url: z.string().url(),                       // VRT MAX episode page URL
  description: z.string().optional(),          // Episode description
  available: z.boolean().optional(),           // Currently available for streaming
  videoId: z.string().optional(),              // Stream asset identifier
  provider: z.string(),                        // Provider key: 'vrt' | 'vtm' | 'playtv'
  airedAt: z.string().datetime().optional(),   // Broadcast date/time
  brand: z.string().optional(),                // Channel: 'een', 'ketnet', 'canvas', 'vrt1'
});

type Episode = z.infer<typeof EpisodeSchema>;
```

### 6.2 Episode Detail (extended)

```ts
const EpisodeDetailSchema = EpisodeSchema.extend({
  streamId: z.string(),                        // Vualto media ID (e.g. "pbs-pub-...$vid-...")
  manifestUrl: z.string().url().optional(),    // Resolved HLS manifest URL
  downloadUrl: z.string().url().optional(),    // Direct download fallback
  seasonEpisodes: z.number().optional(),       // Total episodes in season
  nextEpisode: z.object({
    id: z.string(), title: z.string(),
  }).optional(),
  previousEpisode: z.object({
    id: z.string(), title: z.string(),
  }).optional(),
  drm: z.boolean().optional().default(false),  // Whether DRM-protected
  geoRestricted: z.boolean().optional(),       // Whether geo-blocked
});

type EpisodeDetail = z.infer<typeof EpisodeDetailSchema>;
```

### 6.3 Stream Data

```ts
const StreamDataSchema = z.object({
  title: z.string(),
  duration: z.number(),                         // Milliseconds
  drm: z.boolean(),
  posterImageUrl: z.string().url().optional(),
  targetUrls: z.array(z.object({
    type: z.enum(['hls', 'hls_aes', 'mp4', 'mpeg_dash', 'hds', 'hss']),
    url: z.string().url(),
    quality: z.string().optional(),              // e.g. "hd", "sd"
  })),
  subtitles: z.array(z.object({
    url: z.string().url(),
    language: z.string().default('nl'),
    format: z.string().default('vtt'),
  })).optional(),
  code: z.string().optional(),                   // Error code if failed
});

type StreamData = z.infer<typeof StreamDataSchema>;
```

### 6.4 Download Job

```ts
const DownloadStatusSchema = z.enum([
  'pending', 'downloading', 'paused', 'completed', 'failed', 'cancelled',
]);

const DownloadJobSchema = z.object({
  id: z.string(),
  episodeId: z.string(),
  episodeTitle: z.string(),
  seriesTitle: z.string().optional(),
  season: z.number().optional(),
  episode: z.number().optional(),
  streamId: z.string(),
  status: DownloadStatusSchema,
  progress: z.number().min(0).max(100).default(0),
  speed: z.string().optional(),                  // e.g. "2.5 MB/s"
  eta: z.string().optional(),                    // e.g. "1m 30s"
  error: z.string().optional(),
  outputPath: z.string().optional(),
  outputFilename: z.string().optional(),
  createdAt: z.string().datetime(),
  completedAt: z.string().datetime().optional(),
  fileSize: z.number().optional(),               // Bytes
  provider: z.string(),                          // 'vrt' | 'vtm' | 'playtv'
});

type DownloadJob = z.infer<typeof DownloadJobSchema>;
```

### 6.5 Provider Credentials (Vault)

```ts
const ProviderTypeSchema = z.enum(['vrt', 'vtm', 'playtv']);

const ProviderCredentialsSchema = z.object({
  provider: ProviderTypeSchema,
  email: z.string().email(),
  password: z.string(),                          // Stored encrypted at rest
  label: z.string().optional(),                  // User-friendly name (e.g. "Mijn VRT-account")
  isActive: z.boolean().default(true),
  lastVerified: z.string().datetime().optional(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

type ProviderCredentials = z.infer<typeof ProviderCredentialsSchema>;
```

### 6.6 Search Result

```ts
const SearchResultSchema = z.object({
  query: z.string(),
  episodes: z.array(EpisodeSchema),
  total: z.number(),
  hasMore: z.boolean(),
  cursor: z.string().optional(),
  provider: z.string(),                          // 'all' for cross-provider
});

type SearchResult = z.infer<typeof SearchResultSchema>;
```

---

## 7. VRT MAX Authentication & Download Flow

### 7.1 Authentication Protocol (OIDC-based)

VRT MAX uses OpenID Connect (OIDC) with cookie-based token delivery. The flow consists of 4 stages:

```
┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌────────────┐
│  Client  │     │  SSO Login   │     │  Login API  │     │ Token      │
│          │     │  vrt.be/sso  │     │  login.vrt  │     │ Redirect   │
└────┬─────┘     └──────┬───────┘     └──────┬──────┘     └─────┬──────┘
     │                  │                     │                  │
     │  GET /sso/login  │                     │                  │
     │─────────────────►│                     │                  │
     │◄── Set-Cookie ───│                     │                  │
     │  SESSION         │                     │                  │
     │  OIDCXSRF        │                     │                  │
     │                  │                     │                  │
     │  POST /perform_login                   │                  │
     │  Oidcxsrf header  │───────────────────►│                  │
     │  {loginID, pass}  │                     │                  │
     │◄── 403 OK ───────│────────────────────│                  │
     │  {redirectUrl}    │                     │                  │
     │                  │                     │                  │
     │  GET <redirect>   │                     │                  │
     │─────────────────────────────────────────│────────────────►│
     │◄── Set-Cookie ───│─────────────────────│────────────────│
     │  _at (access)    │                     │                  │
     │  _vt (video)     │                     │                  │
     │  _rt (refresh)   │                     │                  │
```

**Stage 1 — Session Initiation**
```
GET https://www.vrt.be/vrtmax/sso/login
```
Response: 302 redirect with `Set-Cookie` for `SESSION` + `OIDCXSRF` (domain: `.login.vrt.be`).

**Stage 2 — Credential Submission**
```
POST https://login.vrt.be/perform_login
Headers:
  Content-Type: application/json
  Oidcxsrf: <OIDCXSRF cookie value>
Body: {
  "clientId": "vrtnu-site",
  "loginID": "<email>",
  "password": "<password>"
}
```
Response: HTTP 403 (expected, not error) with JSON:
```json
{ "redirectUrl": "https://www.vrt.be/vrtmax/sso/callback?code=...", "errorCode": 0 }
```
On failure: `{ "errorCode": "...", "errorMessage": "..." }`

**Stage 3 — Token Extraction**
```
GET <redirectUrl from Stage 2>
```
Response: Sets 3 JWT cookies:
| Cookie | Domain | Path | Purpose |
|--------|--------|------|---------|
| `vrtnu-site_profile_at` | `.www.vrt.be` | `/` | Access token (Bearer auth for GraphQL) |
| `vrtnu-site_profile_vt` | `.www.vrt.be` | `/` | Video token (identity token for player) |
| `vrtnu-site_profile_rt` | `.www.vrt.be` | `/vrtmax/sso` | Refresh token |

**Stage 4 — Token Refresh**
```
GET https://www.vrt.be/vrtmax/sso/refresh
Cookie: vrtnu-site_profile_rt=<refresh_token>
```
Response: Refreshes all 3 cookies. Returns 401 if refresh token expired.

### 7.2 Episode Metadata (GraphQL)

```
POST https://www.vrt.be/vrtnu-api/graphql/v1
Headers:
  Authorization: Bearer <access_token>
  Content-Type: application/json
  x-vrt-client-name: WEB
  x-vrt-client-version: 1.5.9
  x-vrt-zone: default
Body: {
  "operationName": "VideoPage",
  "query": "query VideoPage($pageId: ID!) {
    page(id: $pageId) {
      ... on EpisodePage {
        episode {
          ageRaw description durationRaw episodeNumberRaw id name onTimeRaw
          program { title }
          season { id titleRaw }
          title brand
        }
        ldjson
        player {
          image { templateUrl }
          modes { streamId }
          drm
        }
      }
    }
  }",
  "variables": { "pageId": "/vrtmax/a-z/thuis/31/thuis-s31a6105/" }
}
```

**Fallback**: If no access token, use `https://www.vrt.be/vrtnu-api/graphql/public/v1` (omit `Authorization` header, keep `x-vrt-client-*`).

### 7.3 Player Token & Stream Resolution

**Step A — Get Player Token**
```
POST https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens
Headers: { Content-Type: application/json }
Body: {
  "identityToken": "<video_token (vrtnu-site_profile_vt)>",
  "playerInfo": "<JWT>"
}
```
Response: `{ "vrtPlayerToken": "b1@..." }`

The `playerInfo` JWT is signed with a known HMAC-SHA256 key:
```typescript
const JWT_KEY_ID = '0-0Fp51UZykfaiCJrfTE3+oMI8zvDteYfPtR+2n1R+z8w=';
const JWT_SIGNING_KEY = 'b5f500d55cb44715107249ccd8a5c0136cfb2788dbb71b90a4f142423bacaf38';
const PLAYER_INFO = {
  platform: 'desktop',
  app: { type: 'browser', name: 'Chrome' },
  device: 'undefined (undefined)',
  os: { name: 'Windows', version: '10' },
  player: { name: 'VRT web player', version: '5.1.1-prod-2025-02-14T08:44:16' },
  exp: <now + 900 seconds>,
};
```

**Step B — Get Stream Manifest**
```
GET https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/videos/<video_id>?client=vrtnu-web@PROD&vrtPlayerToken=<player_token>
```
(Likely redirects to `/media-aggregator/v2/media-items/<id>?...`)
Response: `StreamData` with `targetUrls` containing HLS URLs.

**Error codes**: `CONTENT_REQUIRES_AUTHENTICATION`, `CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS`, `CONTENT_IS_AGE_RESTRICTED`, `CONTENT_UNAVAILABLE_VIA_PROXY`.

### 7.4 Download

For Electron: spawn FFmpeg subprocess:
```bash
ffmpeg -i "<hls_url>" \
  -headers "User-Agent: <ua>\r\nReferer: https://www.vrt.be/\r\n" \
  -c copy -y output.mp4
```

For Web App: the download must go through a proxy/server or Electron main process, since browsers cannot spawn FFmpeg. Options:
1. **Server proxy**: Download via a backend server that runs FFmpeg
2. **Electron main process**: Download via Node.js child_process in Electron's main thread, stream results to renderer
3. **Direct HLS.js stream capture**: Use `MediaRecorder` API to capture the video element's output (lossy, slow, not recommended)

---

## 8. Provider Adapter Architecture (Future — P2)

### 8.1 Common Interface

```typescript
interface ProviderAdapter {
  readonly id: string;           // 'vrt' | 'vtm' | 'playtv'
  readonly displayName: string;  // 'VRT MAX' | 'VTM GO' | 'Play.TV'
  readonly supportsSearch: boolean;
  readonly supportsAuth: boolean;

  // Authentication
  login(credentials: ProviderCredentials): Promise<ProviderTokens>;
  refreshTokens(): Promise<ProviderTokens>;
  isLoggedIn(): boolean;

  // Content discovery
  search(query: string, options?: SearchOptions): Promise<SearchResult>;
  getEpisode(url: string): Promise<EpisodeDetail>;
  getSeason(series: string, season: number): Promise<Episode[]>;

  // Stream resolution
  resolveStream(episode: EpisodeDetail): Promise<StreamData>;

  // Lifecycle
  dispose(): void;
}
```

### 8.2 Provider Registry

```typescript
class ProviderRegistry {
  register(adapter: ProviderAdapter): void;
  getProvider(id: string): ProviderAdapter;
  getAllProviders(): ProviderAdapter[];
  getActiveProviders(): ProviderAdapter[];
}
```

### 8.3 VTM GO — Integration Points (Future)

VTM GO (`https://vtm.be/vtmgo`) serves Flemish commercial TV content (VTM, VTM 2, VTM 3, VTM 4, VTM GOLD). Integration requires:

1. **Login**: VTM GO uses its own authentication system (likely OIDC or SAML-based). Credential endpoint discovery needed.
2. **API**: Unknown — needs reverse engineering from network traffic. Likely a REST JSON API.
3. **Streaming**: HLS with Widevine DRM. DRM-free content availability unknown.
4. **Content**: Episodes, movies, live TV from DPG Media brands.

### 8.4 Play.TV — Integration Points (Future)

Play.TV (`https://www.play.tv`) serves content from SBS Belgium (Play4, Play5, Play6, Play7, Play Crime). Integration requires:

1. **Login**: Play.TV uses its own auth system. Registration-based access.
2. **API**: Unknown — needs reverse engineering.
3. **Streaming**: HLS with possible DRM.
4. **Content**: SBS Belgium programs.

---

## 9. Secure Credential Vault

### 9.1 Principles

| Principle | Rule |
|-----------|------|
| **One master password to rule them all** | A single master password unlocks ALL stored provider credentials. No master password = no access. Non-negotiable. |
| **Never plaintext** | Provider passwords never stored in plaintext in any persistent layer (disk, IndexedDB, localStorage, logs). |
| **No recovery** | If the master password is forgotten, ALL stored credentials are unrecoverable. This is clearly communicated during setup. |
| **In-memory only** | Decrypted credentials exist in process memory only. Never written to disk, never serialized, never in swap. |
| **Auto-lock** | Vault auto-locks after configurable inactivity (default: 5 minutes). Re-decryption requires master password re-entry. |
| **OS keychain as alternative** | On Electron, `safeStorage` replaces the master password — OS handles encryption. Master password mode is still available as a user choice. |
| **Per-platform storage** | Web: `crypto.subtle` + IndexedDB. Electron: `safeStorage` (OS keychain) or `crypto.subtle`. |

### 9.2 First-Time Setup Flow

```
┌────────────────────────────────────────────────────────────┐
│                 First Run — Vault Setup                      │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  1. App launches → no vault key exists                       │
│  2. Show setup screen:                                       │
│     ┌──────────────────────────────────────┐                │
│     │  Maak een hoofdwachtwoord aan        │                │
│     │                                      │                │
│     │  [Hoofdwachtwoord    **********    ] │                │
│     │  [Herhaal wachtwoord **********    ] │                │
│     │                                      │                │
│     │  ⚠ BELANGRIJK: Dit wachtwoord kan   │                │
│     │    niet worden hersteld. Verlies je  │                │
│     │    het, dan ben je al je opgeslagen  │                │
│     │    inloggegevens kwijt.              │                │
│     │                                      │                │
│     │  ┌────────────────────────────┐      │                │
│     │  │  Vault aanmaken          │      │                │
│     │  └────────────────────────────┘      │                │
│     └──────────────────────────────────────┘                │
│                                                              │
│  3. On submit:                                               │
│     a. Validate: min 8 chars, passwords match               │
│     b. Generate random 16-byte salt                          │
│     c. Derive key: PBKDF2(password, salt, 600k iters, SHA-256) │
│     d. Encrypt empty credential list with AES-256-GCM        │
│     e. Store: { salt, iterations: 600000, encryptedData }    │
│        in IndexedDB (Web) or Keystore (Android)              │
│     f. Store key material in memory for session              │
│     g. Vault is now UNLOCKED                                 │
│                                                              │
│  4. User is redirected to "Voeg provider toe" screen         │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### 9.3 Encryption Scheme (Master Password)

All platforms that use a master password follow this scheme:

```typescript
// === ENCRYPT ===
// Input: masterPassword (string), plaintext (JSON string of credentials)
// Output: { salt: Uint8Array, iv: Uint8Array, iterations: number, ciphertext: ArrayBuffer }

const salt = crypto.getRandomValues(new Uint8Array(16));
const iv = crypto.getRandomValues(new Uint8Array(12));
const iterations = 600_000;

const keyMaterial = await crypto.subtle.importKey(
  'raw', new TextEncoder().encode(masterPassword), 'PBKDF2', false, ['deriveKey']
);

const key = await crypto.subtle.deriveKey(
  { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
  keyMaterial,
  { name: 'AES-GCM', length: 256 },
  false,
  ['encrypt', 'decrypt']
);

const ciphertext = await crypto.subtle.encrypt(
  { name: 'AES-GCM', iv }, key, new TextEncoder().encode(plaintext)
);

// === VERIFY (on unlock) ===
// Re-derive key from password + stored salt.
// Decrypt. If decryption throws (bad tag / MAC mismatch) → wrong password.
// No timing-safe comparison needed — AES-GCM authentication catches it.

// === RE-ENCRYPT (on password change) ===
// 1. Unlock vault with old password (prove ownership)
// 2. Decrypt all credentials
// 3. Generate new salt + iv
// 4. Re-encrypt with new password-derived key
// 5. Store new { salt, iv, ciphertext } — OLD DATA IS UNREADABLE
```

### 9.4 Electron Specifics

Electron supports two modes, user-selectable:

| Mode | How It Works | When to Use |
|------|-------------|-------------|
| **OS Keychain** (default) | `safeStorage.encryptString()` / `decryptString()` — OS manages encryption. No master password needed. Vault is unlocked while app runs. | Desktop users who want convenience. Safe against disk theft (keychain is OS-protected). |
| **Master Password** | Same `crypto.subtle` scheme as Web. User must enter password each session. | Users who want an extra layer of security or share their computer. |

```typescript
// OS Keychain mode — no master password
const encrypted = safeStorage.encryptString(JSON.stringify(allCredentials));
// Store encrypted blob in app.getPath('userData') + '/vault.json'

const decrypted = safeStorage.decryptString(encrypted);
const credentials = JSON.parse(decrypted);
```

### 9.5 Vault API

```typescript
interface IVault {
  // Lifecycle
  isInitialized(): Promise<boolean>;
  isLocked(): Promise<boolean>;
  isUnlocked(): Promise<boolean>;

  // Setup
  createMasterPassword(password: string): Promise<void>;    // First-time setup
  changeMasterPassword(oldPassword: string, newPassword: string): Promise<void>;

  // Lock/unlock
  unlock(password: string): Promise<void>;                   // Decrypt + hold key in memory
  lock(): Promise<void>;                                      // Purge key from memory
  autoLockTimer: number;                                      // Seconds until auto-lock (default 300)

  // Credential operations (require unlocked vault)
  addCredentials(provider: string, email: string, password: string): Promise<void>;
  getCredentials(provider: string): Promise<{ email: string; password: string } | null>;
  removeCredentials(provider: string): Promise<void>;
  listProviders(): Promise<Array<{ provider: string; email: string }>>;  // NEVER exposes passwords
  verifyCredentials(provider: string): Promise<boolean>;    // Tests login with stored creds

  // Security
  getPasswordStrength(): Promise<'weak' | 'medium' | 'strong'>;
  getLastUnlockedAt(): Promise<Date | null>;
}
```

### 9.6 Password Change Flow

```
1. User enters OLD master password → vault unlocks
2. Decrypt all credentials with old key
3. User enters NEW master password (×2 confirmation)
4. Generate new salt + iv
5. Derive new key from new password
6. Re-encrypt all credentials with new key
7. Store new encrypted blob, discard old blob
8. OLD MASTER PASSWORD IS NOW PERMANENTLY INVALID
```

### 9.7 Master Password Reset (DESTRUCTIVE)

Since credentials are encrypted with a key derived from the master password, and AES-256-GCM provides no backdoor:

> **If the master password is forgotten, there is no recovery. All stored credentials are permanently lost.**

The app provides a **destructive reset** option:

```
1. User confirms: "Ik begrijp dat al mijn opgeslagen inloggegevens verloren gaan."
2. App deletes the encrypted blob from storage
3. App redirects to first-time setup (create new master password)
4. User must re-enter all provider credentials manually
```

This is clearly communicated during both setup and reset.

### 9.8 Credential Verification

The vault can verify stored credentials by actually attempting a login with each provider:

```typescript
// Called periodically (every 7 days) or manually
async verifyAllCredentials(): Promise<Array<{
  provider: string;
  valid: boolean;
  error?: string;
}>> {
  const providers = await this.listProviders();
  const results = [];
  for (const p of providers) {
    const creds = await this.getCredentials(p.provider);
    try {
      const adapter = ProviderRegistry.getProvider(p.provider);
      await adapter.login(creds!);
      results.push({ provider: p.provider, valid: true });
    } catch (e) {
      results.push({ provider: p.provider, valid: false, error: e.message });
    }
  }
  return results;
}
```

---

## 10. In-App Video Player (Future — P2)

### 10.1 Player Features

| Feature | Description |
|---------|-------------|
| **HLS playback** | HLS.js-based adaptive bitrate streaming |
| **Play/Pause/Seek** | Standard media controls |
| **Time scrubber** | Visual timeline with thumbnail previews |
| **Volume control** | Slider + mute toggle |
| **Fullscreen** | Browser fullscreen API |
| **PiP** | Picture-in-Picture for desktop |
| **Playback speed** | 0.5x–2x range |
| **Keyboard shortcuts** | Space (play), F (fullscreen), M (mute), arrows (seek) |
| **Download button** | Triggers download queue for current episode |
| **Episode info overlay** | Title, description, season/episode number |
| **Auto-next** | Auto-load next episode when current ends |
| **Responsive** | Works on desktop and mobile viewports |

### 10.2 Player UI (Wireframe)

```
┌─────────────────────────────────────────────────────┐
│  ◀  Series Title  •  S1 E105  •  Aflevering 105     │
│─────────────────────────────────────────────────────│
│                                                       │
│                                                       │
│                    VIDEO AREA                          │
│                                                       │
│                                                       │
│  ███████████████░░░░░░░░░░  12:30 / 30:00            │
│  🔊 ────●─────  [⛶]  [⬇]  [▶║]                     │
│─────────────────────────────────────────────────────│
│  Description: Marie stelt aan Thuis een nieuwe       │
│  collega voor...                                      │
│                                                       │
│  Next Episode: Aflevering 106  [▶ Play Next]         │
└─────────────────────────────────────────────────────┘
```

### 10.3 Player Architecture (Web)

```typescript
// packages/web-app/src/components/player/
// VideoPlayer.tsx — Main player component
// HlsPlayer.tsx — HLS.js wrapper with React bindings
// PlayerControls.tsx — Play/pause/seek/volume/fullscreen
// PlayerTimeline.tsx — Visual seek bar with thumbnails
// DownloadButton.tsx — Triggers download flow
// EpisodeInfo.tsx — Metadata overlay

// Stream flow:
// 1. User clicks episode → EpisodePage loads
// 2. resolveStream(streamId) → StreamData with HLS URL
// 3. HLS.js loads manifest → adaptive playback
// 4. Download button → adds to DownloadQueue
// 5. Electron: DownloadQueue → FFmpeg subprocess
```

---

## 11. Build Platform Architecture

### 11.1 Web App (`packages/web-app`)

**Type**: SPA, served from GitHub Pages
**Entry**: `index.html` → Vite bundle → React 19
**Key differences from desktop**:
- No FFmpeg — download is replaced with "Copy HLS URL" or "Open in VLC" instruction
- No OS keychain — vault uses `crypto.subtle` + IndexedDB with mandatory master password
- HLS.js for playback (no native video component)
- Session-bound: refresh token in IndexedDB (encrypted by master password)
- Auto-update: unnecessary (SPA loads fresh on each visit)
- PWA manifest + service worker for offline cache and "install to homescreen"

### 11.2 Electron Desktop (`packages/electron-app`)

**Type**: Desktop app for Windows, Linux, macOS
**Architecture**: Main process (Node.js) + Renderer (web UI) + Preload bridge

| Component | Responsibility |
|-----------|---------------|
| **Main process** | FFmpeg child_process, file system access, safeStorage, auto-updater, system tray, OS notifications |
| **Renderer** | Identical React app as web-app (shared components) |
| **Preload** | `contextBridge.exposeInMainWorld('electronAPI', ...)` — typed IPC surface |

**Build outputs** (via `electron-builder`):

| Platform | Format | electron-builder target |
|----------|--------|------------------------|
| Windows | `.exe` (NSIS installer), `.exe` (portable) | `nsis`, `portable` |
| Linux | `.deb`, `.rpm`, `.AppImage` | `deb`, `rpm`, `AppImage` |
| macOS | `.dmg`, `.zip` | `dmg`, `zip` |

**CI matrix**:
```yaml
# .github/workflows/build.yml (conceptual)
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    arch: [x64]
  include:
    - os: ubuntu-latest
      targets: [deb, rpm, AppImage]
    - os: windows-latest
      targets: [nsis]
    - os: macos-latest
      targets: [dmg]
```

### 11.3 Android Mobile (`packages/mobile-app`) — POSTPONED

**Type**: React Native app, shares `@thuis/core` TypeScript with web/electron
**Status**: Design documented for future reference. Not in scope for initial release.
**Architecture**:

```
packages/mobile-app/
├── android/                    # Native Android project (Gradle)
├── ios/                        # iOS stub (not active target)
├── src/
│   ├── App.tsx                 # Root: navigation, theming
│   ├── navigation/
│   │   ├── RootNavigator.tsx   # Bottom tab navigator (Home, Search, Downloads, Settings)
│   │   └── EpisodeStack.tsx    # Stack: list → detail → player
│   ├── screens/
│   │   ├── HomeScreen.tsx      # Continue watching, popular episodes
│   │   ├── SearchScreen.tsx    # Cross-provider search
│   │   ├── SeasonScreen.tsx    # Episode grid for a series/season
│   │   ├── EpisodeScreen.tsx   # Detail + player + download
│   │   ├── DownloadsScreen.tsx # Download queue
│   │   ├── SettingsScreen.tsx  # Vault, providers, preferences
│   │   └── VaultSetupScreen.tsx# First-run master password creation
│   ├── components/
│   │   ├── VideoPlayer.tsx     # react-native-video (ExoPlayer) wrapper
│   │   ├── EpisodeCard.tsx     # Material Design card
│   │   └── DownloadButton.tsx  # Triggers Android DownloadManager
│   └── native/
│       ├── DownloadService.ts  # Native module for background downloads
│       └── VaultBridge.ts      # react-native-keychain wrapper
├── package.json                # Depends on @thuis/core + react-native + expo or bare RN
├── app.json
├── metro.config.js
├── tsconfig.json
└── babel.config.js
```

**Key decisions**:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Navigation** | React Navigation (bottom tabs + stack) | Industry standard for RN, matches web router pattern |
| **Video** | `react-native-video` with ExoPlayer | Best HLS support on Android, hardware-accelerated |
| **Download** | Android `DownloadManager` via native module | Background downloads, system notification, works when app is killed |
| **Vault** | `react-native-keychain` (Android Keystore) + `crypto.subtle` polyfill | Biometric unlock, hardware-backed key storage |
| **UI** | React Native Paper (Material Design 3) | Consistent Android look, different from web's Tailwind |
| **State** | Zustand (same as web) | Shared store logic with core |
| **Build** | Bare React Native (not Expo) | Need native modules for DownloadManager + Keystore |

**Postponed**: Android (APK) is a separate native stack (React Native) and is not in scope for the initial release. The web app and Electron desktop are the primary targets.

---

## 12. First-Time Setup Flow

The very first time a user launches the app on any platform:

```
LAUNCH (first time)
  │
  ├─► No vault key exists?
  │     YES → Show "Maak een hoofdwachtwoord" screen
  │            → Create master password (min 8 chars, confirmation)
  │            → Warning: "Dit wachtwoord kan niet worden hersteld"
  │            → On submit: derive key, store encrypted blob
  │            → Vault is now UNLOCKED
  │
  ├─► Vault exists but LOCKED?
  │     → Show unlock screen (master password or biometric)
  │     → On success: vault UNLOCKED
  │
  ├─► Vault UNLOCKED but no providers configured?
  │     → Show "Voeg een provider toe" screen
  │     → Options: VRT MAX, VTM GO, Play.TV
  │     → For each: enter email + password
  │     → Credentials encrypted and stored
  │     → Optional: "Verifieer nu" tests login
  │
  ├─► Vault UNLOCKED + providers configured?
  │     → Show main app (search/browse)
  │
  └─► Electron with OS keychain mode?
       → Skip master password setup entirely
       → safeStorage handles encryption
       → Vault is always unlocked while app runs
```

**Re-entry flow** (subsequent launches):

```
LAUNCH
  ├─► Web: Vault is LOCKED → show unlock screen (master password required)
  ├─► Electron (keychain mode): Vault UNLOCKED → go straight to main app
  ├─► Electron (master password mode): Vault LOCKED → show unlock screen
  └─► (Future: Android biometric unlock)
```

---

## 13. Offline Mode

### 13.1 What Works Offline

| Feature | Offline Behavior |
|---------|-----------------|
| Browse cached episode metadata | Full functionality (cached in IndexedDB/AsyncStorage) |
| Search history | Full functionality (local only) |
| View download queue | Full functionality (queue state is local) |
| Play downloaded episodes | Full functionality (local files) |
| Resume partial downloads | ✅ (Electron: temp segments) |
| Search for new episodes | ❌ (requires network — show "Geen internetverbinding" with last cached results) |
| VRT MAX login | ❌ (requires network) |
| Stream new episodes | ❌ (requires network) |

### 13.2 Cache Strategy

```typescript
// Metadata cache (episodes, seasons, series info)
interface MetadataCache {
  get(key: string): Promise<CachedEntry | null>;
  set(key: string, data: unknown, ttlMs: number): Promise<void>;
  invalidate(key: string): Promise<void>;
  clear(): Promise<void>;
}

// TTLs:
// - Episode detail: 1 hour (VRT API responses don't change often)
// - Season list: 1 hour
// - Search results: 30 minutes
// - Provider availability: 24 hours

// Storage:
// - Web: IndexedDB via idb-keyval
// - Electron: IndexedDB (same as web) or SQLite via better-sqlite3
```

### 13.3 UI for Offline State

A persistent banner at the top of the screen when offline:
```
╔══════════════════════════════════════════════════════╗
║  ⚠  Geen internetverbinding — toon resultaten uit   ║
║     cache. Zoeken en streamen is niet beschikbaar.   ║
╚══════════════════════════════════════════════════════╝
```

---

## 14. Cross-Provider Deduplication

### 14.1 Problem

The same episode (e.g., "Thuis S31A105") may appear on VRT MAX and potentially on another provider. We need to detect and merge duplicates.

### 14.2 Strategy

```typescript
interface EpisodeFingerprint {
  // Normalized identifiers used for dedup
  normalizedTitle: string;        // Lowercase, remove accents, trim
  season: number;
  episode: number;
  seriesTitle: string;
}

function fingerprint(episode: Episode): EpisodeFingerprint {
  return {
    normalizedTitle: episode.title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim(),
    season: episode.season,
    episode: episode.episode,
    seriesTitle: episode.seriesTitle.toLowerCase().trim(),
  };
}

function deduplicate(episodes: Episode[]): Episode[] {
  const seen = new Map<string, Episode>();
  for (const ep of episodes) {
    const key = `${fingerprint(ep).seriesTitle}|s${ep.season}a${ep.episode}`;
    if (!seen.has(key)) {
      seen.set(key, ep);
    }
    // If same episode from multiple providers, merge provider info
    // (store as array of providers for display)
  }
  return Array.from(seen.values());
}
```

### 14.3 UI Display

When the same episode exists on multiple providers:

```
┌────────────────────────────────────────────────────────┐
│  Aflevering 105  •  S31  •  E105                       │
│  Beschikbaar op:                                       │
│  [VRT MAX] [VTM GO]                                    │
│  Kies een provider om af te spelen.                    │
└────────────────────────────────────────────────────────┘
```

---

## 15. Research-Blocked Provider Handling

Providers whose API has not yet been reverse-engineered (VTM GO, Play.TV) are still visible in the UI:

### 15.1 UI States for Non-Implemented Providers

| State | Display |
|-------|---------|
| **Not researched** | Provider card in settings: "VTM GO — Nog niet beschikbaar. Binnenkort!" |
| **In research** | Provider card: "VTM GO — Bezig met onderzoek" (after R&D branch started) |
| **Implemented** | Provider card: "VTM GO — Actief ✓" with credential form |

### 15.2 Credential Pre-Collection

Even before a provider's API is implemented, users can enter their credentials:

```typescript
// Credentials are stored in the vault regardless of adapter availability
await vault.addCredentials('vtm', 'user@example.com', 'password123');
// Later, when VTM adapter is implemented:
// credentials are already there, no re-entry needed
```

This avoids the frustration of "I already told you my password, why do I need to enter it again?"

### 15.3 Implementation Checklist (for each new provider)

```
[ ] R001: Map authentication flow (OIDC? REST? Cookies?)
[ ] R002: Identify API endpoints
[ ] R003: Determine DRM status
[ ] R004: Implement ProviderAdapter
[ ] R005: Write TDD tests (mocked HTTP)
[ ] R006: Integration test with real credentials
[ ] R007: Update ProviderRegistry
[ ] R008: Mark provider as "active" in UI
```

---

## 16. API Change Detection

Provider APIs can change without notice. The app needs to detect and handle this.

### 16.1 Detection Strategies

| Strategy | Mechanism | Response |
|----------|-----------|----------|
| **HTTP status monitoring** | Track non-200/non-expected status codes per endpoint | Log warning after 3 failures |
| **Response shape validation** | Zod schemas validate all API responses. If parsing fails, the shape has likely changed | Report to user, log full response for debugging |
| **Expected status check** | `perform_login` returning 200 instead of expected 403 | Flag as API change |
| **Cookie pattern check** | Missing expected cookies after login | Flag as auth flow change |
| **JWT key check** | Player token request fails → signing key may have rotated | Attempt to re-extract from player scripts |

### 16.2 User Notification

When a provider API change is detected:

```
┌──────────────────────────────────────────────────────┐
│  ⚠  VRT MAX lijkt gewijzigd te zijn. De app werkt   │
│     mogelijk niet naar behoren.                      │
│                                                      │
│  [Meer informatie]  [Probeer opnieuw]                │
└──────────────────────────────────────────────────────┘
```

The "Meer informatie" button shows:
- Which provider is affected
- Error details (technical, for copy-paste)
- Link to GitHub issues for the project

### 16.3 Graceful Degradation

When an API change is detected but not yet fixed:

| Scenario | Degraded Behavior |
|----------|------------------|
| Auth flow changed | Show "handmatig inloggen op de website" instruction. User can still watch via browser. |
| GraphQL response changed | Show cached episode metadata if available. New searches disabled. |
| Stream resolution changed | Playback disabled. Downloaded episodes still playable. |
| Single endpoint changed | Retry with alternative known patterns. Fall back to public endpoint. |

### 16.4 Version Pinning & Compatibility

```typescript
// Each provider adapter declares its API version compatibility
interface ProviderAdapter {
  readonly apiVersions: {
    auth: string;      // e.g. "2025-03" — the last known working auth protocol version
    metadata: string;  // e.g. "v1" — GraphQL schema version
    stream: string;    // e.g. "v2" — vualto API version
  };
}
```

When the app starts, it can check if a newer adapter version is available (via app update) and warn the user.

---

## 17. Module Architecture — @thuis/core

### 17.1 Directory Structure

```
packages/core/src/
├── index.ts                          # Public API exports
├── url-resolver.ts                   # VRT URL parsing (existing)
│
├── auth/
│   ├── VrtAuthService.ts             # VRT login/token/refresh (NEW)
│   ├── types.ts                      # Credential, token types (NEW)
│   └── __tests__/
│       └── VrtAuthService.test.ts    # TDD tests (NEW)
│
├── episode/
│   ├── VrtEpisodeService.ts          # Metadata query, stream resolution (NEW)
│   ├── types.ts                      # GraphQL response types (NEW)
│   └── __tests__/
│       └── VrtEpisodeService.test.ts # TDD tests (NEW)
│
├── download/
│   ├── StreamDownloader.ts           # FFmpeg process management (NEW)
│   ├── DownloadQueueManager.ts       # Queue persistence + state (NEW)
│   ├── types.ts                      # Stream, download types (NEW)
│   └── __tests__/
│       ├── StreamDownloader.test.ts  # TDD tests (NEW)
│       └── DownloadQueue.test.ts     # TDD tests (NEW)
│
├── graphql/
│   ├── client.ts                     # GraphQL client (existing, refactor)
│   ├── queries.ts                    # GraphQL query strings (existing, extend)
│   └── types.ts                      # GraphQL response schemas (existing, extend)
│
├── types/
│   ├── episode.ts                    # Episode types (existing, extend)
│   ├── download.ts                   # Download types (existing, extend)
│   └── index.ts                      # Re-exports (existing, extend)
│
├── store/
│   ├── index.ts                      # Zustand store root
│   ├── types.ts                      # Store state types
│   ├── episode-slice.ts             # Episode state
│   ├── download-slice.ts            # Download state
│   └── ui-slice.ts                  # UI state (theme, sidebar, etc.)
│
└── __tests__/
    └── integration/
        └── thuis-download.test.ts    # End-to-end integration test (NEW)
```

### 17.2 VrtAuthService API

```typescript
class VrtAuthService {
  constructor(options?: {
    httpClient?: HttpClient;
    cookieStore?: CookieStore;
    cacheTokens?: boolean;
    tokenStorage?: TokenStorage;
  });

  /** Full login flow: session → credential → tokens */
  async login(credentials: { email: string; password: string }): Promise<VrtTokens>;

  /** Refresh tokens using stored refresh token. Returns new tokens. */
  async refreshTokens(): Promise<VrtTokens>;

  /** Get valid access token. Auto-refreshes if expired. Throws if not logged in. */
  async getAccessToken(): Promise<string>;

  /** Get valid video token. Auto-refreshes if expired. */
  async getVideoToken(): Promise<string>;

  /** Get valid refresh token. Returns null if unavailable. */
  async getRefreshToken(): Promise<string | null>;

  /** Check if there are stored (and non-expired) tokens */
  async isLoggedIn(): Promise<boolean>;

  /** Clear all stored tokens */
  async logout(): Promise<void>;

  /** Force re-login (clear cache + login) */
  async relogin(credentials: { email: string; password: string }): Promise<VrtTokens>;
}

interface VrtTokens {
  accessToken: string;
  videoToken: string;
  refreshToken: string;
  expiresAt: number;            // Unix timestamp (seconds)
  acquiredAt: number;           // Unix timestamp (seconds)
}
```

### 17.3 VrtEpisodeService API

```typescript
class VrtEpisodeService {
  constructor(
    private authService: VrtAuthService,
    options?: { httpClient?: HttpClient }
  );

  /** Fetch episode metadata from a VRT MAX URL */
  async getEpisode(url: string): Promise<EpisodeDetail>;

  /** Resolve HLS stream URL from a stream ID */
  async resolveStream(streamId: string, options?: {
    videoToken?: string;
    client?: string;
  }): Promise<StreamData>;

  /** Convenience: get episode + resolve stream in one call */
  async getEpisodeWithStream(url: string): Promise<{
    episode: EpisodeDetail;
    stream: StreamData;
  }>;
}
```

### 17.4 Error Hierarchy

```typescript
class VrtError extends Error { code: string }

class AuthenticationError extends VrtError {
  code: 'AUTH_FAILED';
}

class InvalidCredentialsError extends AuthenticationError {
  code: 'INVALID_CREDENTIALS';
}

class TokenAcquisitionError extends AuthenticationError {
  code: 'TOKEN_ACQUISITION_FAILED';
}

class TokenExpiredError extends AuthenticationError {
  code: 'TOKEN_EXPIRED';
}

class EpisodeUnavailableError extends VrtError {
  code: 'EPISODE_UNAVAILABLE';
}

class GeoBlockedError extends VrtError {
  code: 'GEO_BLOCKED';
}

class DrmError extends VrtError {
  code: 'DRM_PROTECTED';
}

class DownloadError extends VrtError {
  code: 'DOWNLOAD_FAILED';
}

class ProviderNotSupportedError extends VrtError {
  code: 'PROVIDER_NOT_SUPPORTED';
}
```

---

## 18. Integration Test: thuis-download (TDD)

### 18.1 Unit Tests (mocked HTTP)

```
packages/core/src/auth/__tests__/VrtAuthService.test.ts
├── login()
│   ├── gets session cookies from /sso/login
│   ├── posts credentials to /perform_login with Oidcxsrf header
│   ├── follows redirectUrl to extract tokens
│   ├── returns VrtTokens with all 3 tokens
│   ├── throws InvalidCredentialsError on wrong password
│   ├── throws TokenAcquisitionError when redirect doesn't set cookies
│   └── throws TokenAcquisitionError when response missing fields
│
├── refreshTokens()
│   ├── sends refresh request with _rt cookie
│   ├── updates stored tokens on success
│   ├── throws TokenExpiredError on 401
│   └── throws TokenAcquisitionError on missing response cookies
│
├── getAccessToken()
│   ├── returns cached token if not expired
│   ├── auto-refreshes if 5 min from expiry
│   └── throws if not logged in and no tokens stored
│
├── isLoggedIn()
│   ├── returns true if valid tokens exist
│   ├── returns false if tokens expired and cannot refresh
│   └── returns false if never logged in
│
└── logout()
    └── clears all stored tokens

packages/core/src/episode/__tests__/VrtEpisodeService.test.ts
├── getEpisode()
│   ├── sends VideoPage GraphQL query
│   ├── parses response into EpisodeDetail
│   ├── uses public endpoint if no auth token
│   ├── retries with refreshed token on 401
│   ├── throws EpisodeUnavailableError if no streamId
│   └── includes series, season, brand metadata
│
├── resolveStream()
│   ├── gets vrtPlayerToken with video token identity
│   ├── fetches stream data with player token
│   ├── returns HLS URL from targetUrls
│   ├── throws DrmError if drm=true
│   ├── throws GeoBlockedError if geo-restricted code
│   └── throws EpisodeUnavailableError on unknown code
│
└── getEpisodeWithStream()
    └── combines getEpisode + resolveStream

packages/core/src/download/__tests__/StreamDownloader.test.ts
├── download()
│   ├── spawns ffmpeg with correct arguments
│   ├── pipes progress events
│   ├── resolves on successful completion
│   ├── rejects on ffmpeg error exit code
│   └── rejects if ffmpeg not found
│
└── downloadRange()
    ├── downloads only specified byte range
    └── verifies first bytes of HLS manifest

packages/core/src/__tests__/integration/thuis-download.test.ts
├── full flow
│   ├── logs in with real VRT credentials (from env)
│   ├── fetches thuis episode metadata
│   ├── resolves HLS stream URL
│   ├── downloads first 100KB to verify accessibility
│   ├── reports drm status
│   └── reports geo-restriction if applicable
```

### 18.2 Test Credentials

Integration tests use environment variables:
```bash
VRT_USERNAME=user@example.com
VRT_PASSWORD=********
VRT_TEST_EPISODE_URL=https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/
```

Unit tests use `nock` for HTTP mocking with realistic cookie and response fixtures.

---

## 19. Component Tree — Web App

```
packages/web-app/src/
├── main.tsx                          # App entry, router setup
├── App.tsx                           # Layout, theme provider, routes
├── index.css                         # Tailwind imports + globals
│
├── pages/
│   ├── LoginPage.tsx                 # VRT MAX login form (email + password)
│   ├── SearchPage.tsx                # Unified search across providers
│   ├── SeasonPage.tsx                # Episode list for a season
│   ├── EpisodePage.tsx               # Single episode detail + play/download
│   ├── DownloadQueuePage.tsx         # Download progress overview
│   ├── SettingsPage.tsx              # Provider credentials, preferences
│   └── VaultPage.tsx                 # Credential vault management (P2)
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx               # Navigation + provider status
│   │   ├── Header.tsx                # Search bar, user menu
│   │   └── Footer.tsx
│   │
│   ├── auth/
│   │   ├── LoginForm.tsx             # Email + password form
│   │   ├── TokenStatusBadge.tsx      # Shows auth status (green/red)
│   │   └── LogoutButton.tsx
│   │
│   ├── episode/
│   │   ├── EpisodeCard.tsx           # Thumbnail + title + metadata
│   │   ├── EpisodeList.tsx           # Scrollable episode grid
│   │   ├── SeasonSelector.tsx        # Dropdown for season selection
│   │   └── EpisodeDetail.tsx         # Full metadata display
│   │
│   ├── player/                        # (P2)
│   │   ├── VideoPlayer.tsx           # HLS.js player wrapper
│   │   ├── PlayerControls.tsx        # Play/pause/seek/volume
│   │   ├── PlayerTimeline.tsx        # Seek bar + thumbnails
│   │   └── DownloadButton.tsx        # Adds to download queue
│   │
│   ├── download/
│   │   ├── DownloadQueueList.tsx      # List of download jobs
│   │   ├── DownloadProgressBar.tsx   # Per-job progress indicator
│   │   └── DownloadControls.tsx      # Pause/resume/cancel per job
│   │
│   └── vault/                         # (P2)
│       ├── VaultStatus.tsx            # Lock/unlock indicator
│       ├── CredentialForm.tsx         # Provider credential input
│       └── ProviderCard.tsx           # Connected provider overview
│
└── hooks/
    ├── useAuth.ts                     # Auth state + actions
    ├── useEpisode.ts                  # Episode fetching hook
    ├── useDownload.ts                 # Download queue hook
    ├── usePlayer.ts                   # Player state hook (P2)
    └── useVault.ts                    # Vault state hook (P2)
```

---

## 20. Route Design — Web App

```typescript
// React Router v7 routes
const routes = [
  { path: '/',             component: SearchPage },
  { path: '/login',        component: LoginPage },
  { path: '/browse/:provider/:series', component: SeasonPage },
  { path: '/episode/:provider/:series/:season/:episodeCode', component: EpisodePage },
  { path: '/queue',        component: DownloadQueuePage },
  { path: '/settings',     component: SettingsPage },
  { path: '/vault',        component: VaultPage,      // P2
  { path: '/watch/:provider/:id', component: WatchPage // P2
];
```

---

## 21. Provider-Specific Integration Specs (Future — P2)

### 21.1 VTM GO Integration

**Status**: Research needed
**URL**: `https://vtm.be/vtmgo`
**Owner**: DPG Media

Integration approach:
1. Open browser DevTools on vtm.be/vtmgo
2. Capture login request/response (OIDC flow likely)
3. Map API endpoints for:
   - Authentication
   - Episode listing per program
   - Stream manifest URL resolution
4. Implement `ProviderAdapter` interface
5. Determine DRM status (likely Widevine)

### 21.2 Play.TV Integration

**Status**: Research needed
**URL**: `https://www.play.tv`
**Owner**: SBS Belgium (DPG Media)

Integration approach:
1. Open browser DevTools on play.tv
2. Capture login request/response
3. Map API endpoints
4. Implement `ProviderAdapter` interface
5. Determine DRM status

---

## 22. UI States & Error Handling

Every data-fetching component must handle 4 states:

| State | Display |
|-------|---------|
| **Loading** | Skeleton/spinner with shimmer animation |
| **Error** | Descriptive error message with retry button |
| **Empty** | Friendly "No results" message with suggestion |
| **Success** | Normal content display |

### Standard Error Messages

| Error | User Message |
|-------|-------------|
| `INVALID_CREDENTIALS` | "Ongeldig e-mailadres of wachtwoord. Probeer opnieuw." |
| `TOKEN_EXPIRED` | "Sessie verlopen. Log opnieuw in." |
| `GEO_BLOCKED` | "Deze video is enkel beschikbaar in België." |
| `DRM_PROTECTED` | "Deze video is beveiligd en kan niet worden gedownload." |
| `EPISODE_UNAVAILABLE` | "Deze aflevering is niet beschikbaar." |
| `DOWNLOAD_FAILED` | "Download mislukt. Controleer je internetverbinding en probeer opnieuw." |
| `PROVIDER_NOT_SUPPORTED` | "Deze provider wordt nog niet ondersteund." |
| Network error | "Geen internetverbinding. Controleer je netwerk." |
| Unknown error | "Er is een fout opgetreden. Probeer het later opnieuw." |

All error messages are in Dutch (Belgian context).

---

## 23. Electron Desktop Integration

The Electron app wraps the web app with additional native capabilities:

| Capability | Electron Specific |
|------------|------------------|
| **FFmpeg download** | `child_process.spawn('ffmpeg', ...)` in main process |
| **File system access** | Save downloads to user-chosen directory via `dialog.showSaveDialog()` |
| **OS keychain** | `safeStorage` for encrypting credentials |
| **Auto-updates** | `electron-updater` with GitHub Releases |
| **System tray** | Background download progress in tray icon |
| **Notifications** | OS-native download completion notifications |
| **Context menu** | Right-click on episodes for advanced options |

The Electron main process exposes download capabilities via IPC:

```typescript
// Preload API
interface ElectronDownloadApi {
  startDownload(url: string, outputPath: string): Promise<DownloadHandle>;
  cancelDownload(id: string): Promise<void>;
  pauseDownload(id: string): Promise<void>;
  resumeDownload(id: string): Promise<void>;
  onProgress(callback: (progress: DownloadProgress) => void): void;
  getDownloads(): Promise<DownloadJob[]>;
  selectOutputDirectory(): Promise<string | null>;
}
```

---

## 24. Quality & Testing Strategy

- **Unit Testing**: Jest for all business logic. Target 80% coverage.
- **Integration Testing**: Jest + nock for HTTP-mocked provider flows. Real credentials for end-to-end tests (excluded from CI, run manually).
- **Component Testing**: Playwright Component Tests for React components.
- **E2E Testing**: Playwright for full browser flows (login → browse → play).
- **Spec-Driven**: Implementation follows `.specify/tasks/*.md` derived from SPEC.md.

---

## 25. CI/CD Pipeline

Implemented in `.github/workflows/build.yml`:

### Pipeline

```
Build Docs (Docusaurus)
  → Lint (all packages)
    → Test (core: jest, web-app: jest, electron-app: jest)
      → Build Web (vite build)
      → Build Electron (electron-builder: Windows NSIS, Linux deb/rpm/AppImage, macOS dmg)
        → Deploy Docs (gh-pages — https://aldof.github.io/thuis)
        → Deploy Web (rsync to VPS — https://thuis.aldof.duckdns.org)
        → Publish Electron (upload artifacts to GitHub Release)

Integration tests: Run manually (require real credentials, not in CI).
Scheduled: Weekly credential verification workflow (runs integration tests, alerts on failure).
```

### Build Matrix

```yaml
jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps: [checkout, install, build:docusaurus, deploy:gh-pages]

  build-web:
    runs-on: ubuntu-latest
    steps: [checkout, install, build:core, build:web, deploy:vps]

  build-electron:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps: [checkout, install, build:core, build:web, build:electron, upload:release]

  publish:
    needs: [build-docs, build-web, build-electron]
    steps: [create-release]
```

### Artifacts

| Target | File(s) | Destination |
|--------|---------|-------------|
| Documentation | `docs/build/` | GitHub Pages (`gh-pages` branch) — `https://aldof.github.io/thuis` |
| Web App | `packages/web-app/dist/` | Self-hosted VPS — `https://thuis.aldof.duckdns.org` |
| Windows | `Thuis-Setup-*.exe`, `Thuis-*-portable.exe` | GitHub Release |
| Linux | `thuis_*.deb`, `thuis-*.rpm`, `Thuis-*.AppImage` | GitHub Release |
| macOS | `Thuis-*.dmg` | GitHub Release |

---

## 26. Security & Secrets

- **Secret Management**: No secrets in repo. All credentials injected via environment variables in CI.
- **VRT Token**: `VRT_BEARER_TOKEN` used for GraphQL requests (fallback without full auth flow).
- **Master Password**: Never stored or transmitted. Key derived via PBKDF2 on each unlock.
- **Provider Passwords**: Decrypted in-memory only, never written to disk, never logged.
- **Electron safeStorage**: Uses OS-level encryption (AES-256-GCM on Windows/macOS, libsecret on Linux). Key managed by OS.
- **Android Keystore**: Hardware-backed on supported devices. Biometric authentication available.
- **Network Security**: All provider API calls use HTTPS. Certificate pinning considered for Electron/Android (future).
- **FFmpeg Binary**: Detected from system PATH, not bundled. User is warned at first download if missing.
- **Audit Log**: Vault operations (unlock, add credential, remove credential) logged locally. No logging of plaintext passwords.
- **Session Boundaries**: Vault auto-locks on app close. No cross-session credential caching outside encrypted storage.

---

## 27. Glossary

| Term | Definition |
|------|------------|
| **VRT MAX** | Flemish public broadcaster's streaming platform (formerly VRT NU). |
| **VTM GO** | DPG Media's streaming platform for commercial Flemish TV. |
| **Play.TV** | SBS Belgium's streaming platform (Play4, Play5, Play6, Play7). |
| **VRT-API** | Official VRT MAX GraphQL endpoint. |
| **HLS** | HTTP Live Streaming — Apple's adaptive bitrate streaming protocol. |
| **FFmpeg** | Open-source multimedia framework for transcoding and streaming. |
| **OIDC** | OpenID Connect — authentication protocol used by VRT MAX. |
| **vrtPlayerToken** | Temporary token required to access VRT's media streaming servers. |
| **Zod** | Schema validation library for TypeScript. |
| **Zustand** | Minimal state management library for React. |
| **TDD** | Test-Driven Development. |
| **DRY** | Don't Repeat Yourself (shared core). |
| **Provider Adapter** | Plugin interface for uniform integration of different video providers. |
| **Credential Vault** | Encrypted storage for provider login credentials. |
