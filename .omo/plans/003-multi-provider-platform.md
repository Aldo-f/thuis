# Work Plan: Multi-Provider Platform & Secure Credential Vault

## TL;DR

> **Quick Summary**: Plan the design, implementation, and verification of a fully‑secure multi‑provider platform for the Thuis application. The plan covers provider integration, a master‑password credential vault, and unified search. The work will be executed in parallel waves to maximize throughput and ensure strict adherence to Spec‑Kit principles.

> **Deliverables**: Architecture, core interfaces, credential vault, provider adapters, unit & integration tests.

> **Estimated Effort**: Medium – about two weeks of parallel work.

> **Parallel Execution**: Yes – 6 parallel tasks in up to 3 waves.

---

## Context

### Spec Notes
- The specification resides at `specs/003-multi-provider-platform/spec.md`.
- Focus on functional requirements FR‑001 – FR‑008, key entities ProviderAdapter, ProviderRegistry, CredentialVault.

### Current State
- Core architecture of the Thuis monorepo is defined (packages/core, web‑app, electron‑app).
- Existing VRT provider logic is hard‑coded; no generic provider registry.
- No secure credential vault is present.

---

## Work Objectives

### Core Objective
Design and implement a **provider‑agnostic** architecture and a **secure, single‑master‑password vault** that can be extended to multiple streaming providers while preserving user privacy.

### Concrete Deliverables
- `ProviderAdapter` interface definition.
- `ProviderRegistry` singleton with registration, discovery, and life‑cycle.
- `CredentialVault` with PBKDF2‑AES‑GCM (web) and `safeStorage` (Electron). Include auto‑lock and master‑password support.
- Refactored VRT provider to an adapter following the interface.
- Placeholder (mock) adapters for VTM GO and Play.TV with unit test scaffolds.
- Unified search service that fans out to all providers and aggregates results.
- Unit tests covering all new code.
- Integration tests that simulate login, episode fetch, and stream resolution.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (Jest + ts‑jest).
- **Automated tests**: YES (unit + integration tests, fail initially).
- **Coverage**: Target 80% on new code.
- **TDD/Tests‑After**: **Test‑after** – implementation first, then full test suite (but all tests must pass before code is merged).

### QA Policy
All QA is agent‑executed. Each task will contain an **Agent‑Executed QA Scenario** that will be run by the `playwright` or `jest` agent after implementation. No manual verification is allowed.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Design & Registry):
• Task 1: ProviderAdapter interface & ProviderRegistry design
• Task 2: CredentialVault design (web & Electron)

Wave 2 (Implementation):
• Task 3: Refactor VRT provider to Adapter
• Task 4: Implement unified search service
• Task 5: Implement placeholder adapters for VTM GO & Play.TV

Wave 3 (Testing & Integration):
• Task 6: Unit & integration test suites for all new code

```

---

## TODOs

- [ ] 1. Design ProviderAdapter interface and ProviderRegistry
- [ ] 2. Design CredentialVault (web + Electron)
- [ ] 3. Refactor VRT provider to adapter
- [ ] 4. Implement unified search service
- [ ] 5. Implement placeholder adapters for VTM GO and Play.TV
- [ ] 6. Write unit & integration tests for all new code

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify final plan matches spec and no guardrails are broken.
- [ ] F2. **Test & Build Verification** — `unspecified-high`
  Run full test suite; ensure 80% coverage.
- [ ] F3. **Functional Demo** — `unspecified-high`
  Execute an end‑to‑end flow: sign up with VRT, search, play a mock episode.
- [ ] F4. **Security Audit** — `unspecified-high`
  Verify vault encryption keys, auto‑lock timeout, and absence of plaintext passwords.

---

## Commit Strategy

- **1**: `feat: multi‑provider platform – design and initial implementation`.

---

## Success Criteria

- All architecture diagrams match the new provider interface.
- All tests pass and coverage ≥80% for new code.
- Security audit confirms no plaintext passwords stored.
- Initial demo shows provider login, search, and stream resolution.
