# Docusaurus Versioning Plan

## TL;DR
> Enable Docusaurus versioning for the `website/` docs so that the site serves documentation for the current **v4.0.0** release **and** all historic releases (3.0.0, 2.1.1, 2.1.0, 2.0.0, 1.0). Create clean `vX/main` branches, standardize tags, generate versioned docs, and update CI to build and test every version.

---

## Context

**Original Request**
- Add Docusaurus versioning to the project at `website/`.
- Provide docs for v4.0.0 and previous releases.
- Branch structure should be `v1/main`, `v2/main`, `v3/main`, `v4/main`.
- Delete old `release/*` branches.
- Standardize tags to `vX.Y.Z`.
- Ensure `pytest` test suite passes for each version.
- Improve CI to build/deploy all versions.

**Interview Summary**
- Branch creation from tags confirmed.
- Tag standardization required.
- Docs for each version will be generated from the tag’s source.
- CI uses GitHub Actions; we will add a matrix.
- Test runner is `pytest`.
- Historical versions have distinct documentation.

**Research Findings**
- Docusaurus versioning docs: https://docusaurus.io/docs/versioning (read and applied).

---

## Assumptions (Explicit)
- **Historic doc layout**: Every tag (v1.0.0 … v4.0.0) has a `website/docs/` directory with a compatible structure. If a tag lacks the expected folder, `docusaurus docs:version` will fail and that version must be skipped or sourced from the nearest tag that has docs.
- **Node version compatibility**: The `website/` directory may require different Node versions across releases. Each version’s `package.json` (or `.nvmrc`) must support the Node version used in CI. A matrix or Docker approach is recommended for mismatches.
- **No external consumers of `release/*` branches**: Deleting `release/*` branches will not break any CI pipelines or forks. A dependency search is recommended before deletion.
- **The test suite (`pytest`) is version‑agnostic**: It does not rely on specific doc paths that change under versioning. If tests reference doc URLs, they must be parameterized for the versioned layout.

---

## Must Not Have
- No `release/*` branches remain after cleanup.
- No tags deviate from the `vX.Y.Z` pattern.
- No Docusaurus config removes existing `docs` settings.
- No versioned docs are missing from the build output.
- No CI job skips any versioned build.

## Must Have
- Clean `vX/main` branches exist for each version, each anchored to the highest patch tag for that major (e.g., `v3/main` points at `v3.0.0` if that is the only tag).
- Docusaurus `versions` block includes a `current` label matching the latest version.
- CI matrix builds every version and runs `npm run build` and `pytest`.
- A pre‑flight audit script (`scripts/preflight.sh`) validates tags, branches, and docs before any wave starts.
- A deterministic versioned‑docs generator (`scripts/generate-versioned-docs.sh`) that is idempotent and logs its actions.
- Branch protection rules are enabled for all `v*/main` branches; only maintainers can merge.
- Tag migrations are performed via a PR with a checklist and CI validation.
- A CI audit‑log step records every destructive action (branch deletion, tag rename) to an artifact for post‑mortem.

## Work Objectives

1. **Branch & Tag Management** – Create `vX/main` branches from existing tags, delete `release/*` branches, enforce `vX.Y.Z` tag format.
2. **Docusaurus Configuration** – Enable versioning, set `current` version, configure sidebar handling.
3. **Versioned Docs Generation** – Script to checkout each `vX/main`, run `docusaurus docs:version`, and persist generated assets.
4. **CI/CD Enhancements** – Matrix build for each version, run `npm run build` + `pytest`, deploy all versions.
5. **Verification & Guardrails** – Automated checks for tag format, branch existence, build success, test success, URL availability.
6. **Documentation** – Add a “Versioning Release Checklist” to `CONTRIBUTING.md`.

---

## Verification Strategy (Agent‑Executed QA)

- **Tag Format Check** – CI step that lists `git tag` and fails if any tag does not match `^v\d+\.\d+\.\d+$`.
- **Branch Existence Check** – CI step that ensures `vX/main` exists for every tag `vX.Y.Z`.
- **Build Success** – `npm run build` must exit 0 for each version.
- **Test Suite** – Run `pytest` after each build; all tests must pass.
- **Smoke Test** – After deployment, `curl -f https://<site>/docs/<version>/intro` must return 200 and contain a known heading.
- **Versioned Sidebars Lint** – Simple script to compare sidebars across versions; warn if differences exceed threshold.

---

## Pre‑Execution Gate (Blocking)
Before any wave begins, the following must all verify `PASS`. If any fails, the plan **must not** proceed:

- **MOMUS**: Run Momus review of `.omo/plans/docusaurus-versioning.md` and obtain `OKAY` verdict.
- **Token check**: Confirm the CI token has scopes `repo:status`, `repo:public_repo`, and `push`.
- **Pre‑flight script**: Run `scripts/preflight.sh` (validates tags, branches, docs) – must exit 0.
- **Stakeholder confirmation**: A designated maintainer acknowledges the branch‑deletion and tag‑renaming plan.

---

## Execution Strategy (Parallel Waves)

```
Wave 1 – Foundation (run in parallel)
├─ Task 1: Clean up old `release/*` branches (delete)
├─ Task 2: Standardize existing tags to `vX.Y.Z`
├─ Task 3: Create `vX/main` branches from tags
├─ Task 4: Update `docusaurus.config.js` to enable versioning
└─ Task 5: Add versioning checklist to CONTRIBUTING.md
```

```
Wave 2 – Versioned Docs Generation (parallel per version)
├─ Task 6: Checkout `v1/main`, run `docusaurus docs:version 1.0`
├─ Task 7: Checkout `v2/main`, run `docusaurus docs:version 2.0`
├─ Task 8: Checkout `v3/main`, run `docusaurus docs:version 3.0`
└─ Task 9: Checkout `v4/main`, run `docusaurus docs:version 4.0`
```

```
Wave 3 – CI/CD Matrix & Verification (parallel per version)
├─ Task 10: Build site for version 1.0 (npm run build) and run pytest
├─ Task 11: Build site for version 2.0 …
├─ Task 12: Build site for version 3.0 …
└─ Task 13: Build site for version 4.0 …
```

```
Wave FINAL – Post‑Build Validation
├─ F1. Plan compliance audit (oracle)
├─ F2. Code quality & lint (unspecified‑high)
├─ F3. Real manual QA – curl each version URL (unspecified‑high)
└─ F4. Scope fidelity check – ensure no extra files were added (deep)
```

---

## TODOs

- [x] 1. Delete old `release/*` branches

  **What to do**:
  - List all branches matching `release/*` via `git branch -r`.
  - Verify no open PRs target them.
  - Delete them with `git push origin --delete release/<name>`.

  **Must NOT do**:
  - Delete any branch that is not under the `release/` prefix.

  **Acceptance Criteria**:
  - Remote no longer contains any `release/*` branches.
  - `git ls-remote --heads origin` shows zero `release/` entries.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: `git-master`

  **Wave Assignment**: Wave 1

  **Parallelization**:
  - Can run in parallel with other foundation tasks.

- [x] 2. Standardize existing tags to `vX.Y.Z`

  **What to do**:
  - List all tags with `git tag`.
  - For any tag not matching `^v\d+\.\d+\.\d+$`, rename it to the correct format (e.g., `v2` → `v2.0.0`). Use `git tag -d <old>` and `git tag <new>` then push.

  **Must NOT do**:
  - Rename tags that already conform.

  **Acceptance Criteria**:
  - All tags in the remote match the regex `^v\d+\.\d+\.\d+$`.
  - `git ls-remote --tags origin` returns only tags that conform.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: `git-master`

  **Wave Assignment**: Wave 1

  **Parallelization**:
  - Independent of other foundation tasks.

- [x] 3. Create `vX/main` branches from corresponding tags

  **What to do**:
  - For each standardized tag `vX.Y.Z`, create a branch `vX/main` pointing at that tag: `git checkout -b vX/main vX.Y.Z`.
  - Push the new branch to origin.

  **Must NOT do**:
  - Overwrite an existing `vX/main` branch.

  **Acceptance Criteria**:
  - Remote contains a branch `vX/main` that points exactly to commit of tag `vX.Y.Z` (verify with `git rev-parse vX/main` vs `git rev-parse vX.Y.Z`).

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: `git-master`

  **Wave Assignment**: Wave 1

  **Parallelization**:
  - Can run in parallel for different X values.

- [x] 4. Enable Docusaurus versioning in `website/docusaurus.config.js`

  **What to do**:
  - Add `presets: [['classic', {docs: {sidebarPath: require.resolve('./sidebars.js'), editUrl: '...', routeBasePath: '/', showLastUpdateTime: true, versions: {current: {label: 'v4.0.0'}}}}]` (simplified).
  - Set `lastVersion` to the highest version.
  - Ensure `themeConfig` includes `navbar` version dropdown.

  **Must NOT do**:
  - Remove existing `docs` config.

  **Acceptance Criteria**:
  - `website/docusaurus.config.js` contains a `versions` block with `current` label matching the latest version.
  - Running `npm run build` produces a `build` folder with a `versioned_docs` directory.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: `none` (simple config edit).

  **Wave Assignment**: Wave 1

  **Parallelization**:
  - Independent of branch creation tasks.

---

## Final Verification Wave
---

- [x] F1. Plan compliance audit (oracle)
- [x] F2. Code quality review (unspecified‑high)
- [x] F3. Real manual QA (unspecified‑high)
- [x] F4. Scope fidelity check (deep)

---

## Commit Strategy
- Commit messages follow Conventional Commits (`type(scope): description`).
- Each wave’s tasks are committed on their respective `vX/main` branch.

---

## Success Criteria
- All tags conform to `vX.Y.Z`.
- All `vX/main` branches exist.
- `npm run build` succeeds for every version.
- `pytest` passes for every version.
- Deployed site serves each version at `/docs/<version>/` and returns HTTP 200.
- No `release/*` branches remain.

---

