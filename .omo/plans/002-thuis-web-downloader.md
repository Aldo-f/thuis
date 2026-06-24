# Work Plan: Thuis Web Downloader Specification Completion

## TL;DR

> **Quick Summary**: Complete the specification-to-code mapping and close out feature specification `002-thuis-web-downloader`.
>
> **Deliverables**:
> - Reconcile spec files into `.omo/plans/002-thuis-web-downloader.md`.
> - Validate Jest unit test suite of `@thuis/core` (23 unit tests pass).
> - Outline transition to `003-multi-provider-platform` for multi-provider credential vaulting and stream adapter integration.
>
> **Estimated Effort**: Quick
> **Parallel Execution**: YES
> **Critical Path**: Core verification → Sync Specs → Update `.specify/feature.json` to 003

---

## Context

### Original Request
We have fully implemented Phase 1 (Core Engine), Phase 2 (Web App UI), Phase 3 (Electron), and Phase 4 (Docs) for the Thuis application. We need to formalize the completion of the `002-thuis-web-downloader` specification in Specify and transition to the next specifications.

### Research Findings
- The `002-thuis-web-downloader` feature covers the core login, metadata retrieval, stream resolution, local streaming (HLS), and Electron downloading (FFmpeg) capabilities.
- All 23 unit tests mock the network correctly using `nock` and compile cleanly with strict TypeScript configurations.

---

## Work Objectives

### Core Objective
Document the completed `002-thuis-web-downloader` feature, verify test compliance, and officially transition to planning/implementing `003-multi-provider-platform` in the Spec Kit workflow.

### Concrete Deliverables
- Fully populated `.omo/plans/002-thuis-web-downloader.md` documenting implemented components and coverage.
- Fully verified test run in `@thuis/core`.
- Updated `.specify/feature.json` to `"specs/003-multi-provider-platform"` for the next feature.

### Must Have
- Comprehensive mapping of implemented files to the functional requirements of `002-thuis-web-downloader`.
- 100% of the 23 unit tests in `@thuis/core` passing.

### Must NOT Have (Guardrails)
- No code changes to `packages/core`, `packages/web-app`, or `packages/electron-app` (since implementation is already verified and committed).
- No modified code outside of `.omo/` or `.specify/`.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Unit tests with Jest (`pnpm --filter @thuis/core test`)
- **Coverage**: 100% passing tests for auth, metadata, and stream resolution.

### QA Policy
Since the feature is fully implemented, we will verify the code works by running the Jest test suite of the core package, and outline manual validation steps for stream resolution and playbacks.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Documentation & Spec Closeout):
├── Task 1: Complete 002 technical mapping in .omo/plans/ [quick]
├── Task 2: Verify all 23 unit tests pass [quick]
└── Task 3: Commit 002 closeout documentation [quick]

Wave 2 (Specification Transition):
└── Task 4: Set active feature in feature.json to specs/003-multi-provider-platform [quick]
```

## TODOs

- [ ] 1. Technical mapping of 002-thuis-web-downloader to code

  **What to do**:
  Map the implemented files in the codebase to each requirement in the `002-thuis-web-downloader` specification to ensure 100% compliance.
  - FR-001 (VRT Auth): `packages/core/src/auth/VrtAuthService.ts`
  - FR-005 (Episode Metadata): `packages/core/src/episode/VrtEpisodeService.ts`
  - FR-007 (Stream Resolution): `packages/core/src/download/StreamResolver.ts`
  - FR-011 (FFmpeg Downloader): `packages/electron-app/src/main/download-engine.ts`
  - FR-014 (Web Player): `packages/web-app/src/pages/EpisodeDetail.tsx` with Hls.js

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: This is purely a mapping and documentation task.

  **Acceptance Criteria**:
  - [ ] Code paths for login, metadata, stream resolution, downloading, and UI player documented and aligned.

- [ ] 2. Run and verify core Jest test suite

  **What to do**:
  Run `pnpm --filter @thuis/core test` from the workspace root and verify that all 23 unit tests pass cleanly.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Running unit tests is a single, fast verification step.

  **Acceptance Criteria**:
  - [ ] Output from test runner shows 23 tests passing with 0 failures.

- [ ] 3. Commit closeout documentation to Git

  **What to do**:
  Stage the `.omo/plans/002-thuis-web-downloader.md` file and commit it under the conventional commit `docs: complete 002-thuis-web-downloader planning and transition`.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple Git operation.

  **Acceptance Criteria**:
  - [ ] Commit exists on local and remote branches.

- [ ] 4. Transition active feature to specs/003-multi-provider-platform

  **What to do**:
  Update `.specify/feature.json` to `"specs/003-multi-provider-platform"` so that subsequent Spec Kit runs operate on the next design scope (Multi-provider configuration and credential storage).

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple JSON file modification.

  **Acceptance Criteria**:
  - [ ] `.specify/feature.json` contains `"feature_directory": "specs/003-multi-provider-platform"`.

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify that all requirements in `002-thuis-web-downloader` match the committed source code files exactly.
  Output: `Must Have [5/5] | Tasks [4/4] | VERDICT: APPROVE`

- [ ] F2. **Test & Build Verification** — `unspecified-high`
  Run the `@thuis/core` tests and verify compilation of all workspace packages.
  Output: `Core Tests [PASS] | Web Build [PASS] | Electron Build [PASS] | VERDICT: APPROVE`

---

## Commit Strategy

- **1**: `docs: document specification 002 closeout and transition to 003`

---

## Success Criteria

### Verification Commands
```bash
pnpm --filter @thuis/core test
```
