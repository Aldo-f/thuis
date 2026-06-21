# SPEC: Thuis-V2 – VRT MAX Content Monitor

**Version**: 0.1.0
**Status**: Draft
**Author**: Aldo Fieuw

---

## 1. Project Overview

Thuis-V2 is a modular ecosystem designed to monitor and manage media references from VRT MAX, specifically focusing on the "Thuis" series.

| Build | Description |
|-------|-------------|
| **Electron Desktop** | Desktop application (Linux/macOS/Windows) using Electron 31 + Vite + React. |
| **Web App** | Responsive SPA using Vite + React 19, served via GitHub Pages. |
| **Core Library** | Shared `pnpm` package providing VRT-API clients, typed data models (Zod), and shared state (Zustand). |
| **CI/CD** | GitHub Actions for automated linting, testing, and deployment. |

---

## 2. Domain & Scope

**Primary Domain**: `CONTENT-MONITORING` – fetching, enriching, and displaying media references from VRT MAX.

**Boundaries**
- **In Scope**: Electron renderer, React frontend, core library logic.
- **Out of Scope**: VRT-API backend logic, GitHub Pages infrastructure, OS-level distribution.

---

## 3. Architectural Vision

- **Monorepo (pnpm Workspaces)**: Code organized into `packages/*` for maximum reuse.
- **Single Point of Truth**: The `core` package is the only source of data fetching and business logic.
- **Strict Type Safety**: All I/O validated via Zod schemas.
- **State Isolation**: Shared Zustand state layer used across both Electron and Web.
- **TDD / Spec-First**: Architecture defined in `SPEC.md` and `specs/` before implementation.

---

## 4. Technology Stack

| Layer | Technology | Version | Notes |
|-------|-------------|---------|-------|
| **Runtime** | Node.js | 20 | ESM-only, ES2022 target |
| **Frontend** | React | 19 | React 19 (Experimental/Latest) |
| **State** | Zustand | 4.5 | Minimal state management |
| **Validation** | Zod | 3.23 | Runtime type validation |
| **API** | VRT GraphQL | 1.x | Auth via Bearer token |
| **Packaging** | electron-builder | 24 | Multi-platform installers |
| **Testing** | Jest / Playwright | | Unit + E2E tests |
| **CI/CD** | GitHub Actions | | Deployment to GH Pages & Releases |

---

## 5. Feature Highlights

| Feature | Priority | Description |
|---------|----------|-------------|
| **VRT-Search** | P1 | GraphQL search on `title` and `season`. |
| **Content Display** | P1 | Display episode metadata (duration, title, images). |
| **Download Queue** | P2 | Persistent queue for media downloads. |
| **Offline Cache** | P2 | Metadata cached via IndexedDB / localStorage. |
| **Responsive UI** | P1 | Tailwind 4 mobile-first design. |
| **CI Build** | P1 | Automated Electron & Web publishing. |

---

## 6. Data Model

```ts
// Episode Model
const EpisodeSchema = z.object({
  id: z.string(),
  title: z.string(),
  season: z.number(),
  episode: z.number(),
  duration: z.string(),
  imageUrl: z.string().url().optional(),
  url: z.string().url(),
});

// Download Job
const DownloadJobSchema = z.object({
  id: z.string(),
  episodeId: z.string(),
  status: z.enum(['pending', 'downloading', 'completed', 'failed']),
  progress: z.number().min(0).max(100),
});
```

---

## 7. Integration Points

1. **VRT API**: Consumed via GraphQL; Auth token provided via environment variable.
2. **Electron IPC**: Secure communication between main and renderer via context bridge.
3. **GitHub Pages**: Static web assets hosted on GitHub.
4. **GitHub Releases**: Binary installers hosted on GitHub.

---

## 8. Quality & Testing Strategy

- **Unit Testing**: Jest for business logic. Target 80% coverage.
- **Integration Testing**: Playwright for both Electron and Browser environments.
- **Spec-Driven**: Implementation strictly follows `.specify/tasks/*.md`.

---

## 9. CI/CD Pipeline

Implemented in `.github/workflows/build.yml`:
- **Pipeline**: Lint $\rightarrow$ Test $\rightarrow$ Build $\rightarrow$ Publish.
- **Targets**: `gh-pages` (Web) and `release` (Electron).

---

## 10. Security & Secrets

- **Secret Management**: No secrets in repo. Tokens provided via GitHub Secrets.
- **VRT Token**: `VRT_BEARER_TOKEN` used for GraphQL requests.
- **Electron Signing**: Certificates managed via environment variables during build.

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **VRT-API** | Official VRT Max GraphQL endpoint. |
| **Zod** | Schema validation library for TypeScript. |
| **TDD** | Test-Driven Development. |
| **DRY** | Don't Repeat Yourself (shared core). |
