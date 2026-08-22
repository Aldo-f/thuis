---
id: architecture
title: System Architecture
sidebar_position: 3
---

# System Architecture

Thuis v5 relies on a clean, layered C4-inspired architecture separating shared business logic, UI renderers, and native shell execution.

## Monorepo Layout

```
thuis/
├── packages/
│   ├── core/           # @thuis/core (Shared business logic, schemas, Zustand store)
│   ├── web-app/        # @thuis/web-app (React 19, Vite, Tailwind 4 SPA)
│   └── electron-app/   # @thuis/electron-app (Electron 31 desktop wrapper)
└── website/            # Docusaurus documentation portal
```

## @thuis/core Architecture

The core package contains:
- **GraphQL Client (`src/graphql/`)**: Direct, type-safe API communication with `https://www.vrt.be/vrtnu-api/graphql/v1` via custom queries and schema validations.
- **Zod Schemas (`src/types/`)**: Central validation definitions for `Episode`, `EpisodeDetail`, and `DownloadJob`.
- **URL Resolver (`src/url-resolver.ts`)**: Pure parsing utility for resolving incoming VRT MAX URLs.
- **Zustand Store (`src/store/`)**: Combined modular slices for episode search, active downloads, and UI configuration, leveraging top-level localStorage persistence.
