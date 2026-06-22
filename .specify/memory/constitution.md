# Thuis-V2 Constitution

## Core Principles

### I. Monorepo Structure
The project uses pnpm workspaces with 3 packages: `core` (shared logic), `web-app` (React SPA), `electron-app` (desktop wrapper). All code lives in `packages/*`. No code outside these directories.

### II. Core-Only Business Logic
All data fetching, authentication, state management, and business logic lives in `@thuis/core`. The `web-app` and `electron-app` packages are thin consumers — they render UI and delegate to core. Core must never import from web-app or electron-app.

### III. Type Safety First
All I/O boundaries (API responses, storage, IPC) MUST be validated with Zod schemas. No `as any` casts. No `@ts-ignore` or `@ts-expect-error`. TypeScript strict mode is enforced.

### IV. TDD / Spec-First (NON-NEGOTIABLE)
Tests are written before implementation. Every feature starts as a spec in `.specify/specs/`. Implementation follows the spec-derived task list. Tests must fail before implementation begins (Red-Green-Refactor).

### V. Dutch User-Facing Language
All user-facing strings (UI text, error messages, notifications) MUST be in Dutch. Logs, code comments, variable names, and internal documentation can be in English.

### VI. Provider Abstraction
All video providers implement the `ProviderAdapter` interface. Core code must never import provider-specific modules directly — always go through `ProviderRegistry`.

### VII. Build Target Separation
There are exactly 3 consumer packages:
- `packages/web-app` — React SPA (Vite + HLS.js + crypto.subtle vault)
- `packages/electron-app` — Electron wrapper (shares web UI + FFmpeg + safeStorage)
- `packages/mobile-app` — React Native for Android (ExoPlayer + Keystore + DownloadManager)

All three consume `@thuis/core` which is platform-agnostic TypeScript. No platform-specific code in core.

### VIII. One Master Password
A single master password protects all stored provider credentials. On first run, the user creates this password. No recovery is possible if forgotten. On Electron, `safeStorage` can replace the master password as a convenience mode.

### IX. Offline Resilience
The app must function offline for browsing cached metadata and playing/downloaded episodes. Network-dependent features (search, stream, login) must degrade gracefully with clear Dutch messages. No crashes in offline mode.

### X. API Change Resilience
Provider APIs can change without notice. All API responses are Zod-validated. On validation failure, the app must:
1. Log the full response for debugging
2. Show a Dutch error message to the user
3. Never crash or leave the user in a broken state

## Security Requirements

### Credential Storage
- Never store plaintext passwords in any persistent storage (files, IndexedDB, localStorage, env files).
- Electron: use `safeStorage` (OS keychain) for credential encryption.
- Web: use `crypto.subtle` (PBKDF2 + AES-256-GCM) with IndexedDB storage.
- Decrypted credentials exist in process memory only, never serialized to disk.

### Token Handling
- Access tokens and video tokens are ephemeral (held in memory, not persisted beyond session).
- Refresh tokens may be persisted (encrypted) for session recovery.
- Tokens must be checked for expiry before use; auto-refresh within 5-minute window.

### Network Security
- All API calls use HTTPS. HTTP is never used.
- No API keys or secrets in client-side code or Git history.
- JWT signing keys for playerInfo are considered "public" (extracted from client-side JS) but should be treated as change-prone.

## Testing Requirements

### Coverage Targets
- Core package: 80% branch coverage minimum.
- Web/Electron packages: Component tests for all interactive UI states.
- Integration tests: excluded from CI (require real credentials), run manually before release.

### Test Layers (from bottom up)
1. **Unit tests** (Jest): Pure logic, HTTP mocked with nock. No real API calls.
2. **Component tests** (Playwright): React components rendered in isolation with mocked data.
3. **Integration tests** (Jest): Real credentials, real network calls. Skipped in CI.
4. **E2E tests** (Playwright): Full browser flow. Runs manually.

### Test File Convention
- Unit tests: `src/**/__tests__/*.test.ts` (co-located with source)
- Integration tests: `src/__tests__/integration/*.test.ts`
- Component tests: `src/**/__tests__/*.test.tsx` or Playwright spec files

## Governance
- SPEC.md is the authoritative project specification. All implementation specs in `.specify/specs/` derive from it.
- SPEC.md version bumps require agreement between all contributors.
- Constitution changes require documentation of the change, rationale, and migration plan.
- All PRs must verify TDD compliance: tests exist, tests fail before implementation, tests pass after.
- Complexity must be justified: if a solution feels complex, challenge it with a simpler alternative first.
- DRM circumvention is explicitly out of scope. DRM-protected content is detected and reported, not decoded.

**Version**: 1.0.0 | **Ratified**: 2026-06-22 | **Last Amended**: 2026-06-22
