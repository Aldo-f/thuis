# Feature Specification: Multi-Provider Platform & Secure Credential Vault

**Feature Branch**: `003-multi-provider-platform`

**Created**: 2026-06-22

**Status**: Draft

**Input**: SPEC.md v0.2.0 sections 8, 9, 15

---

## User Scenarios & Testing

### User Story 1 — Provider Adapter Interface (Priority: P1)

As a developer, I want a common `ProviderAdapter` interface so that new video providers can be plugged in without modifying core logic.

**Why this priority**: The interface is the foundation for all provider integration. Without it, each provider would need bespoke code.

**Independent Test**: Verify that a mock provider implementing `ProviderAdapter` can be registered, discovered, and used for search/resolve through the `ProviderRegistry` without any provider-specific code in the calling layer.

**Acceptance Scenarios**:

1. **Given** a class implementing `ProviderAdapter`, **When** registered via `ProviderRegistry.register()`, **Then** `getProvider(id)` returns the instance.
2. **Given** multiple registered providers, **When** `getAllProviders()` is called, **Then** all are returned.
3. **Given** a registered provider with `supportsSearch: false`, **When** a cross-provider search runs, **Then** it is skipped.
4. **Given** a registered provider, **When** `dispose()` is called, **Then** the provider cleans up resources.

---

### User Story 2 — VRT MAX Refactored as ProviderAdapter (Priority: P1)

As a developer, I want the existing VRT MAX integration to implement `ProviderAdapter` so that it works consistently with other providers.

**Why this priority**: Before adding new providers, the existing one must conform to the common interface.

**Independent Test**: All existing VRT auth/episode tests continue to pass after refactoring `VrtAuthService` and `VrtEpisodeService` behind the `ProviderAdapter` interface.

**Acceptance Scenarios**:

1. **Given** the VRT provider adapter, **When** `login(credentials)` is called, **Then** it performs the OIDC flow and returns tokens.
2. **Given** the VRT provider adapter, **When** `getEpisode(url)` is called, **Then** it returns typed EpisodeDetail.
3. **Given** the VRT provider adapter, **When** `resolveStream(episode)` is called, **Then** it returns StreamData with HLS URL.

---

### User Story 3 — Secure Credential Vault with Master Password (Priority: P1)

As a user, I want ONE master password that unlocks ALL my stored provider credentials so that my VRT, VTM, and Play.TV passwords are protected by a single key.

**Why this priority**: Credential storage is essential for UX and security. The one-master-password model is the core security guarantee of the app.

**Independent Test**: Verify encryption round-trip with known PBKDF2 + AES-256-GCM test vectors. Verify that:
1. Ciphertext + salt + iv can be decrypted ONLY with the correct password
2. Wrong password throws (AES-GCM authentication failure)
3. Plaintext password never appears in IndexedDB, filesystem, or logs
4. After lock(), decrypted data is purged from memory
5. Re-entering the master password re-derives the correct key

**Acceptance Scenarios**:

1. **Given** a first-time user, **When** they create a master password (min 8 chars, confirmed), **Then** a PBKDF2-derived AES-256-GCM key is created and an empty encrypted credential blob is stored in IndexedDB.
2. **Given** an initialized but locked vault, **When** the user enters the wrong master password, **Then** an "Ongeldig hoofdwachtwoord" error is shown.
3. **Given** an unlocked vault, **When** addCredentials('vrt', email, password) is called, **Then** the credentials are encrypted and appended to the blob.
4. **Given** an unlocked vault with stored VRT credentials, **When** getCredentials('vrt') is called, **Then** the decrypted email and password are returned in-memory only.
5. **Given** stored credentials, **When** listProviders() is called, **Then** only `[{ provider: 'vrt', email: '...' }]` is returned — never the password.
6. **Given** the vault has been idle for 5 minutes, **When** any credential operation is attempted, **Then** the vault auto-locked and the user must re-enter the master password.

**Web security scheme**:
```
PBKDF2(600k iterations, SHA-256) → AES-256-GCM key
IV: 12 bytes random (per encryption)
Salt: 16 bytes random (per vault creation)
Encrypted payload: salt(16) + iv(12) + ciphertext
Storage: IndexedDB
```

**Electron security scheme** (two modes):
```
Mode 1 — OS Keychain (default):
  Electron safeStorage.encryptString() / decryptString()
  Storage: encrypted file in app.getPath('userData') + '/vault.json'
  No master password — OS manages the encryption key

Mode 2 — Master Password:
  Same crypto.subtle scheme as Web
  User-chosen: convenience vs extra security
```

**Android**: Postponed — not in scope for initial release.

---

### User Story 4 — VTM GO Provider Adapter (Priority: P2)

As a user, I want to log in to my VTM GO account and browse/search VTM GO content from within the Thuis app.

**Why this priority**: VTM GO is the second-largest Flemish streaming platform and adds significant content coverage.

**Independent Test**: Requires research into VTM GO's API. Placeholder tests verify the adapter structure compiles and returns `ProviderNotSupportedError` until research is complete.

**Acceptance Scenarios**:

1. **Given** valid VTM GO credentials, **When** the VTM provider's login() is called, **Then** it authenticates and returns tokens.
2. **Given** a VTM GO program URL, **When** getEpisode() is called, **Then** EpisodeDetail is returned.
3. **Given** an authenticated VTM session, **When** resolveStream() is called, **Then** StreamData is returned.

**Research requirements** (blocking):

- [ ] R001: Map VTM GO login flow (OIDC? SAML? Custom?)
- [ ] R002: Identify API endpoints for episode listing
- [ ] R003: Identify stream manifest delivery mechanism
- [ ] R004: Determine DRM status (Widevine? PlayReady? None?)
- [ ] R005: Document API contract for adapter implementation

---

### User Story 5 — Play.TV Provider Adapter (Priority: P3)

As a user, I want to log in to my Play.TV account and access Play4/Play5/Play6/Play7 content from within the Thuis app.

**Why this priority**: Play.TV is the third major Flemish streaming platform, completing the "big three" coverage.

**Independent Test**: Same structure as VTM GO — placeholder tests until research is complete.

**Acceptance Scenarios**:

1. **Given** valid Play.TV credentials, **When** the Play.TV provider's login() is called, **Then** it authenticates.
2. **Given** a Play.TV program URL, **When** getEpisode() is called, **Then** EpisodeDetail is returned.

**Research requirements** (blocking):

- [ ] R001: Map Play.TV login flow
- [ ] R002: Identify API endpoints
- [ ] R003: Determine DRM status
- [ ] R004: Document API contract

---

### User Story 6 — Cross-Provider Unified Search (Priority: P2)

As a user, I want to search across all configured providers at once so that I can find any episode without knowing which platform carries it.

**Why this priority**: Unified search is the key value proposition of a multi-provider platform vs. using each provider's site separately.

**Independent Test**: With 2+ mock providers registered, verify that a search query fans out to all providers and aggregates results into a single sorted list.

**Acceptance Scenarios**:

1. **Given** 3 registered providers (VRT, VTM mock, Play.TV mock), **When** `search("Thuis")` is called, **Then** results from all providers are returned.
2. **Given** a search query, **When** results are returned, **Then** each result includes a `provider` field identifying the source.
3. **Given** one provider is offline, **When** search is called, **Then** results from remaining providers are returned (partial failure).

---

### Edge Cases

- What happens when the OS keychain is unavailable (Electron on headless server)? → Fall back to encrypted file with master password.
- What happens when a user revokes app access via the provider's website? → Next token refresh fails → prompt user to re-enter credentials.
- What happens when two providers have an episode with the same title? → Each result includes a `provider` field; UI shows provider icon.
- What happens when the vault master password is forgotten? → No recovery possible — user must re-enter all credentials.
- What happens when a provider changes its API? → Adapter throws `ProviderNotSupportedError` until updated.
- What happens when a user has no accounts for a given provider? → Provider shows as "Not configured" in the UI.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST define a `ProviderAdapter` interface with methods for login, search, getEpisode, resolveStream, and lifecycle.
- **FR-002**: System MUST provide a `ProviderRegistry` singleton for registering and discovering provider adapters.
- **FR-003**: The existing VRT MAX integration MUST be refactored into a `VrtProviderAdapter` implementing `ProviderAdapter`.
- **FR-004**: System MUST provide a secure credential vault using platform-appropriate encryption (OS keychain for Electron, `crypto.subtle` + IndexedDB for web).
- **FR-005**: The vault MUST auto-lock after a configurable period of inactivity (default 5 minutes).
- **FR-006**: The vault MUST support a master password for web (optional for Electron).
- **FR-007**: The vault MUST NOT expose plaintext passwords via any API — only decrypted in-memory with explicit getCredentials() call.
- **FR-008**: System MUST support cross-provider search that fans out to all registered providers and aggregates results.
- **FR-009**: System MUST handle partial provider failures during cross-provider search (return partial results).
- **FR-010**: System MUST visually distinguish results by provider in the UI.

### Key Entities

- **ProviderAdapter**: Interface with `id`, `displayName`, `supportsSearch`, `supportsAuth`, and methods for login, search, getEpisode, resolveStream, dispose.
- **ProviderRegistry**: Singleton that maps `providerId → ProviderAdapter`. Supports register, getProvider, getAllProviders, getActiveProviders.
- **ProviderCredentials**: Provider type, email, encrypted password, label, timestamps.
- **CredentialVault**: Encrypted storage for multiple ProviderCredentials. Supports add, get, remove, list, lock, unlock.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Provider adapter interface is implemented and documented — a new provider can be added in under 100 lines of code.
- **SC-002**: Credential vault encryption/decryption round-trip passes with test vectors.
- **SC-003**: Vault auto-lock fires within 30 seconds of the configured timeout.
- **SC-004**: Cross-provider search with 3 providers completes in under 10 seconds (network-dependent).
- **SC-005**: Zero plaintext passwords appear in any storage layer (verified by grep + code review).

---

## Assumptions

- VTM GO and Play.TV authentication is via email/password (not exclusively Google/Facebook SSO).
- VTM GO and Play.TV APIs can be reverse-engineered from web traffic; no official public API exists.
- Play.TV is owned by SBS Belgium (DPG Media) — may share infrastructure with VTM GO.
- Users are willing to store provider passwords in exchange for not having to log in manually each time.
- The OS keychain is available on Electron target platforms (Linux: libsecret, macOS: Keychain, Windows: Credential Manager).
- For the web crypto.subtle implementation: the app runs in a secure context (HTTPS or localhost) — required by the Web Crypto API.

---

## Notes

- VTM GO and Play.TV adapters are **research-blocked**. The spec provides the contract; implementation requires API reverse-engineering.
- The credential vault should be built and tested before any new provider adapters (since they all need it).
- Consider a "vault health" feature: periodically verify stored credentials by attempting login and flagging failures.
- Master password recovery is intentionally out of scope — if forgotten, all stored credentials must be re-entered.
- For the Electron app, consider using `safeStorage.isEncryptionAvailable()` to detect keychain support and fall back gracefully.
