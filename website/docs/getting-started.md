---
id: getting-started
title: Getting Started
sidebar_position: 2
---

# Getting Started

This guide shows you how to run Thuis v5 — a unified platform for watching and downloading Flemish TV content from VRT MAX (with VTM GO and Play.TV coming soon).

## What's Available Now

Thuis is a **React + TypeScript** monorepo with:

| Platform | Tech Stack | Status |
|----------|------------|--------|
| **Web App** | Vite + React 19 + Tailwind 4 + HLS.js | ✅ Production — `https://thuis.aldof.duckdns.org` |
| **Electron Desktop** | Electron 31 + FFmpeg | ✅ Production — Win/Lin/Mac installers |
| **Docs** | Docusaurus | ✅ Production — `https://aldo-f.github.io/thuis/` |

**Coming later:**
- **APK** (React Native Android) — postponed, separate native stack

## Prerequisites

- **Node.js** ≥ 20.x
- **pnpm** ≥ 10.x
- **FFmpeg** (for Electron download engine)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: `winget install ffmpeg`

## Installation

```bash
git clone https://github.com/Aldo-f/thuis.git
cd thuis
pnpm install
```

## Development

### Web App (Development Server)

```bash
pnpm dev
```

Serves the web app at `http://localhost:5173`.

### Electron App (Development)

Make sure the web dev server is running (`pnpm dev`), then:

```bash
pnpm electron-dev
```

Or build for your current OS:

```bash
pnpm electron-build
```

### Documentation Site

```bash
cd website
pnpm install
pnpm start
```

Available at `http://localhost:3000`.

## First-Time Setup (Vault)

### Registering a New Provider

To add a custom provider, implement the `ProviderAdapter` interface and register it in `packages/core/src/providers/index.ts`. Once the adapter is compiled, it will be discovered automatically by the `SearchService`. The UI will show the new provider in the **Add Provider** dialog.

### Configuring the Vault

After registering a provider, you may need to store its credentials:

1. Open the **Settings** page.
2. Select the newly added provider from the list.
3. Click **Configure Credentials** and enter the required fields (e.g., API key, username/password).
4. Save – the credentials are encrypted with the master password and stored securely.

The vault will auto‑lock after 5 minutes of inactivity; you will be prompted to re‑enter the master password when needed.

## First-Time Setup (Vault)

On first launch, you'll see the **Vault Setup** screen where you create a master password.

> **⚠️ Warning:** This master password cannot be recovered if forgotten. All provider credentials will be permanently lost.

After setup, add your **VRT MAX** credentials:
- Email + password
- Stored encrypted via OS keychain (Electron) or `crypto.subtle` + IndexedDB (Web)

## Usage

1. **Watch directly:** Click an episode → HLS.js player opens → play/pause/seek/fullscreen with keyboard shortcuts.
2. **Download:** Click the download button → FFmpeg downloads MP4 (Electron only). Web users get the HLS URL for manual use.
3. **Multi-provider:** Future VTM GO/Play.TV support — one vault, all your Flemish TV.

## Deployment

### Web App

```bash
pnpm build:web
```

Output in `packages/web-app/dist/`. Deploy to your server (the provided `nginx.conf` works with Docker/Traefik).

### Electron

```bash
pnpm build:electron
```

Outputs `.exe`, `.deb`, `.AppImage`, `.dmg` in `dist/`. Upload to GitHub Releases.

### Docs

```bash
cd website && pnpm build
```

Output in `website/build/`. Deploy to GitHub Pages.

## Architecture

```
packages/
├── core/              # Shared TypeScript (auth, episode, download, types)
├── web-app/           # React SPA (Vite + Tailwind + HLS.js)
├── electron-app/      # Desktop wrapper (Electron + FFmpeg)
└── website/           # Docusaurus docs
```

## CI/CD

- **Lint** → **Test** → **Build** → **Deploy** pipeline in `.github/workflows/`.
- Integration tests require `VRT_USERNAME`/`VRT_PASSWORD` — run manually for end-to-end validation.

## Next Steps

- Read the [Architecture docs](architecture.md) for backend details.
- Explore the [Usage guide](usage.md) for video watching and downloads.
- Explore the [Architecture](architecture.md) page for technical details.
