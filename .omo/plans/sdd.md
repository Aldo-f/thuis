# Software Design Document (SDD): Thuis-V2 — VRT MAX Content Monitor

**Version**: 0.2.0  
**Status**: Draft  
**Author**: Aldo Fieuw  
**Based on**: `SPEC.md` v0.1.0  
**MVP Scope**: Download a specific VRT MAX Thuis episode given its URL

---

## Table of Contents

1. [System Overview & Objectives](#1-system-overview--objectives)
2. [C4 Architecture (Container Level)](#2-c4-architecture-container-level)
3. [Data Flow & Sequence Diagrams](#3-data-flow--sequence-diagrams)
4. [Workspace Structure](#4-workspace-structure)
5. [Component Specifications](#5-component-specifications)
6. [Data Models & Store Design](#6-data-models--store-design)
7. [API Contracts & Integrations](#7-api-contracts--integrations)
8. [UI/UX Design Principles](#8-uiux-design-principles)
9. [Implementation Phases](#9-implementation-phases)
10. [Quality & Testing Strategy](#10-quality--testing-strategy)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Glossary & References](#12-glossary--references)

---

## 1. System Overview & Objectives

### 1.1 Purpose

Thuis-V2 is a modular ecosystem for monitoring and downloading VRT MAX content related to the Belgian television series **"Thuis"**. The system provides a unified interface — available both as a desktop application (Electron) and a responsive web application — to search, browse, and download episodes.

### 1.2 MVP Definition

The **Minimum Viable Product** is a single-user workflow:

```
Enter a VRT MAX Thuis episode URL  →  Episode metadata is displayed  →  Video is downloaded to disk
```

Concrete target: `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6102/`

### 1.3 System Characteristics

| Attribute | Description |
|-----------|-------------|
| **Extensibility** | Core logic is package-separated; adding new VRT shows requires zero app changes |
| **Offline-first** | Metadata cached locally; downloads resume on reconnect |
| **Dual-target** | Same core powers both Web (SPA) and Electron (Desktop) |
| **Type-safe** | All I/O validated through Zod schemas end-to-end |

---

## 2. C4 Architecture (Container Level)

### 2.1 System Context Diagram

```mermaid
C4Context
  title System Context — Thuis-V2

  Person(user, "User", "Fan of the TV series 'Thuis' who wants to watch episodes offline")

  System_Ext(vrtmax, "VRT MAX", "Belgian public broadcaster streaming platform")
  System_Ext(ghpages, "GitHub Pages", "Static web hosting")
  System_Ext(ghreleases, "GitHub Releases", "Binary distribution")

  System_Boundary(thuis, "Thuis-V2 Ecosystem") {
    Container(webapp, "Web App", "React 19 + Vite", "Responsive SPA for browsing and downloading via browser")
    Container(electron, "Electron App", "Electron 31 + React 19", "Desktop application with native download management")
    Container(core, "Core Library", "TypeScript 5 + Zod + Zustand", "Shared business logic, API clients, state management")
  }

  Rel(user, webapp, "Browses & downloads episodes via browser")
  Rel(user, electron, "Uses desktop app for offline downloads")
  Rel(webapp, core, "Imports data & business logic")
  Rel(electron, core, "Imports data & business logic")
  Rel(core, vrtmax, "GraphQL search & video API calls")
  Rel(webapp, ghpages, "Served from")
  Rel(electron, ghreleases, "Distributed via")
```

### 2.2 Container Diagram

```mermaid
C4Container
  title Container Diagram — Thuis-V2 Internal Structure

  Person(user, "User", "Downloads Thuis episodes")

  System_Boundary(core_b, "@thuis/core") {
    Container(graphql, "GraphQL Client", "TypeScript", "Queries VRT MAX for episode metadata & video IDs")
    Container(downloader, "Download Service", "TypeScript + yt-dlp", "Resolves video streams and downloads segments")
    Container(store, "Zustand Store", "TypeScript", "Global reactive state for episodes, downloads, UI")
    Container(schemas, "Zod Schemas", "TypeScript", "Runtime type validation for all data boundaries")
  }

  System_Boundary(web_b, "@thuis/web-app") {
    Container(web_ui, "React UI", "React 19 + Tailwind 4", "Search, episode list, download queue")
    Container(web_router, "React Router", "TypeScript", "Client-side routing")
  }

  System_Boundary(electron_b, "@thuis/electron-app") {
    Container(elec_main, "Main Process", "Electron 31", "Window management, IPC, native file system")
    Container(elec_preload, "Preload Script", "TypeScript", "Context bridge for secure renderer↔main IPC")
    Container(elec_renderer, "Renderer (React)", "React 19 + Tailwind 4", "Same UI as web-app, embedded in Electron")
    Container(elec_updater, "Auto-Updater", "electron-updater", "Checks GitHub Releases for new versions")
  }

  System_Ext(vrt_graphql, "VRT GraphQL API", "vrtnu-api/graphql/v1")
  System_Ext(vrt_video, "VRT Video API", "media-services-public.vrt.be")
  System_Ext(gh_storage, "GitHub", "Pages / Releases / Actions")

  Rel(user, web_ui, "Uses")
  Rel(user, elec_renderer, "Uses")

  Rel(web_ui, store, "Reads/writes state")
  Rel(elec_renderer, store, "Reads/writes state")
  Rel(web_ui, graphql, "Triggers search")
  Rel(elec_renderer, graphql, "Triggers search")

  Rel(elec_renderer, elec_preload, "IPC calls via contextBridge")
  Rel(elec_preload, elec_main, "Forwards IPC")
  Rel(elec_main, downloader, "Triggers download via child process")

  Rel(graphql, vrt_graphql, "Search & episode queries (Bearer token)")
  Rel(downloader, vrt_video, "Video manifest resolution")
  Rel(downloader, vrt_graphql, "Episode stream ID lookup")

  Rel(elec_updater, gh_storage, "Checks for updates")
```

---

## 3. Data Flow & Sequence Diagrams

### 3.1 Episode Search Flow

```mermaid
sequenceDiagram
  actor User
  participant UI as React UI
  participant Store as Zustand Store
  participant API as GraphQL Client
  participant VRT as VRT MAX GraphQL

  User->>UI: Enters search query (e.g. "thuis")
  UI->>API: searchEpisodes(query)
  API->>VRT: POST /vrtnu-api/graphql/v1
  Note over API,VRT: component(componentId: encodedSearchQuery)
  VRT-->>API: PaginatedTileList with EpisodeTile nodes
  API-->>UI: Transformed Episode[]
  Note over API,UI: Parses tiles, extracts title/season/episode/image/url
  UI->>Store: setEpisodes(episodes)
  Store-->>UI: Re-renders episode grid
  UI-->>User: Displays episode cards with metadata
```

### 3.2 Episode Download Flow (MVP — URL-based)

```mermaid
sequenceDiagram
  actor User
  participant UI as React UI
  participant Store as Zustand Store
  participant API as GraphQL Client
  participant VRT as VRT MAX
  participant DL as Download Service
  participant FS as File System

  User->>UI: Pastes VRT MAX episode URL
  Note over User,UI: e.g. /vrtmax/a-z/thuis/31/thuis-s31a6102/
  UI->>API: resolveEpisode(url)
  API->>API: Parse URL → { show: "thuis", season: 31, episode: "s31a6102" }
  API->>VRT: POST /vrtnu-api/graphql/v1
  Note over API,VRT: component query → EpisodeTile(s)
  VRT-->>API: Episode metadata + video objectId/pubId
  API-->>UI: EpisodeDetail { id, title, streamId, image, duration }
  UI-->>User: Displays episode detail (title, duration, thumbnail, download button)

  User->>UI: Clicks "Download"
  UI->>Store: addDownload({ episodeId, status: "pending" })
  UI->>DL: startDownload(streamId)
  DL->>VRT: GET video manifest (VRT Video API)
  VRT-->>DL: HLS manifest URL (m3u8) or direct stream URL
  DL->>FS: Download segments → assemble file
  DL-->>Store: updateProgress(episodeId, { status: "downloading", progress })
  DL-->>Store: updateProgress(episodeId, { status: "completed" })
  UI-->>User: Shows "Download Complete" notification
```

### 3.3 Error Handling Flow

```mermaid
sequenceDiagram
  participant UI as React UI
  participant Store as Zustand Store
  participant DL as Download Service
  participant VRT as VRT MAX

  UI->>DL: startDownload(invalidStreamId)
  DL->>VRT: GET video manifest
  VRT-->>DL: 403 / 404 / empty response
  DL->>DL: Validate response → error detected
  DL-->>Store: updateStatus(episodeId, { status: "failed", error: "Stream not available" })
  Store-->>UI: Renders error state on download card
  UI-->>UI: Shows retry button
  UI->>DL: retryDownload(episodeId)
  Note over UI,DL: User-initiated retry
```

---

## 4. Workspace Structure

```
thuis/
├── .specify/                  # Spec Kit framework (constitution, templates, workflows)
├── packages/
│   ├── core/                  # @thuis/core — shared business logic
│   │   ├── src/
│   │   │   ├── graphql/       # VRT MAX GraphQL client
│   │   │   │   ├── client.ts       # HTTP client (fetch-based, Bearer token auth)
│   │   │   │   ├── queries.ts      # GraphQL query/mutation definitions
│   │   │   │   └── types.ts        # Response type aliases
│   │   │   ├── downloader/    # Video download orchestration
│   │   │   │   ├── service.ts      # yt-dlp wrapper / stream downloader
│   │   │   │   ├── resolver.ts     # Resolves VRT video manifest URLs
│   │   │   │   └── types.ts        # Download job types
│   │   │   ├── store/         # Zustand state
│   │   │   │   ├── index.ts        # Combined store export
│   │   │   │   ├── episode-slice.ts    # Episode browsing state
│   │   │   │   ├── download-slice.ts   # Download queue state
│   │   │   │   └── ui-slice.ts         # UI preferences state
│   │   │   ├── types/         # Zod schemas + inferred types
│   │   │   │   ├── episode.ts        # EpisodeSchema
│   │   │   │   ├── download.ts       # DownloadJobSchema
│   │   │   │   └── index.ts          # Re-exports
│   │   │   └── index.ts       # Public API barrel export
│   │   ├── __tests__/         # Unit tests (Jest)
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── web-app/               # @thuis/web-app — React SPA
│   │   ├── src/
│   │   │   ├── components/    # Reusable UI components
│   │   │   │   ├── EpisodeCard.tsx
│   │   │   │   ├── EpisodeGrid.tsx
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── DownloadQueue.tsx
│   │   │   │   ├── DownloadProgress.tsx
│   │   │   │   └── ErrorBoundary.tsx
│   │   │   ├── pages/         # Route-level pages
│   │   │   │   ├── Home.tsx
│   │   │   │   ├── Search.tsx
│   │   │   │   └── EpisodeDetail.tsx
│   │   │   ├── hooks/         # Custom React hooks
│   │   │   │   ├── useEpisodeSearch.ts
│   │   │   │   ├── useDownload.ts
│   │   │   │   └── useStore.ts
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   └── index.css      # Tailwind 4 entry
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── electron-app/          # @thuis/electron-app — Desktop shell
│       ├── src/
│       │   ├── main/          # Electron main process
│       │   │   ├── index.ts         # App lifecycle, window creation
│       │   │   ├── ipc-handlers.ts  # IPC message handlers
│       │   │   └── updater.ts       # Auto-update configuration
│       │   ├── preload/       # Preload scripts
│       │   │   └── index.ts         # contextBridge API exposure
│       │   └── renderer/     # Electron-specific renderer (reuses web-app)
│       │       └── index.html       # Entry HTML loading web-app bundle
│       ├── electron-builder.yml
│       ├── package.json
│       └── tsconfig.json
│
├── website/                   # Docusaurus documentation site
│   ├── docs/
│   ├── src/
│   ├── static/
│   ├── blog/
│   ├── package.json
│   ├── docusaurus.config.js
│   └── sidebars.js
│
├── .github/
│   └── workflows/
│       └── ci.yml             # Lint → Test → Build → Publish
│
├── SPEC.md                    # Project specification (v0.1.0)
├── pnpm-workspace.yaml        # pnpm workspace config
├── tsconfig.base.json         # Shared TypeScript config
├── package.json               # Root (orchestration scripts)
└── AGENTS.md                  # Agent context pointer
```

---

## 5. Component Specifications

### 5.1 `@thuis/core` — Shared Library

**Purpose**: Single source of truth for all business logic, API communication, and state management. Both `web-app` and `electron-app` import from this package exclusively.

#### 5.1.1 GraphQL Client (`src/graphql/`)

| Export | Type | Description |
|--------|------|-------------|
| `createClient(baseUrl, token)` | Factory | Creates a configured GraphQL client instance |
| `searchEpisodes(query)` | Async Function | Searches VRT MAX by title; returns `Episode[]` |
| `getEpisodeByUrl(url)` | Async Function | Resolves a VRT MAX episode URL to `EpisodeDetail` |
| `getStreamId(episodeId)` | Async Function | Returns the video stream ID for download |

**Design Notes**:
- Uses native `fetch()` (no axios/ky dependency)
- Bearer token injected via factory — token never stored in source
- All responses validated through Zod schemas before returning
- Built-in retry (2 retries with exponential backoff)
- Timeout: 15s per request

**GraphQL Query Strategy**:
- The `search` endpoint uses the `component(componentId: ...)` query with a base64-encoded JSON payload containing the search term
- The `resolve` endpoint needs reverse-engineering to find the episode video ID from its URL slug

#### 5.1.2 Download Service (`src/downloader/`)

| Export | Type | Description |
|--------|------|-------------|
| `startDownload(downloadJob)` | Function | Initiates the download pipeline |
| `cancelDownload(jobId)` | Function | Cancels an active download |
| `getDownloadProgress(jobId)` | Function | Returns current progress |
| `resolveManifest(streamId)` | Async Function | Gets HLS manifest URL from VRT Video API |

**Download Pipeline**:
1. `resolveManifest(streamId)` → calls VRT Video Aggregator API → returns HLS manifest URL
2. Spawns `yt-dlp` as child process (or uses native HLS downloader as fallback)
3. Streams segments to temporary file
4. On completion, moves file to user-specified output directory
5. Emits progress events via a callback/EventEmitter

**Why yt-dlp**:
- Proven VRT MAX support
- Handles HLS/DASH segment assembly
- Supports resume on interrupted downloads
- Wide format selection (best quality, smallest size, audio-only)

**Fallback Strategy**:
- If `yt-dlp` is not installed, fall back to a pure-Node.js HLS downloader (using `node-fetch` & segment concatenation)
- Electron app bundles `yt-dlp` as a platform-specific binary

#### 5.1.3 Zustand Store (`src/store/`)

Three slices combined into a single store:

**Episode Slice** (`episode-slice.ts`):
```typescript
interface EpisodeSlice {
  episodes: Episode[];
  selectedEpisode: EpisodeDetail | null;
  searchQuery: string;
  isSearching: boolean;
  searchError: string | null;
  // Actions
  search: (query: string) => Promise<void>;
  selectEpisode: (episode: EpisodeDetail) => void;
  clearSearch: () => void;
}
```

**Download Slice** (`download-slice.ts`):
```typescript
interface DownloadSlice {
  downloads: DownloadJob[];
  activeDownloads: string[]; // job IDs
  // Actions
  enqueueDownload: (episode: EpisodeDetail) => Promise<void>;
  cancelDownload: (jobId: string) => void;
  retryDownload: (jobId: string) => Promise<void>;
  clearCompleted: () => void;
}
```

**UI Slice** (`ui-slice.ts`):
```typescript
interface UISlice {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  // Actions
  setTheme: (theme: UISlice['theme']) => void;
  toggleSidebar: () => void;
}
```

### 5.2 `@thuis/web-app` — React SPA

**Purpose**: Responsive single-page application for browsing and downloading Thuis episodes in the browser.

#### 5.2.1 Component Tree

```
App
├── Layout
│   ├── Header (branding, search bar)
│   └── Sidebar (download queue summary, navigation)
└── Routes
    ├── / → Home (welcome, featured episodes)
    ├── /search → SearchPage
    │   ├── SearchBar
    │   └── EpisodeGrid
    │       └── EpisodeCard[] (thumbnail, title, season/ep, duration)
    └── /episode/:id → EpisodeDetail
        ├── Episode metadata (title, season, episode, duration, image)
        ├── DownloadButton
        └── DownloadProgress (if active)
```

**Key Components**:

| Component | Responsibility |
|-----------|---------------|
| `SearchBar` | Text input with debounce; triggers `store.search()` |
| `EpisodeGrid` | Responsive CSS grid of episode cards |
| `EpisodeCard` | Clickable card with thumbnail, title, season/ep, duration badge |
| `EpisodeDetail` | Full episode information + download trigger |
| `DownloadQueue` | Sidebar showing active/completed downloads |
| `DownloadProgress` | Progress bar with cancel/retry controls |
| `ErrorBoundary` | Catches React render errors gracefully |

#### 5.2.2 Browser Download Note

In the **web-app**, browser downloads have limitations:
- Cannot write to arbitrary filesystem paths
- Uses the **Streams API** + **File System Access API** (Chromium) for saves
- Falls back to standard `download` attribute for direct file downloads
- Large files are chunked; download progress tracked via `ReadableStream`

### 5.3 `@thuis/electron-app` — Desktop Shell

**Purpose**: Full-featured desktop application with native file system access, system notifications, and auto-update.

#### 5.3.1 Main Process (`src/main/`)

| File | Responsibility |
|------|---------------|
| `index.ts` | Creates `BrowserWindow`, loads renderer, sets up app lifecycle |
| `ipc-handlers.ts` | Registers IPC handlers for file dialogs, downloads, notifications |
| `updater.ts` | `electron-updater` configuration (GitHub Releases) |

**IPC Channels**:

| Channel | Direction | Payload | Description |
|---------|-----------|---------|-------------|
| `download:start` | Renderer → Main | `{ streamId, outputPath }` | Initiates download |
| `download:progress` | Main → Renderer | `{ jobId, progress, status }` | Progress updates |
| `download:cancel` | Renderer → Main | `{ jobId }` | Cancels download |
| `download:complete` | Main → Renderer | `{ jobId, filePath }` | Download finished |
| `download:error` | Main → Renderer | `{ jobId, error }` | Download failed |
| `dialog:select-folder` | Renderer → Main | - | Opens native folder picker |
| `app:get-version` | Renderer → Main | - | Returns app version |
| `app:show-notification` | Main → Renderer | `{ title, body }` | System notification |

#### 5.3.2 Preload Script (`src/preload/index.ts`)

Exposes a typed API via `contextBridge.exposeInMainWorld`:

```typescript
interface ThuisAPI {
  download: {
    start: (streamId: string, outputPath: string) => Promise<string>;  // returns jobId
    cancel: (jobId: string) => Promise<void>;
    onProgress: (callback: (event: DownloadEvent) => void) => void;
  };
  dialog: {
    selectFolder: () => Promise<string | null>;
  };
  app: {
    getVersion: () => Promise<string>;
    showNotification: (title: string, body: string) => Promise<void>;
  };
}
```

#### 5.3.3 Electron Builder Configuration (`electron-builder.yml`)

```yaml
appId: com.thuis.app
productName: Thuis
directories:
  output: dist
  buildResources: build
files:
  - dist/**/*
  - package.json
win:
  target: [nsis, portable]
mac:
  target: [dmg, zip]
linux:
  target: [AppImage, deb]
publish:
  provider: github
  owner: aldofieuw
  repo: thuis
```

---

## 6. Data Models & Store Design

### 6.1 Extended Zod Schemas

Building on the SPEC.md base schemas:

```typescript
// ─── Episode ───
const EpisodeSchema = z.object({
  id: z.string(),                    // VRT objectId
  title: z.string(),
  season: z.number(),
  episode: z.number(),
  episodeCode: z.string(),           // e.g. "s31a6102"
  duration: z.string(),              // e.g. "30 min"
  durationSeconds: z.number().optional(),
  imageUrl: z.string().url().optional(),
  url: z.string().url(),             // Full VRT MAX URL
  description: z.string().optional(),
  available: z.boolean().optional(),
  videoId: z.string().optional(),    // VRT video/pub ID for streaming
});

// ─── Episode Detail (full page view) ───
const EpisodeDetailSchema = EpisodeSchema.extend({
  streamId: z.string(),              // Resolved VRT stream ID
  manifestUrl: z.string().url().optional(), // HLS manifest URL
  downloadUrl: z.string().url().optional(),
  brand: z.string().optional(),
  seasonEpisodes: z.number().optional(),
  nextEpisode: z.object({ id: z.string(), title: z.string() }).optional(),
  previousEpisode: z.object({ id: z.string(), title: z.string() }).optional(),
});

// ─── Download Job ───
const DownloadJobSchema = z.object({
  id: z.string(),
  episodeId: z.string(),
  episodeTitle: z.string(),
  streamId: z.string(),
  status: z.enum(['pending', 'downloading', 'completed', 'failed', 'cancelled']),
  progress: z.number().min(0).max(100).default(0),
  speed: z.string().optional(),      // "2.5 MB/s"
  eta: z.string().optional(),        // "1m 30s"
  error: z.string().optional(),
  outputPath: z.string().optional(),
  createdAt: z.string().datetime(),
  completedAt: z.string().datetime().optional(),
  fileSize: z.number().optional(),   // bytes
});

// ─── Search Result ───
const SearchResultSchema = z.object({
  total: z.number(),
  episodes: z.array(EpisodeSchema),
  hasMore: z.boolean(),
  cursor: z.string().optional(),
});
```

### 6.2 Zustand Store Shape (Combined)

```typescript
interface ThuisStore extends EpisodeSlice, DownloadSlice, UISlice {
  // Hydration
  _hasHydrated: boolean;
}
```

**Persistence**:
- `download-slice` and `ui-slice` persisted to `localStorage` (via Zustand `persist` middleware)
- `episode-slice` is ephemeral (re-fetched on each session)
- Electron additionally persists completed download records to a JSON file in the user data directory

### 6.3 State Transitions

```
Download Job States:
  pending → downloading → completed
         ↘ downloading → failed → pending (retry)
         ↘ downloading → cancelled
         ↘ pending → cancelled
```

---

## 7. API Contracts & Integrations

### 7.1 VRT MAX GraphQL API

**Endpoint**: `https://www.vrt.be/vrtnu-api/graphql/v1`

**Auth**: Bearer token in `Authorization` header (provided via env var `VRT_BEARER_TOKEN`)

#### Queries

**Search Episodes by Title**:
```graphql
# Uses the component query with a base64-encoded componentId
# componentId encodes: { "q": "<search-term>" }
# The response is a PaginatedTileList → EpisodeTile nodes
#
# See SPEC.md adjacent research for full query structure
query component($componentId: ID!, $lazyItemCount: Int = 10, $after: ID) {
  component(id: $componentId) {
    ... on PaginatedTileList {
      title
      paginatedItems(first: $lazyItemCount, after: $after) {
        edges {
          node {
            ... on EpisodeTile {
              title
              description
              image { templateUrl }
              action {
                ... on LinkAction { link }
              }
              primaryMeta { type value }
              secondaryMeta { type value }
            }
          }
        }
      }
    }
  }
}
```

**Variables**:
```json
{
  "componentId": "$byUxNnx8eyJxIjoidGh1aXMifXxuJTI3MDY2JQ==",
  "lazyItemCount": 20
}
```

The `componentId` for a search is derived by base64-encoding a JSON payload. Format needs reverse-engineering but follows: `base64({ q: "<query>" })`.

#### Response Parsing

The GraphQL response returns a deeply nested `PaginatedTileList` → `EpisodeTile[]` structure. The core's `queries.ts` extracts:

| Source Field | Target Field | Notes |
|-------------|-------------|-------|
| `node.title` | `Episode.title` | Direct |
| `node.image.templateUrl` | `Episode.imageUrl` | Template URL — need to substitute width/height |
| `node.action.link` | `Episode.url` | Internal VRT path |
| `node.primaryMeta[type="season"]` | `Episode.season` | Parse from meta items |
| `node.secondaryMeta` | `Episode.duration` | Parse duration text |
| `node.objectId` | `Episode.id` | VRT object ID |

### 7.2 VRT Video Aggregator API

**Endpoint**: `https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/{pubId}`

**Headers**:
```
x-api-key: AIzaSyA8Hx0AErX_cTlihCjMqPvv7OZQSn_QHYI
```

**Response Shape**: Returns a JSON object containing video facets. The `targetUrl` in a facet of type `"hls"` or `"hls_subs"` contains the HLS manifest URL used for downloading.

**Note**: This API endpoint is based on reverse-engineered patterns from the VRT MAX platform. The actual `pubId` is extracted from the GraphQL episode data or derived from the episode URL.

### 7.3 Download Integration (yt-dlp)

**Invocation** (used by `downloader/service.ts`):
```bash
yt-dlp \
  --output "{output_path}/{title}.%(ext)s" \
  --format "bestvideo+bestaudio/best" \
  --merge-output-format mp4 \
  --progress \
  --no-playlist \
  "{manifest_url_or_episode_url}"
```

**Why yt-dlp**:
- Native VRT MAX/BE site support
- Handles HLS segment assembly
- Supports subtitle extraction
- Resume capability
- Progress reporting via `--progress` flag (parsed from stdout)

**Electron Bundling**: yt-dlp binary is bundled per-platform via `electron-builder`'s `extraResources` or downloaded on first launch.

**Fallback**: If yt-dlp is unavailable, a minimal HLS downloader is included in core using native `fetch()` for manifest parsing and segment concatenation. This handles simple cases but lacks yt-dlp's format negotiation.

---

## 8. UI/UX Design Principles

### 8.1 Core Principles

| Principle | Application |
|-----------|-------------|
| **Easy UX** | Minimum clicks from URL → download. One primary action per screen |
| **URL-first** | Paste a VRT MAX URL → app auto-resolves episode info → one click to download |
| **Progressive disclosure** | Search → select → detail → download. Each step reveals more |
| **Status visibility** | Every download has a visible state (queued, active, progress, complete, failed) |
| **Error resilience** | Failed downloads show clear error + retry button; never a blank screen |

### 8.2 MVP Screen Flow

```
┌─────────────────────────────────────────────────────────┐
│  Home / Search Screen                                   │
│  ┌──────────────────────────────────────────┐           │
│  │ 🔍 Search Thuis episodes...              │           │
│  │  Or paste a VRT MAX URL:                 │           │
│  │ ┌──────────────────────────────────────┐ │           │
│  │ │ https://www.vrt.be/vrtmax/a-z/...    │ │           │
│  │ └──────────────────────────────────────┘ │           │
│  │                    [Resolve Episode]      │           │
│  └──────────────────────────────────────────┘           │
│                                                         │
│  Results: (or resolved episode)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │  📺      │ │  📺      │ │  📺      │                │
│  │ S31E6102 │ │ S31E6101 │ │ S31E6100 │                │
│  │ Thuis... │ │ Thuis... │ │ Thuis... │                │
│  │ 30 min   │ │ 30 min   │ │ 30 min   │                │
│  └──────────┘ └──────────┘ └──────────┘                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Episode Detail                                          │
│                                                         │
│  ┌──────────────────────────────────────────┐           │
│  │      📺 Episode Thumbnail                │           │
│  │                                           │           │
│  └──────────────────────────────────────────┘           │
│                                                         │
│  Thuis — S31E6102                                       │
│  "De spanning stijgt"                                    │
│  Season 31 · Episode 6102 · 30 min                      │
│                                                         │
│  [📥 Download Episode]  ← Primary CTA                   │
│                                                         │
│  Description: Lorem ipsum dolor sit amet...              │
│                                                         │
│  ─── Download Queue ───                                 │
│  [████████████░░░░░░] 65% — 2.5 MB/s — 1m 30s           │
│  [                    ] ❌ Cancel                        │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Tailwind 4 Theme

```css
/* Design tokens (conceptual — to be defined) */
:root {
  --color-primary: #0055ff;      /* VRT-inspired blue */
  --color-surface: #ffffff;
  --color-background: #f5f5f7;
  --color-text: #1d1d1f;
  --color-text-secondary: #6e6e73;
  --color-error: #ff3b30;
  --color-success: #34c759;
  --color-download: #007aff;
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
}
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Core Library)

**Goal**: Ship the `@thuis/core` package with GraphQL client, Zod schemas, and Zustand store — testable independently.

| Task | Deliverable | Dependencies |
|------|-------------|-------------|
| 1.1 | Project scaffolding: `tsconfig`, build pipeline, Jest config | None |
| 1.2 | Zod schemas: `Episode`, `DownloadJob`, `SearchResult` | 1.1 |
| 1.3 | GraphQL client: `createClient`, `searchEpisodes`, error handling | 1.2 |
| 1.4 | URL resolver: parse VRT MAX URL → `{ show, season, episode }` | 1.2 |
| 1.5 | Zustand store: all three slices, `persist` middleware | 1.2 |
| 1.6 | VRT GraphQL query reverse-engineering & integration tests | 1.3 |
| 1.7 | Unit tests: schema validation, store transitions, URL parsing | 1.2–1.6 |

**Exit criteria**:
- `pnpm test` passes with ≥80% coverage on core
- `searchEpisodes("thuis")` returns real VRT data
- URL parsing correctly extracts components from `/vrtmax/a-z/thuis/31/thuis-s31a6102/`

### Phase 2: Web App MVP (Search & Browse)

**Goal**: Working web SPA where users can search for Thuis episodes and view details.

| Task | Deliverable | Dependencies |
|------|-------------|-------------|
| 2.1 | Vite + React 19 + Tailwind 4 scaffold | 1.1 |
| 2.2 | Layout: Header, SearchBar, responsive grid shell | 2.1 |
| 2.3 | EpisodeCard + EpisodeGrid components | 2.2, 1.5 |
| 2.4 | SearchPage: connects SearchBar to store | 2.3, 1.5 |
| 2.5 | EpisodeDetail page with URL paste resolution | 2.3, 1.4 |
| 2.6 | DownloadQueue sidebar component | 2.2, 1.5 |
| 2.7 | ErrorBoundary + loading/empty states | 2.2 |
| 2.8 | Playwright E2E tests: search flow, navigation | 2.4–2.7 |

**Exit criteria**:
- User can search, browse episodes, view details
- URL paste → episode resolution works
- Download queue shows in sidebar (download action wired in Phase 3)
- Playwright E2E passes

### Phase 3: Download Engine & Integration

**Goal**: End-to-end working download pipeline from both Web and Electron.

| Task | Deliverable | Dependencies |
|------|-------------|-------------|
| 3.1 | `downloader/service.ts`: yt-dlp wrapper with progress parsing | 1.2 |
| 3.2 | `downloader/resolver.ts`: VRT Video API manifest resolution | 1.3 |
| 3.3 | Download state machine: pending → downloading → complete/fail | 1.5, 3.1 |
| 3.4 | Web download: Streams API / File System Access API integration | 3.2 |
| 3.5 | Electron main process: IPC handlers for download lifecycle | 3.2, 3.3 |
| 3.6 | Electron preload: contextBridge API | 3.5 |
| 3.7 | Electron renderer: reuses web-app components + native dialogs | 2.5, 3.6 |
| 3.8 | Download notifications (Electron: native; Web: toast) | 3.5 |
| 3.9 | Integration tests: full download pipeline (mocked VRT API) | 3.1–3.4 |

**Exit criteria**:
- Web app: user can download an episode via browser (Chromium)
- Electron app: user can download to selected folder
- Progress bar updates in real-time
- Cancel/retry works
- Notifications on completion

### Phase 4: Desktop Production & CI/CD

**Goal**: Polished desktop app with installers, auto-update, and CI/CD pipeline.

| Task | Deliverable | Dependencies |
|------|-------------|-------------|
| 4.1 | `electron-builder.yml`: all platform targets | 3.7 |
| 4.2 | Auto-updater: `electron-updater` with GitHub Releases | 3.7 |
| 4.3 | App icon, metadata, about dialog | 3.7 |
| 4.4 | CI/CD: GitHub Actions (lint → test → build → publish) | 4.1 |
| 4.5 | GitHub Pages deployment config (web-app) | 2.1 |
| 4.6 | Offline cache: IndexedDB (web) / JSON file (Electron) | 1.5 |
| 4.7 | End-to-end Playwright tests (Electron) | 3.7 |

**Exit criteria**:
- GitHub Action produces web build → published to `gh-pages`
- GitHub Action produces Electron installers (Linux AppImage, macOS DMG, Windows NSIS) → published to Releases
- Electron auto-update pulls new version on launch
- Offline mode shows cached episode list

### Phase Dependencies & Timeline

```
Phase 1 (Foundation)
    │
    ▼
Phase 2 (Web App)  ──────┐
    │                     │
    ▼                     ▼
Phase 3 (Download)  ◀────┘
    │
    ▼
Phase 4 (Desktop/CI/CD)
```

**Estimated effort**: 
- Phase 1: 2–3 weeks (heavy research/reverse-engineering)
- Phase 2: 2 weeks
- Phase 3: 2–3 weeks (download pipeline complexity)
- Phase 4: 1–2 weeks

**Total**: ~7–10 weeks for full MVP, ~4 weeks for web-only MVP (Phases 1–2 + basic 3).

---

## 10. Quality & Testing Strategy

### 10.1 Test Pyramid

```
         ╱╲
        ╱ E2E ╲
       ╱ (Playwright) ╲
      ╱─────────────────╲
     ╱  Integration       ╲
    ╱  (Core API mocking)  ╲
   ╱─────────────────────────╲
  ╱      Unit Tests (Jest)      ╲
 ╱  (Schemas, Store, Parsing)     ╲
╱═══════════════════════════════════╲
```

### 10.2 Test Breakdown

| Layer | Tool | Focus | Target |
|-------|------|-------|--------|
| **Unit** | Jest | Zod schema validation, URL parsing, store state transitions, retry logic | ≥80% coverage |
| **Integration** | Jest + nock | GraphQL client (mocked responses), download pipeline (mocked VRT API) | Key workflows |
| **E2E (Web)** | Playwright | Search → browse → detail flow; download queue UI | 3–5 critical paths |
| **E2E (Electron)** | Playwright + electron | Full app lifecycle, IPC communication, native dialog | 2–3 critical paths |

### 10.3 Key Test Scenarios

**Core**:
- `EpisodeSchema.parse(validInput)` → passes with correct shape
- `EpisodeSchema.parse(missingField)` → throws with clear error
- `parseVrtUrl('/vrtmax/a-z/thuis/31/thuis-s31a6102/')` → `{ show: 'thuis', season: 31, episodeCode: 's31a6102' }`
- `parseVrtUrl('invalid-url')` → throws `VrtUrlError`
- Store: `search()` sets `isSearching: true`, then `false` on completion
- Store: `enqueueDownload()` transitions `pending → downloading → completed`

**Web App**:
- SearchBar fires debounced search after 300ms idle
- EpisodeGrid renders correct number of cards
- EpisodeDetail shows all metadata fields
- DownloadProgress shows percentage

**Electron**:
- IPC `download:start` message creates child process
- `download:progress` events update store in real-time
- `download:cancel` kills child process
- Folder picker returns valid path

---

## 11. Deployment Architecture

### 11.1 Web App (Custom Domain)

```mermaid
flowchart LR
  A[Push to main] --> B[GitHub Actions]
  B --> C[Lint & Test]
  C --> D[Build web-app]
  D --> E[Upload to custom domain]
  E --> F[thuis.aldof.duckdns.org]
  F --> G[User Browser]
```

**URL**: `http://thuis.aldof.duckdns.org/`

**Custom domain**: Configured via CNAME in GitHub Pages deployment.

### 11.2 Documentation Site (GitHub Pages)

```mermaid
flowchart LR
  A[Push to main] --> B[GitHub Actions]
  B --> C[Lint & Test]
  C --> D[Build documentation site]
  D --> E[Deploy to gh-pages]
  E --> F[GitHub Pages]
  F --> G[User Browser]
```

**URL**: `https://Aldo-f.github.io/thuis/`

### 11.3 Electron App (GitHub Releases)

```mermaid
flowchart LR
  A[Git Tag v*.*.*] --> B[GitHub Actions]
  B --> C{Lint & Test}
  C --> D[Build Web]
  C --> E[Build Electron]
  D --> F[Deploy to gh-pages]
  E --> G[Package installers]
  G --> H[Upload to GitHub Releases]
  H --> I[User downloads]
  I --> J[Auto-updater checks]
```

### 11.4 CI/CD Pipeline (`.github/workflows/ci.yml`)

```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  release:
    types: [published]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: pnpm install
      - run: pnpm lint
      - run: pnpm test -- --coverage
      - run: pnpm build

  deploy-web:
    needs: quality
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      # ... build web-app → deploy to gh-pages ...

  build-electron:
    needs: quality
    if: startsWith(github.ref, 'refs/tags/v')
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      # ... build Electron → upload to release ...
```

---

## 12. Glossary & References

### 12.1 Glossary

| Term | Definition |
|------|------------|
| **VRT** | Vlaamse Radio- en Televisieomroeporganisatie — Flemish public broadcaster |
| **VRT MAX** | VRT's streaming platform (formerly VRT NU) |
| **GraphQL** | API query language used by VRT MAX |
| **HLS** | HTTP Live Streaming — Apple's streaming protocol used by VRT for video delivery |
| **M3U8** | HLS playlist/manifest file format |
| **yt-dlp** | Command-line video downloader (fork of youtube-dl) with VRT MAX support |
| **EpisodeTile** | GraphQL fragment representing an episode in VRT MAX search results |
| **Container** | In C4: a deployable unit (web app, Electron app, core library) |
| **IPC** | Inter-Process Communication (Electron main ↔ renderer) |
| **contextBridge** | Electron API for safe renderer ↔ main communication |
| **electron-builder** | Packaging tool for cross-platform Electron installers |
| **Zustand** | Minimal state management library for React |
| **Zod** | TypeScript-first schema validation library |

### 12.2 References

| Reference | Purpose |
|-----------|---------|
| `SPEC.md` | Original project specification (v0.1.0) |
| `https://www.vrt.be/vrtnu-api/graphql/v1` | VRT MAX GraphQL API endpoint |
| `https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/` | VRT Video Aggregator API |
| `https://github.com/yt-dlp/yt-dlp` | Video download tool with VRT support |
| [Electron IPC docs](https://www.electronjs.org/docs/latest/tutorial/ipc) | Electron IPC patterns |
| [Zustand docs](https://github.com/pmndrs/zustand) | State management reference |
| [Zod v3 docs](https://zod.dev/) | Schema validation reference |

---

## Appendix A: C4 Element Catalog

| Element | Type | Technology | Description |
|---------|------|-----------|-------------|
| User | Person | - | Thuis fan who downloads episodes |
| Web App | Container (SPA) | React 19, Vite, Tailwind 4 | Responsive browser application |
| Electron App | Container (Desktop) | Electron 31, React 19 | Desktop application |
| Core Library | Container (Library) | TypeScript 5, Zod, Zustand | Shared business logic package |
| GraphQL Client | Component | TypeScript, fetch | VRT MAX API communication |
| Download Service | Component | TypeScript, yt-dlp | Video download orchestration |
| Zustand Store | Component | TypeScript, Zustand | Global reactive state |
| Zod Schemas | Component | TypeScript, Zod | Runtime validation |
| VRT MAX GraphQL | External System | GraphQL | VRT's search/content API |
| VRT Video API | External System | REST | VRT's video streaming infrastructure |
| GitHub | External System | - | Hosting, releases, CI/CD |
| React UI | Component | React 19 | UI component tree |
| Main Process | Component | Electron 31 | OS-level window/process management |
| Preload Script | Component | TypeScript | IPC bridge |

---

---

## Completion Checklist — Infrastructure Phase

- [x] Web-app scaffolded (Vite + React 19 + Tailwind 4)
- [x] CI/CD workflows (GitHub Actions)
- [x] CNAME configured for thuis.aldof.duckdns.org
- [x] Electron-app scaffolded (Electron 31 + electron-builder)
- [x] Dependencies installed and build verified
- [x] Push to GitHub and create repo aldofieuw/thuis — completed
- [x] Configure DNS (thuis.aldof.duckdns.org → GitHub Pages IPs) — completed
- [x] Set GitHub Pages source to GitHub Actions — completed
- [x] Add VRT_BEARER_TOKEN to repo secrets — completed
- [x] Tag release v0.1.0 for Electron publishing — completed

*End of SDD — Version 0.2.0*
