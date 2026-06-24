# Full Project Build — Combined Implementation Plan

## TL;DR

> **Quick Summary**: Complete the entire Thuis application across all three specs (002‑thuis‑web‑downloader, 003‑multi‑provider‑platform, 004‑video‑viewer‑download). The plan delivers a production‑ready multi‑provider video platform with a secure credential vault, provider abstraction, HLS video player, download engine, CI/CD, and Docker deployment.
>
> **Deliverables**:
> - Provider abstraction layer (`ProviderAdapter` interface + `ProviderRegistry`)
> - VRT, VTM GO, and Play.TV adapters (VRT fully implemented, stubs for others)
> - Secure credential vault (master‑password via PBKDF2‑AES‑256‑GCM / Electron safeStorage)
> - Cross‑provider search service
> - Updated React UI (provider cards, credential forms, episode detail, player, download queue)
> - Full test suite (unit, integration, component, E2E with Playwright)
> - Docker deployment (Traefik + nginx)
> - CI pipeline (GitHub Actions)
> - Documentation (Docusaurus on GitHub Pages)
>
> **Estimated Effort**: Large (3‑5 weeks parallel, 2‑3 weeks critical path)
> **Parallel Execution**: YES – 5 waves, 3‑7 tasks per wave
> **Critical Path**: Adapter interface → VRT adapter → Vault → UI wiring → Tests → CI/Deploy

---

## Context

### Project Structure
```
packages/
├── core/src/
│   ├── providers/     NEW – ProviderAdapter, ProviderRegistry, Vrt/Vtmgo/Playtv adapters
│   ├── vault/         NEW – CredentialVault, encryption helpers
│   ├── auth/          EXISTS – VrtAuthService (to be wrapped)
│   ├── episode/       EXISTS – VrtEpisodeService (to be wrapped)
│   ├── download/      EXISTS – StreamResolver (to be wrapped)
│   ├── graphql/       EXISTS – types, queries, client
│   ├── store/         EXISTS – UI/download/episode slices
│   └── __tests__/     EXISTS + MORE
├── web-app/src/
│   ├── components/vault/  EXISTS – ProviderCard, ProviderCredentialForm, etc.
│   ├── hooks/             EXISTS – useVault, useAuth, useEpisode
│   ├── pages/             EXISTS – VaultPage, EpisodeDetail
│   └── services/          NEW – SearchService
└── electron-app/src/
    └── main/              EXISTS – download-engine, tray-manager
```

### Already Implemented (completed in 002)
- VrtAuthService with OIDC login, token refresh, cookie handling
- VrtEpisodeService with VideoPage GraphQL query
- StreamResolver with vualto token acquisition
- FFmpeg download engine in Electron
- HLS.js video player with keyboard controls
- Vault UI (ProviderCard, ProviderCredentialForm, VaultSetupForm, VaultUnlockForm, VaultStatusBadge)
- Master password vault with PBKDF2 + AES-256-GCM on Web
- Electron safeStorage vault
- Download queue UI (shell)
- Docusaurus documentation site
- Docker/Docker Compose for web app
- 23 core unit tests passing

### Already Built (initial work on 003)
- ProviderAdapter interface (basic — needs expansion)
- ProviderRegistry singleton (complete)

### Remaining Work
- Expand ProviderAdapter to include login, search, getEpisode, resolveStream
- Create VrtProviderAdapter wrapping existing services
- Create VtmgoProviderAdapter (stub)
- Create PlaytvProviderAdapter (stub)
- Implement CredentialVault service layer
- Implement cross-provider SearchService
- Update UI components and hooks to use ProviderRegistry
- Full test coverage for all new code
- CI pipeline
- Deployment finalization

---

## Work Objectives

### Core Objective
Deliver a fully functional Thuis application where a user can log in to VRT MAX via a secure master‑password vault, browse episodes, search across multiple providers, stream or download any episode, all with a polished Dutch‑language UI.

### Concrete Deliverables
- Updated `ProviderAdapter` interface (6 methods)
- `VrtProviderAdapter` implementation
- `VtmgoProviderAdapter` and `PlaytvProviderAdapter` stubs
- `CredentialVault` with auto‑lock
- `SearchService` with cross‑provider fan‑out
- Updated `ProviderCard`, `ProviderCredentialForm`, `VaultPage`, `EpisodeDetail`, `DownloadQueue`
- Updated hooks (`useVault`, `useAuth`, `useEpisode`)
- Full test suite (≥80% coverage on new code)
- CI pipeline (lint, typecheck, test, build Docker)
- Updated Docker/Traefik config
- Docusaurus docs

### Must Have
- Multi‑provider abstraction compiles and passes tests with `tsc --noEmit`
- VRT provider works identically to existing code (all existing tests pass)
- Master‑password vault encrypts/decrypts correctly (test vectors)
- UI shows provider cards dynamically from registry
- Cross‑provider search aggregates results
- All error messages in Dutch
- Zero plaintext credentials in storage (verified by grep)

### Must NOT Have (Guardrails)
- No `as any` or `@ts-ignore` in new code
- No Android APK build (postponed)
- No actual VTM GO / Play.TV API reverse‑engineering (stubs only)
- No changes to existing working VRT auth/episode flow logic (only wrapping)

---

## Verification Strategy

### Test Infrastructure
- **Framework**: Jest + ts-jest (ESM mode via `NODE_OPTIONS=--experimental-vm-modules`)
- **Coverage target**: ≥80% on all new `providers/` and `vault/` code
- **Test layers**:
  1. Unit tests: pure logic, mocked HTTP (nock)
  2. Component tests: Playwright for React components
  3. Integration tests: real VRT credentials (VRT_USERNAME/PASSWORD)
  4. Security tests: plaintext detection, encryption round‑trip

### Agent‑Executed QA (mandatory per task)
Every task includes QA scenarios that are run automatically after implementation:
- **UI tasks**: Playwright opens page, fills forms, asserts DOM, captures screenshot
- **Core tasks**: Bash runs `jest`, captures output
- **API/backend tasks**: Bash runs the module, asserts correct behavior

### Manual QA (final verification)
- Full user flow: open app → set master password → configure VRT credentials → search episode → play stream → download → verify file on disk
- URL: `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/`
- Language: all UI Dutch

---

## Execution Strategy

### Parallel Waves

```
Wave 1 (Foundation – start immediately):
├── 1. Expand ProviderAdapter interface
├── 2. Implement CredentialVault
├── 3. Implement PBKDF2-AES-GCM encryption module
├── 4. Create ProviderRegistry tests (existing, flesh out)
├── 5. Update core/index.ts exports
├── 6. Create vault/index.ts with public API
└── 7. Update Dockerfile for vault env vars

Wave 2 (Provider adapters – after Wave 1):
├── 8. Create VrtProviderAdapter wrapping VrtAuthService, VrtEpisodeService, StreamResolver
├── 9. Create VtmgoProviderAdapter (stub with ProviderNotSupportedError)
├── 10. Create PlaytvProviderAdapter (stub with ProviderNotSupportedError)
├── 11. Register all adapters in ProviderRegistry at app startup
├── 12. Add VrtProviderAdapter unit tests
└── 13. Add stub adapter unit tests

Wave 3 (UI & Search – after Wave 2):
├── 14. Implement SearchService with cross-provider fan-out
├── 15. Update ProviderCard to read from registry
├── 16. Update ProviderCredentialForm to use registry
├── 17. Update VaultPage to render cards dynamically
├── 18. Update useVault hook to integrate with CredentialVault service
├── 19. Update useAuth hook to use VrtProviderAdapter
├── 20. Update useEpisode hook to get episode from registry
├── 21. Update EpisodeDetail page to use registry-based stream resolution
├── 22. Update DownloadQueue component to work with registry
└── 23. Add SearchService unit tests

Wave 4 (Integration & Tests – after Wave 3):
├── 24. Write Playwright component tests for UI components
├── 25. Write integration tests (login → search → play → download)
├── 26. Write security tests (ciphertext verification, auto‑lock timings, plaintext grep)
├── 27. Write regression tests (existing VRT flow unchanged)
├── 28. Run performance benchmarks
└── 29. Fix all test failures

Wave 5 (Deploy & Documentation – after Wave 4):
├── 30. Update Docusaurus docs for provider system
├── 31. Finalize Docker/Traefik configuration
├── 32. Set up GitHub Actions CI pipeline
└── 33. Build and verify Docker images

Wave FINAL (Verification):
├── F1. Oracle plan compliance audit
├── F2. Manual QA – full user flow
├── F3. Security audit – plaintext check, vault timing
└── F4. Scope fidelity check – no missing features
```

---

## TODOs

- [x] 1. **Expand ProviderAdapter interface** (`packages/core/src/providers/ProviderAdapter.ts`)

  **What to do**:
  - Add methods: `login(credentials: LoginArgs): Promise<ProviderTokens>`, `search(query: string): Promise<SearchResult[]>`, `getEpisode(url: string): Promise<EpisodeDetail>`, `resolveStream(episode: EpisodeDetail): Promise<StreamData>`
  - Add fields: `id: string`, `displayName: string`, `supportsSearch: boolean`, `supportsAuth: boolean`
  - Create supporting types file `packages/core/src/providers/types.ts` with `LoginArgs`, `ProviderTokens`, `SearchResult`, etc.
  - Ensure `tsc --noEmit` passes

  **Must NOT do**:
  - Do not implement any methods, only define the interface
  - Do not remove existing `name`, `init()`, `dispose()`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Single file modification with clear requirements

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Tasks 8, 9, 10
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] ProviderAdapter interface compiles with 6 methods + 2 properties
  - [ ] Supporting types exist and compile
  - [ ] `tsc --noEmit` passes

  **QA Scenarios**:
  ```
  Scenario: Interface compiles correctly
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `tsc --noEmit` in packages/core
    Expected Result: exit code 0, no TypeScript errors
    Evidence: .omo/evidence/task-1-tsc-pass.txt
  ```

- [x] 2. **Implement CredentialVault service** (`packages/core/src/vault/Vault.ts`)

  **What to do**:
  - Create `CredentialVault` class with methods: `lock()`, `unlock(masterPassword: string)`, `addCredentials(provider: string, email: string, password: string)`, `getCredentials(provider: string)`, `removeCredentials(provider: string)`, `listProviders()`, `isLocked()`
  - Implement auto‑lock timer (configurable, default 5 minutes)
  - Web implementation: store encrypted blob in IndexedDB via a thin wrapper
  - Electron implementation: use `safeStorage` (optional, fallback to IndexedDB)
  - Cache decrypted credentials in memory only; purge on `lock()`
  - All user‑facing errors in Dutch: "Ongeldig hoofdwachtwoord", "Wachtwoord vereist", etc.

  **Must NOT do**:
  - Never write plaintext passwords to any storage (IndexedDB, localStorage, files)
  - Never expose decrypted credentials in logs or error messages

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Complex state management with security requirements

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Tasks 15, 18
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] Vault encrypts and decrypts correctly (round‑trip test with known test vectors)
  - [ ] Wrong master password throws "Ongeldig hoofdwachtwoord"
  - [ ] Auto‑lock fires after configured timeout
  - [ ] All error messages in Dutch

  **QA Scenarios**:
  ```
  Scenario: Encryption round-trip
    Tool: Bash
    Preconditions: None
    Steps:
      1. Create vault with known masterPassword and test credentials
      2. Call addCredentials('vrt', 'user@example.com', 'secret123')
      3. Call getCredentials('vrt')
    Expected Result: { email: 'user@example.com', password: 'secret123' }
    Evidence: .omo/evidence/task-2-roundtrip.txt

  Scenario: Wrong password rejected
    Tool: Bash
    Preconditions: Vault locked with known masterPassword
    Steps:
      1. Call unlock('wrongpassword')
    Expected Result: throws Error with "Ongeldig hoofdwachtwoord"
    Evidence: .omo/evidence/task-2-wrong-pw.txt
  ```

- [x] 3. **Implement PBKDF2‑AES‑GCM encryption module** (`packages/core/src/vault/encryption.ts`)

  **What to do**:
  - Web: Use `crypto.subtle` API with PBKDF2 (600k iterations, SHA‑256) → AES‑256‑GCM key
  - Electron: Use `safeStorage.encryptString()`/`decryptString()` as alternative path
  - Generate random salt (16 bytes) per vault, random IV (12 bytes) per encryption
  - Encrypted payload format: `salt(16) + iv(12) + ciphertext`
  - Export `deriveKey(password, salt)`, `encrypt(key, plaintext)`, `decrypt(key, ciphertext)`

  **Must NOT do**:
  - Do not use synchronous crypto (blocking)
  - Do not hardcode salt or IV values

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Cryptography requires precision and security awareness

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Task 2
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `encrypt(deriveKey(password, salt), plaintext)` produces valid ciphertext
  - [ ] `decrypt` with matching key recovers plaintext
  - [ ] Wrong password fails decryption
  - [ ] 600k PBKDF2 iterations (configurable for tests)

  **QA Scenarios**:
  ```
  Scenario: Derive key and encrypt/decrypt
    Tool: Bash
    Preconditions: None
    Steps:
      1. Call deriveKey('testpassword', randomSalt)
      2. Encrypt known plaintext
      3. Decrypt ciphertext
    Expected Result: decrypted text matches original plaintext
    Evidence: .omo/evidence/task-3-crypto.txt

  Scenario: Wrong key fails
    Tool: Bash
    Preconditions: key1 derived from 'password1', key2 from 'password2'
    Steps:
      1. Encrypt plaintext with key1
      2. Decrypt with key2
    Expected Result: throws or returns garbage (AES-GCM authentication failure)
    Evidence: .omo/evidence/task-3-wrong-key.txt
  ```

- [x] 4. **Flesh out ProviderRegistry tests** (`packages/core/src/__tests__/providers/ProviderRegistry.test.ts`)

  **What to do**:
  - Write tests for: `register()`, `get()`, `getAll()`, `dispose()`
  - Test duplicate registration (should throw or return early)
  - Test disposing adapters
  - Use mock adapters implementing `ProviderAdapter`

  **Must NOT do**:
  - Do not modify `ProviderRegistry` implementation, only add tests

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Standard unit tests

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: None
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] All registry tests pass
  - [ ] `jest --coverage` shows ≥80% coverage on provider code

  **QA Scenarios**:
  ```
  Scenario: Registry unit tests pass
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `jest src/__tests__/providers/ProviderRegistry.test.ts`
    Expected Result: All tests pass, exit 0
    Evidence: .omo/evidence/task-4-registry-tests.txt
  ```

- [x] 5. **Update core/index.ts exports** (`packages/core/src/index.ts`)

  **What to do**:
  - Export all new provider types, interfaces, classes
  - Export vault classes and encryption utilities
  - Ensure existing exports remain unchanged

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple export updates

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Tasks 15-22
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] All new modules are importable via `@thuis/core`
  - [ ] `tsc --noEmit` passes

- [x] 6. **Create vault/index.ts with public API** (`packages/core/src/vault/index.ts`)

  **What to do**:
  - Create barrel export for vault module
  - Export `CredentialVault`, `deriveKey`, `encrypt`, `decrypt`, `createEmptyVault`, `VaultError`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple barrel file

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Task 2, 5
  - **Blocked By**: None

- [x] 7. **Update Dockerfile for vault env vars** (`Dockerfile`, `packages/web-app/Dockerfile`)

  **What to do**:
  - Add `ENV MASTER_PASSWORD` build arg
  - Add startup script that initializes vault from env var
  - Document usage in `docker-compose.yml`

  **Must NOT do**:
  - Do not store default password in Dockerfile

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple Dockerfile edits

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1)
  - **Blocks**: Wave 5
  - **Blocked By**: None

- [x] 8. **Create VrtProviderAdapter** (`packages/core/src/providers/vrt/VrtProviderAdapter.ts`)

  **What to do**:
  - Create class `VrtProviderAdapter` implementing expanded `ProviderAdapter`
  - Set `id = 'vrt'`, `displayName = 'VRT MAX'`, `supportsSearch = true`, `supportsAuth = true`
  - `login(credentials)`: wrap `VrtAuthService.login()` using provided email/password
  - `search(query)`: wrap existing search logic (PaginatedTileList query)
  - `getEpisode(url)`: wrap `VrtEpisodeService.getEpisode()` using the episode URL
  - `resolveStream(episode)`: wrap `StreamResolver.resolveStream()` using the streamId
  - `init()`: create instances of `VrtAuthService`, `VrtEpisodeService`, `StreamResolver`
  - `dispose()`: clean up any resources
  - Import all necessary types from existing modules

  **Must NOT do**:
  - Do not modify VrtAuthService, VrtEpisodeService, or StreamResolver implementation
  - Do not duplicate business logic — delegate to existing services

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Requires thorough understanding of existing services

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Tasks 14, 19, 20, 21, 22
  - **Blocked By**: Task 1 (expanded interface)

  **Acceptance Criteria**:
  - [ ] VrtProviderAdapter implements ProviderAdapter fully
  - [ ] `getAll()` includes VRT adapter
  - [ ] All existing VRT unit tests still pass
  - [ ] `tsc --noEmit` passes

  **QA Scenarios**:
  ```
  Scenario: VRT adapter registered and retrievable
    Tool: Bash
    Preconditions: Adapter created and registered
    Steps:
      1. Call ProviderRegistry.get('vrt')
    Expected Result: returns VrtProviderAdapter instance
    Evidence: .omo/evidence/task-8-registered.txt

  Scenario: Existing VRT tests still pass
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `jest src/__tests__/auth/VrtAuthService.test.ts`
      2. Run `jest src/__tests__/episode/VrtEpisodeService.test.ts`
      3. Run `jest src/__tests__/download/StreamResolver.test.ts`
    Expected Result: All pass, 23 tests passing
    Evidence: .omo/evidence/task-8-vrt-tests.txt
  ```

- [x] 9. **Create VtmgoProviderAdapter stub** (`packages/core/src/providers/vtmgo/VtmgoProviderAdapter.ts`)

  **What to do**:
  - Create class `VtmgoProviderAdapter` implementing `ProviderAdapter`
  - Set `id = 'vtmgo'`, `displayName = 'VTM GO'`, `supportsSearch = false`, `supportsAuth = false`
  - All methods throw `ProviderNotSupportedError` with Dutch message "VTM GO wordt nog niet ondersteund"
  - `init()`: no-op or log
  - `dispose()`: no-op

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple stub implementation

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Tasks 14, 22
  - **Blocked By**: Task 1 (expanded interface)

  **Acceptance Criteria**:
  - [ ] VtmgoProviderAdapter implements ProviderAdapter
  - [ ] `getAll()` returns it
  - [ ] All methods throw `ProviderNotSupportedError`
  - [ ] Unit test confirms error behavior

- [x] 10. **Create PlaytvProviderAdapter stub** (`packages/core/src/providers/playtv/PlaytvProviderAdapter.ts`)

  **What to do**:
  - Same structure as VTM GO stub
  - Set `id = 'playtv'`, `displayName = 'Play.TV'`, `supportsSearch = false`, `supportsAuth = false`
  - Dutch error: "Play.TV wordt nog niet ondersteund"

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple stub

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Tasks 14, 22
  - **Blocked By**: Task 1

- [x] 11. **Register all adapters at app startup** (`packages/core/src/provider-setup.ts`)

  **What to do**:
  - Create initialization module that discovers and registers all adapters
  - Register VRT, VTM GO, Play.TV adapters on app startup
  - Export `initializeProviders()` function called at app boot

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple wiring

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Tasks 15-22
  - **Blocked By**: Tasks 8, 9, 10

- [x] 12. **Add VrtProviderAdapter unit tests** (`packages/core/src/__tests__/providers/VrtProviderAdapter.test.ts`)

  **What to do**:
  - Mock underlying services (VrtAuthService, VrtEpisodeService, StreamResolver)
  - Test: `login()` calls `VrtAuthService.login()` with correct credentials
  - Test: `getEpisode()` calls `VrtEpisodeService.getEpisode()` with correct URL
  - Test: `resolveStream()` calls `StreamResolver.resolveStream()` with correct streamId
  - Test: `search()` returns search results

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Standard unit tests with mocking

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 8

- [x] 13. **Add stub adapter unit tests** (`packages/core/src/__tests__/providers/StubAdapter.test.ts`)

  **What to do**:
  - Test that VTM GO and Play.TV stubs throw `ProviderNotSupportedError`
  - Test that they appear in `ProviderRegistry.getAll()`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple tests

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 2)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 9, 10

- [x] 14. **Implement SearchService** (`packages/web-app/src/services/SearchService.ts`)

  **What to do**:
  - Create class `SearchService` with method `search(query: string): Promise<SearchResult[]>`
  - Iterate over `ProviderRegistry.getActiveProviders()`
  - For each provider with `supportsSearch: true`, call `provider.search(query)`
  - Aggregate results with `provider` field identifying the source
  - Handle partial failures: if one provider fails, return results from remaining providers
  - Return typed results with episode metadata

  **Must NOT do**:
  - Do not block on failed providers (use `Promise.allSettled`)
  - Do not expose raw provider errors to user

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Aggregation logic with error handling

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 8, 9, 10

  **Acceptance Criteria**:
  - [ ] Search fans out to all registered providers
  - [ ] Results include `provider` field
  - [ ] Partial failure returns partial results
  - [ ] Tests cover happy and error paths

- [x] 15. **Update ProviderCard to read from registry** (`packages/web-app/src/components/vault/ProviderCard.tsx`)

  **What to do**:
  - Replace hardcoded VRT card with dynamic card reading from `ProviderRegistry.getAll()`
  - Display adapter `displayName`, `id`, `supportsAuth` state
  - Show "Geconfigureerd" badge if credentials exist for that provider
  - Show "Niet ondersteund" for stub adapters
  - Use Dutch labels for all UI text

  **Must NOT do**:
  - Do not break existing VRT card styling or behavior
  - Do not hardcode provider list

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: React UI component with dynamic content

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Task 17
  - **Blocked By**: Tasks 8, 11

- [x] 16. **Update ProviderCredentialForm to use registry** (`packages/web-app/src/components/vault/ProviderCredentialForm.tsx`)

  **What to do**:
  - Pass provider adapter to form so it knows which provider to configure
  - On submit: call adapter's `login()` with email/password to verify credentials
  - On success: store credentials via `CredentialVault.addCredentials()`
  - Show Dutch error messages on failure
  - Disable form for stub adapters (show "Niet ondersteund")

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: React form with integration logic

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Task 17
  - **Blocked By**: Tasks 2, 8, 11

- [x] 17. **Update VaultPage to render cards dynamically** (`packages/web-app/src/pages/VaultPage.tsx`)

  **What to do**:
  - Fetch `ProviderRegistry.getAll()` and render a card for each adapter
  - Handle empty state (no providers registered)
  - Show loading state while providers initialize
  - Show lock/unlock state from CredentialVault

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: React page component

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 15, 16

- [x] 18. **Update useVault hook** (`packages/web-app/src/hooks/useVault.ts`)

  **What to do**:
  - Integrate with `CredentialVault` service from core
  - Expose: `isLocked`, `lock()`, `unlock()`, `providers`, `addCredentials()`, `getCredentials()`
  - Auto-sync with registry: when providers are registered, check vault for stored credentials
  - Keep existing API surface stable

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Hook wiring

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Tasks 17, 19, 20
  - **Blocked By**: Tasks 2, 11

- [x] 19. **Update useAuth hook** (`packages/web-app/src/hooks/useAuth.ts`)

  **What to do**:
  - Replace direct `VrtAuthService` import with `ProviderRegistry.get('vrt').login()`
  - Keep same return type and interface
  - Handle case where VRT adapter isn't registered

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Hook refactoring

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 8, 11

- [x] 20. **Update useEpisode hook** (`packages/web-app/src/hooks/useEpisode.ts`)

  **What to do**:
  - Replace direct `VrtEpisodeService` import with `ProviderRegistry.get('vrt').getEpisode()`
  - Keep same return type and interface
  - Handle adapter not found case

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Hook refactoring

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Task 21
  - **Blocked By**: Tasks 8, 11

- [x] 21. **Update EpisodeDetail page for registry-based resolution** (`packages/web-app/src/pages/EpisodeDetail.tsx`)

  **What to do**:
  - Use provider adapter's `resolveStream()` instead of direct `StreamResolver` import
  - Fetch credentials from vault before stream resolution
  - Show provider name in metadata section
  - Support "Show technical details" that reveals HLS URL
  - All error messages in Dutch

  **Must NOT do**:
  - Do not break existing HLS.js player integration
  - Do not change keyboard shortcuts

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: React page with multiple integrations

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 8, 18, 20

- [x] 22. **Update DownloadQueue for registry** (`packages/web-app/src/pages/DownloadQueuePage.tsx`)

  **What to do**:
  - Use `ProviderRegistry` to resolve streams for queued episodes
  - Show provider icon/name per download item
  - Keep existing pause/resume/cancel behavior

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: React component refactoring

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Tasks 8, 11

- [x] 23. **Add SearchService unit tests** (`packages/web-app/src/__tests__/services/SearchService.test.ts`)

  **What to do**:
  - Mock 2-3 providers with controlled behaviors
  - Test happy path: all providers return results
  - Test partial failure: one provider fails
  - Test empty results
  - Test provider filtering based on `supportsSearch`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Unit tests

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3)
  - **Blocks**: Wave 4
  - **Blocked By**: Task 14

- [x] 24. **Write Playwright component tests** (`packages/web-app/src/__tests__/components/`)

  **What to do**:
  - Test ProviderCard: renders dynamic provider cards from registry
  - Test ProviderCredentialForm: submits credentials, validates inputs, shows Dutch errors
  - Test EpisodeDetail: loads episode metadata, renders player
  - Test DownloadQueue: add/remove items, progress display
  - Test vault lock/unlock flow

  **Must NOT do**:
  - Do not test against real VRT API (mock all HTTP)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`
  - **Reason**: Playwright testing requires UI interaction

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 4)
  - **Blocks**: Task 29
  - **Blocked By**: Tasks 15-22

- [x] 25. **Write integration tests** (`packages/core/src/__tests__/integration/provider-flow.test.ts`)

  **What to do**:
  - End-to-end test: register VRT adapter → login with mock credentials → fetch episode → resolve stream
  - Use nock to mock all HTTP calls
  - Test vault integration: encrypt credentials, unlock, use for auth
  - Test with `VRT_USERNAME`/`VRT_PASSWORD` env vars (excluded from CI)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Complex multi-step integration flow

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 4)
  - **Blocks**: Task 29
  - **Blocked By**: Tasks 8, 12, 18

- [x] 26. **Write security tests** (`packages/core/src/__tests__/security/vault-security.test.ts`)

  **What to do**:
  - Verify encryption round-trip with known test vectors
  - Verify auto-lock timing (±500ms tolerance)
  - Verify plaintext password never appears in logs (test with custom logger)
  - Verify `lock()` purges decrypted data from memory

  **Must NOT do**:
  - Do not run these tests in CI with real credentials

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Focused security tests

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 4)
  - **Blocks**: Task 29
  - **Blocked By**: Tasks 2, 3

- [x] 27. **Write regression tests** (`packages/core/src/__tests__/regression/provider-regression.test.ts`)

  **What to do**:
  - Ensure existing VRT flow works identically after refactoring
  - Compare: direct VrtAuthService.login() vs VrtProviderAdapter.login()
  - Compare: direct VrtEpisodeService.getEpisode() vs VrtProviderAdapter.getEpisode()
  - Compare: direct StreamResolver.resolveStream() vs VrtProviderAdapter.resolveStream()

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Comparison-based tests

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 4)
  - **Blocks**: Task 29
  - **Blocked By**: Tasks 8, 12

- [x] 28. **Run performance benchmarks** (`packages/core/src/__tests__/performance/provider-benchmark.test.ts`)

  **What to do**:
  - Measure: login latency (VRT adapter vs direct)
  - Measure: search latency with 3 providers (mocked network)
  - Measure: episode fetch latency
  - Measure: stream resolution latency
  - Log results (not enforced as pass/fail)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Measurement-based

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 4)
  - **Blocks**: None
  - **Blocked By**: Tasks 8, 14

- [~] 29. **Fix all test failures**

  **What to do**:
  - Run full test suite: `NODE_OPTIONS=--experimental-vm-modules pnpm --filter @thuis/core test`
  - Run Playwright tests: `pnpm --filter @thuis/web-app test`
  - Fix any failures found
  - Ensure all 23 original tests still pass + new tests

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`
  - **Reason**: Debugging and fixing failures

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential fix)
  - **Blocks**: Wave 5
  - **Blocked By**: Tasks 24-28

---

- [x] 30. **Update Docusaurus docs** (`docs/`)

  **What to do**:
  - Document ProviderAdapter interface and how to add new providers
  - Document CredentialVault architecture and security model
  - Document SearchService
  - Update Getting Started guide with multi-provider setup
  - Update API reference

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: `[]`
  - **Reason**: Technical documentation

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 5)
  - **Blocks**: None
  - **Blocked By**: Task 29

- [x] 31. **Finalize Docker/Traefik configuration** (`docker-compose.yml`, `nginx.conf`, `traefik.yml`)

  **What to do**:
  - Verify multi-stage Dockerfile builds
  - Ensure `MASTER_PASSWORD` env var is passed correctly
  - Test nginx reverse proxy for HLS streaming (CORS headers)
  - Verify `thuis.aldof.duckdns.org` routing works

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: DevOps configuration

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 5)
  - **Blocks**: Task 33
  - **Blocked By**: Task 29

- [x] 32. **Set up GitHub Actions CI** (`.github/workflows/ci.yml`)

  **What to do**:
  - Add workflow for: lint → typecheck → test → build → Docker
  - Cache node_modules with pnpm store
  - Run on push to `v4/main` and PRs
  - Exclude integration tests from CI (require real credentials)
  - Add coverage reporting

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: CI configuration

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 5)
  - **Blocks**: None
  - **Blocked By**: Task 29

- [~] 33. **Build and verify Docker images**

  **What to do**:
  - Build web app Docker image: `docker build -t thuis-web -f packages/web-app/Dockerfile .`
  - Verify container starts: `docker run --rm thuis-web`
  - Verify health endpoint responds
  - Push to registry if configured

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Docker build verification

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 5)
  - **Blocks**: Final Verification
  - **Blocked By**: Tasks 29, 31

---

## Final Verification Wave

- [~] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end‑to‑end. Verify all "Must Have" implemented, all "Must NOT Have" absent. Check evidence files exist.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | VERDICT: APPROVE/REJECT`

- [~] F2. **Manual QA – Full User Flow** — `unspecified-high` (+ playwright skill)
  Start from clean state. Execute complete user workflow: set master password, configure VRT credentials, search episode, play stream, download. Take screenshots at each step.
  URL: `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/`
  Output: `Steps [N/N pass] | Evidence path | VERDICT`

- [~] F3. **Security Audit** — `unspecified-high`
  Grep codebase for plaintext passwords (`grep -r "plaintext\|password.*string" --include="*.ts" --include="*.tsx" packages/`). Verify encryption round‑trip with test vectors. Verify auto‑lock timeout works.
  Output: `Plaintext [CLEAN/N issues] | Vault [PASS/FAIL] | VERDICT`

- [~] F4. **Scope Fidelity Check** — `deep`
  For each task, verify implementation matches spec requirements (specs/002, 003, 004). No feature creep. No missing features.
  Output: `Tasks [N/N compliant] | VERDICT`

---

## Commit Strategy

- **1**: `feat(providers): expand ProviderAdapter interface with login/search/getEpisode/resolveStream`
- **2**: `feat(vault): implement CredentialVault with PBKDF2-AES-GCM encryption`
- **3**: `feat(providers): implement VrtProviderAdapter wrapping existing services`
- **4**: `feat(providers): add VTM GO and Play.TV stub adapters`
- **5**: `feat(search): implement cross-provider SearchService`
- **6**: `feat(ui): update vault UI and hooks to use ProviderRegistry`
- **7**: `feat(ui): update episode detail page and download queue for multi-provider`
- **8**: `test(providers): unit and integration tests for adapter system`
- **9**: `test(vault): encryption round-trip and security tests`
- **10**: `ci: add GitHub Actions workflow`
- **11**: `docs: update documentation for multi-provider system`
- **12**: `deploy: finalize Docker/Traefik configuration`

---

## Success Criteria

- All tests pass: `NODE_OPTIONS=--experimental-vm-modules pnpm --filter @thuis/core test`
- TypeScript compilation: `tsc --noEmit` passes across all packages
- Lint: `pnpm lint` passes
- Coverage: ≥80% for `providers/` and `vault/`
- Manual QA: full flow works end‑to‑end with live VRT credentials
- Security: zero plaintext passwords in storage (verified by grep)
- Docker: `docker-compose up` serves the app at the configured domain
- Docs: Docusaurus builds and deploys cleanly
