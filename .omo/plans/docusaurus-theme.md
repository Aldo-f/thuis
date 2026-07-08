# Plan: Extract Docusaurus Theme to Reusable Package

## TL;DR

> **Quick Summary**: Extract `thuis/website`'s custom CSS and theme configuration into a standalone `@aldo-f/docusaurus-theme` NPM package published to GitHub Packages, with TypeScript source, Rollup build, and CI.

> **Deliverables**:
> - New private GitHub repo: `aldo-f/docusaurus-theme`
> - NPM package `@aldo-f/docusaurus-theme` published to GitHub Packages
> - `getThemePath()` + `getClientModules()` exports for Docusaurus consumption
> - CI pipeline (GitHub Actions): lint → type-check → build → test → publish on tag
> - Local example site for testing

> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: Copy CSS → Build theme entry → Package config → CI → Publish → Install in consumer

---

## Context

### Original Request

User has a fully configured Docusaurus site in `thuis/website` with custom CSS (`src/css/custom.css`) and theme config (`docusaurus.config.ts`). They want to extract these into a reusable private NPM package so other repos (e.g., `script.google`) can share consistent styling.

### Interview Summary

**Key Discussions**:
- New repo: `aldo-f/docusaurus-theme` (private, GitHub)
- Package name: `@aldo-f/docusaurus-theme`
- Language: TypeScript (source + .d.ts)
- Registry: GitHub Packages
- CI: GitHub Actions
- Testing: Jest (fresh setup)
- Components: No swizzled components exist yet — provide `theme/` structure with placeholder for future use
- Only actual custom file: `src/css/custom.css` (Tailwind + Infima overrides)

**Research Findings**:
- `website/src/theme/` does not exist (empty — no swizzled components)
- `website/src/css/custom.css` — single CSS file with all custom styling
- `website/src/components/` is empty (no custom non-theme components)
- `website/src/pages/index.tsx` + `index.module.css` — site-specific homepage (NOT migrated to theme)
- Docusaurus version: 3.10.1
- The site uses Tailwind CSS v4 (via `@tailwindcss/postcss`), PostCSS, and Infima
- `docusaurus.config.ts` references `customCss: './src/css/custom.css'` in the classic preset

### Metis Review

**Identified Gaps** (addressed):
- **No swizzled components**: Simplified scope — theme is CSS-only with placeholder structure. Resolved: user wants full structure with placeholders for future components.
- **Build tool choice**: Rollup chosen for CJS/ESM output (standard Docusaurus theme practice)
- **Tailwind + PostCSS**: Not bundled in theme package — consumer handles their own Tailwind setup
- **Image assets**: Not included — too site-specific; add later if needed
- **Test scope**: Jest tests for `getThemePath()` + `getClientModules()` + CSS snapshot

---

## Work Objectives

### Core Objective

Extract `thuis/website`'s custom Docusaurus styling into a reusable npm theme package `@aldo-f/docusaurus-theme` with full CI/CD for GitHub Packages publishing.

### Concrete Deliverables

- ✅ New GitHub repo `aldo-f/docusaurus-theme` (private) — already created
- ✅ `package.json` configured for GitHub Packages publishing
- ✅ TypeScript source with Rollup build (CJS + ESM + types)
- ✅ Theme entry point: `src/index.ts` with `getThemePath()` and `getClientModules()`
- ✅ `theme/` directory structure with placeholder for future swizzled components
- ✅ `custom.css` migrated from `thuis/website/src/css/`
- ✅ GitHub Actions workflow (publish on tag)
- ✅ Jest test suite
- ✅ Local example site for testing
- ✅ Published to GitHub Packages (`@aldo-f/docusaurus-theme`)

### Definition of Done

- [ ] `npm run build` succeeds, produces `dist/` with `index.js`, `index.esm.js`, `index.d.ts`, `custom.css`
- [ ] `npm test` passes (≥2 tests)
- [ ] CI workflow runs green
- [ ] Package published to GitHub Packages (`npm publish` succeeds)
- [ ] A test consumer site can `npm install @aldo-f/docusaurus-theme` and load the CSS

### Must Have

- Expose `custom.css` via `getClientModules()`
- Expose `getThemePath()` pointing to the theme directory
- Full TypeScript support with declarations
- CI that publishes on `git tag v*`

### Must NOT Have (Guardrails)

- Do NOT modify the original `thuis/website` repo
- Do NOT include site-specific pages (`src/pages/`, `sidebars.ts`)
- Do NOT bundle Tailwind/PostCSS config — consumer handles that
- Do NOT include `docusaurus.config.ts` — only theming API
- Do NOT hardcode paths to `thuis` — theme must be portable
- Do NOT include the `@easyops-cn/docusaurus-search-local` plugin — that's site-specific
- Do NOT bundle React or Docusaurus as dependencies (they are peerDependencies)

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (fresh setup)
- **Automated tests**: Tests-after (Jest)
- **Framework**: Jest with ts-jest
- **Coverage**: Unit tests for exported functions + CSS snapshot

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Library/Module**: Use Bash (Node REPL) — Import package, call functions, inspect output
- **Build**: Verify `dist/` files exist with correct content
- **CI**: Verify GitHub Actions workflow YAML is valid

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — 4 tasks):
├── Task 1: Scaffold new repo skeleton (package.json, tsconfig, gitignore, README)
├── Task 2: Create theme entry point (src/index.ts, src/theme/placeholder)
├── Task 3: Migrate custom.css + set up Rollup build
├── Task 4: Set up Jest testing infrastructure

Wave 2 (After Wave 1 — 2 tasks):
├── Task 5: Write test suite (getThemePath, getClientModules, CSS snapshot)
├── Task 6: Build verification + local smoke test

Wave 3 (After Wave 2 — 2 tasks):
├── Task 7: Set up GitHub Actions CI (lint, build, test, publish)
├── Task 8: Create local example site for manual pre-publish verification

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── F1: Plan Compliance Audit (oracle)
├── F2: Code Quality Review (unspecified-high)
├── F3: Manual QA — run example site, verify CSS loads
├── F4: Scope Fidelity Check (deep)
→ Present results → Get explicit user okay → Publish

Critical Path: Task 1 → Task 2 → Task 3 → Task 5 → Task 7 → F1-F4 → Publish
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 4 (Wave 1)
```

### Dependency Matrix (abbreviated)
| Task | Depends On | Blocks |
|------|-----------|--------|
| 1    | -         | 2,3,4,7 |
| 2    | 1         | 5,6     |
| 3    | 1         | 5,6     |
| 4    | 1         | 5       |
| 5    | 2,3,4     | 6       |
| 6    | 5         | 7       |
| 7    | 6         | 8       |
| 8    | 7         | F1-F4   |

### Recommended Agent Profiles

- **Task 1**: `quick` — Standard repo scaffolding
- **Task 2**: `unspecified-high` — Docusaurus theme API + TypeScript
- **Task 3**: `quick` — File copy + Rollup config
- **Task 4**: `unspecified-low` — Jest config setup
- **Task 5**: `unspecified-high` — Test writing
- **Task 6**: `unspecified-low` — Smoke test/build check
- **Task 7**: `unspecified-high` — GitHub Actions + GPR publish
- **Task 8**: `unspecified-high` — Example Docusaurus site

---

## TODOs

- [ ] 1. **Scaffold new repo skeleton**

  **What to do**:
  - Create the following files in the new repo root:
    - `package.json` with:
      - `name: "@aldo-f/docusaurus-theme"`
      - `version: "0.1.0"`
      - `private: true`
      - `publishConfig.access: "restricted"` (for GitHub Packages)
      - `main: "dist/cjs/index.js"`
      - `module: "dist/esm/index.js"`
      - `types: "dist/types/index.d.ts"`
      - `files: ["dist", "src"]`
      - `sideEffects: ["src/css/**/*.css"]`
      - `repository.type: "git"`, `repository.url: "git+https://github.com/Aldo-f/docusaurus-theme.git"`
      - peerDependencies: `@docusaurus/core: "^3.10.0"`, `react: "^19.0.0"`, `react-dom: "^19.0.0"`
      - devDependencies: `typescript`, `rollup`, `@rollup/plugin-typescript`, `@rollup/plugin-node-resolve`, `rollup-plugin-postcss`, `@types/react`, `tslib`, `jest`, `ts-jest`, `@types/jest`, `rimraf`
      - scripts: `build: "rimraf dist && rollup -c"`, `test: "jest"`, `typecheck: "tsc --noEmit"`
    - `tsconfig.json` — target ES2020, module ESNext, jsx react-jsx, declaration true, declarationDir dist/types
    - `rollup.config.js` — basic skeleton: input `src/index.ts`, output CJS + ESM, external `react`, `react-dom`, `@docusaurus/*` (Task 3 will add plugin configuration and finalize)
    - `.gitignore` — `node_modules`, `dist`, `.env`
    - `LICENSE` — MIT
    - `.npmrc` — `@aldo-f:registry=https://npm.pkg.github.com/`
    - `README.md` — brief description, install from GPR, usage
  - Init git repo, add remote, commit

  **Must NOT do**:
  - Do NOT include any site-specific config (docusaurus.config.ts, sidebars.ts)
  - Do NOT install real dependencies yet (just list them; actual install happens later in CI or local dev)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard scaffolding — creating config files, package.json, git init
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Tasks 2, 3, 4, 7
  - **Blocked By**: None (can start immediately)

  **References**:
  - Docusaurus theme packaging guide: https://docusaurus.io/docs/advanced-plugins (theme structure)
  - GitHub Packages config: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry

  **Acceptance Criteria**:
  - [ ] `package.json` exists with correct name, main, files, peerDependencies
  - [ ] `tsconfig.json` compiles with `tsc --noEmit`
  - [ ] `.gitignore` contains node_modules, dist
  - [ ] `.npmrc` points to GitHub Packages
  - [ ] Repo initialized with remote pointing to `git@github.com:Aldo-f/docusaurus-theme.git`

  **QA Scenarios**:
  ```
  Scenario: Verify package.json structure
    Tool: Bash
    Preconditions: File exists in repo root
    Steps:
      1. node -e "const pkg = require('./package.json'); console.log(pkg.name); console.log(pkg.main); console.log(pkg.files);"
    Expected Result: Output shows "@aldo-f/docusaurus-theme", "dist/cjs/index.js", "["dist","src"]"
    Evidence: .omo/evidence/task-1-package-json.txt

  Scenario: Verify .gitignore
    Tool: Bash
    Preconditions: File exists
    Steps:
      1. grep "node_modules" .gitignore && grep "dist" .gitignore
    Expected Result: Both patterns found
    Evidence: .omo/evidence/task-1-gitignore.txt

  Scenario: Verify git remote
    Tool: Bash
    Preconditions: Git initialized
    Steps:
      1. git remote -v
    Expected Result: Shows origin → git@github.com:Aldo-f/docusaurus-theme.git
    Evidence: .omo/evidence/task-1-git-remote.txt
  ```

  **Evidence to Capture**:
  - [ ] task-1-package-json.txt
  - [ ] task-1-gitignore.txt
  - [ ] task-1-git-remote.txt

  **Commit**: YES
  - Message: `chore(repo): scaffold package skeleton`
  - Files: `package.json`, `tsconfig.json`, `rollup.config.js`, `.gitignore`, `LICENSE`, `.npmrc`, `README.md`

---

- [ ] 2. **Create theme entry point + placeholder theme structure**

  **What to do**:
  - Create `src/index.ts` with:
    ```ts
    import path from 'node:path';

    export function getThemePath(): string {
      return path.resolve(__dirname, 'theme');
    }

    export function getClientModules(): string[] {
      return [path.resolve(__dirname, 'css/custom.css')];
    }
    ```
  - Create `src/theme/` directory with placeholder `index.ts`:
    ```ts
    // Placeholder for future swizzled Docusaurus theme components.
    // When you swizzle a component in your site, move the overridden
    // component file here and re-export it.
    export {};
    ```
  - Create `src/theme/Layout/` directory with placeholder if needed (empty for now)
  - Ensure TypeScript compiles the entry point correctly

  **Must NOT do**:
  - Do NOT export site-specific components (pages, non-theme components)
  - Do NOT import from thuis/website directly — this is a clean copy

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding of Docusaurus theme API (getThemePath, getClientModules)
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1 (needs tsconfig.json)

  **References**:
  - Docusaurus theme API: https://docusaurus.io/docs/advanced-plugins#theme-vs-plugin
  - `tsconfig.json` from Task 1

  **Acceptance Criteria**:
  - [ ] `src/index.ts` exports `getThemePath` and `getClientModules`
  - [ ] `src/theme/index.ts` exists with placeholder export
  - [ ] `tsc --noEmit` passes on the source

  **QA Scenarios**:
  ```
  Scenario: Verify exported functions
    Tool: Bash (Node)
    Preconditions: Source files written
    Steps:
      1. npx ts-node -e "
          const { getThemePath, getClientModules } = require('./src/index.ts');
          console.log('getThemePath:', getThemePath());
          console.log('getClientModules:', getClientModules());
        "
    Expected Result: getThemePath returns a path ending in 'theme', getClientModules returns array with path ending in 'css/custom.css'
    Evidence: .omo/evidence/task-2-exports.txt

  Scenario: TypeScript compiles
    Tool: Bash
    Preconditions: Source files written
    Steps:
      1. npx tsc --noEmit --strict src/index.ts
    Expected Result: Exit code 0, no errors
    Evidence: .omo/evidence/task-2-ts-check.txt
  ```

  **Evidence to Capture**:
  - [ ] task-2-exports.txt
  - [ ] task-2-ts-check.txt

  **Commit**: NO (subsumed by Task 3's combined commit)

---

- [ ] 3. **Migrate custom.css + set up Rollup build**

  **What to do**:
  - Copy `thuis/website/src/css/custom.css` to the new repo at `src/css/custom.css`
  - Update `rollup.config.js` (skeleton from Task 1) with full plugin configuration:
    - Input: `src/index.ts`
    - Output: CJS (`dist/cjs/index.js`) + ESM (`dist/esm/index.js`)
    - External: `react`, `react-dom`, `@docusaurus/*`, `react-jsx-runtime`
    - Plugin: `@rollup/plugin-typescript` for TS compilation
    - Plugin: `rollup-plugin-postcss` to handle CSS imports (emit as separate file or inline as path reference)
    - Plugin: `@rollup/plugin-node-resolve` for resolving node_modules
    - Copy the custom.css from `src/css/custom.css` to `dist/css/custom.css` (CSS is referenced by `getClientModules()` via path, not bundled into JS)
  - Test that `npm run build` produces correct output files

  **Must NOT do**:
  - Do NOT post-process the CSS (Tailwind/PostCSS should stay in the consumer site)
  - Do NOT copy site-specific files like `src/pages/`, `sidebars.ts`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward file copy + standard Rollup config
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 5, 6
  - **Blocked By**: Task 1 (needs rollup.config.js, tsconfig.json)

  **References**:
  - Source file: `thuis/website/src/css/custom.css`
  - Rollup config: https://rollupjs.org/configuration-options/
  - rollup-plugin-postcss: https://github.com/egoist/rollup-plugin-postcss

  **Acceptance Criteria**:
  - [ ] `src/css/custom.css` exists in new repo
  - [ ] `npm run build` creates `dist/cjs/index.js`, `dist/esm/index.js`, `dist/types/index.d.ts`, `dist/css/custom.css`
  - [ ] Build completes without errors

  **QA Scenarios**:
  ```
  Scenario: Build produces expected output files
    Tool: Bash
    Preconditions: npm run build completed
    Steps:
      1. ls dist/cjs/index.js dist/esm/index.js dist/types/index.d.ts dist/css/custom.css
    Expected Result: All 4 files exist
    Evidence: .omo/evidence/task-3-build-output.txt

  Scenario: Verify CSS content preserved
    Tool: Bash
    Preconditions: Build completed
    Steps:
      1. diff <(cat src/css/custom.css) <(cat dist/css/custom.css)
    Expected Result: No differences — CSS is preserved through build
    Evidence: .omo/evidence/task-3-css-preserved.txt

  Scenario: CJS import works
    Tool: Bash (Node)
    Preconditions: Build completed
    Steps:
      1. node -e "const m = require('./dist/cjs/index.js'); console.log(typeof m.getThemePath); console.log(typeof m.getClientModules);"
    Expected Result: "function" printed twice
    Evidence: .omo/evidence/task-3-cjs-import.txt
  ```

  **Evidence to Capture**:
  - [ ] task-3-build-output.txt
  - [ ] task-3-css-preserved.txt
  - [ ] task-3-cjs-import.txt

  **Commit**: YES (combined commit for Tasks 2 + 3)
  - Message: `feat(theme): add theme entry point, CSS, and Rollup build`
  - Files: `src/index.ts`, `src/theme/index.ts`, `src/css/custom.css`

---

- [ ] 4. **Set up Jest testing infrastructure**

  **What to do**:
  - Create `jest.config.js`:
    ```js
    module.exports = {
      preset: 'ts-jest',
      testEnvironment: 'node',
      roots: ['<rootDir>/src'],
      testMatch: ['**/__tests__/**/*.test.ts'],
      moduleNameMapper: {
        '\\.css$': '<rootDir>/src/__mocks__/styleMock.js',
      },
    };
    ```
  - Create `src/__mocks__/styleMock.js`:
    ```js
    module.exports = {};
    ```
  - Create `src/__tests__/` directory (tests themselves are in Task 5)
  - Verify Jest runs with a minimal placeholder test
  - Add `test` script to `package.json` if not already there
  - Ensure `jest`, `ts-jest`, `@types/jest` are in devDependencies

  **Must NOT do**:
  - Do NOT use babel — keep it ts-jest only
  - Do NOT set up React testing library yet (no components to test)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Standard Jest config setup
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1 (needs package.json)

  **References**:
  - Jest docs: https://jestjs.io/docs/configuration
  - ts-jest docs: https://kulshekhar.github.io/ts-jest/

  **Acceptance Criteria**:
  - [ ] `jest.config.js` exists
  - [ ] `npm test` runs without errors (placeholder test passes)
  - [ ] CSS imports are properly mocked

  **QA Scenarios**:
  ```
  Scenario: Jest runs placeholder test
    Tool: Bash
    Preconditions: Config files written
    Steps:
      1. Create minimal test: echo 'test("placeholder", () => { expect(1).toBe(1); });' > src/__tests__/placeholder.test.ts
      2. npm test
    Expected Result: Tests pass (1 passed)
    Evidence: .omo/evidence/task-4-jest-placeholder.txt

  Scenario: CSS mock works
    Tool: Bash
    Preconditions: styleMock.js exists
    Steps:
      1. node -e "const m = require('./src/__mocks__/styleMock.js'); console.log(JSON.stringify(m));"
    Expected Result: "{}"
    Evidence: .omo/evidence/task-4-style-mock.txt
  ```

  **Evidence to Capture**:
  - [ ] task-4-jest-placeholder.txt
  - [ ] task-4-style-mock.txt

  **Commit**: YES
  - Message: `chore(test): add Jest configuration with ts-jest`
  - Files: `jest.config.js`, `src/__mocks__/styleMock.js`

---

- [ ] 5. **Write test suite for theme exports**

  **What to do**:
  - Create `src/__tests__/theme.test.ts` with tests:
    1. **getThemePath returns a string**: Verify it returns a non-empty string
    2. **getThemePath points to existing directory**: Verify the returned path resolves to a directory that exists
    3. **getClientModules returns an array**: Verify it returns an array
    4. **getClientModules paths exist**: Verify each path in the returned array points to an existing file
    5. **CSS path ends with custom.css**: Verify the last segment matches
  - Create `src/__tests__/css.test.ts` (optional snapshot test):
    1. Custom CSS file exists and is non-empty
    2. CSS file contains expected Docusaurus/Tailwind classes (e.g., `--ifm-`, `@tailwind`)
  - Run `npm test` — all tests pass

  **Must NOT do**:
  - Do NOT test React components (none exist yet)
  - Do NOT test against thuis/website files (tests must be self-contained)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Writing meaningful tests for the Docusaurus theme API requires understanding the expected behavior
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 2, 3, 4)
  - **Parallel Group**: Wave 2 (sequential)
  - **Blocks**: Task 6
  - **Blocked By**: Tasks 2, 3, 4

  **References**:
  - `src/index.ts` from Task 2 — the module under test
  - `ts-jest` config from Task 4

  **Acceptance Criteria**:
  - [ ] `npm test` passes all tests
  - [ ] All exported functions have test coverage
  - [ ] CSS path verification works

  **QA Scenarios**:
  ```
  Scenario: Full test suite passes
    Tool: Bash
    Preconditions: Build completed, all source files in place
    Steps:
      1. npm test 2>&1
    Expected Result: All tests pass (≥5 tests, 0 failures)
    Evidence: .omo/evidence/task-5-all-tests.txt

  Scenario: getThemePath returns real path
    Tool: Bash (Node)
    Preconditions: Tests in place
    Steps:
      1. npx ts-node -e "
          const { getThemePath } = require('./src/index.ts');
          const fs = require('fs');
          const p = getThemePath();
          console.log('Path:', p);
          console.log('Exists:', fs.existsSync(p));
        "
    Expected Result: Path exists, returns true
    Evidence: .omo/evidence/task-5-theme-path.txt
  ```

  **Evidence to Capture**:
  - [ ] task-5-all-tests.txt
  - [ ] task-5-theme-path.txt

  **Commit**: YES
  - Message: `test(theme): add test suite for theme entry exports`
  - Files: `src/__tests__/theme.test.ts`, `src/__tests__/css.test.ts`
  - Pre-commit: `npm test`

---

- [ ] 6. **Build verification + local smoke test**

  **What to do**:
  - Run full build: `npm run build`
  - Verify `dist/` output:
    - `dist/cjs/index.js` — CommonJS bundle
    - `dist/esm/index.js` — ESM bundle
    - `dist/types/index.d.ts` — TypeScript declarations
    - `dist/css/custom.css` — Copied CSS
  - Run `npm test` to ensure all tests pass against built output
  - Optional: Temporarily create a minimal Node script that imports the built CJS module and calls `getThemePath()` and `getClientModules()` to verify they work at runtime

  **Must NOT do**:
  - Do NOT publish yet (that's Task 7/8+)
  - Do NOT modify source files

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Simple verification — run commands, check output
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (after Task 5)
  - **Blocks**: Task 7
  - **Blocked By**: Task 5

  **References**:
  - Build output from Task 3

  **Acceptance Criteria**:
  - [ ] `npm run build` succeeds (exit code 0)
  - [ ] `dist/cjs/index.js`, `dist/esm/index.js`, `dist/types/index.d.ts`, `dist/css/custom.css` all exist
  - [ ] `npm test` passes
  - [ ] Runtime import of CJS bundle works

  **QA Scenarios**:
  ```
  Scenario: Full build + test pipeline
    Tool: Bash
    Preconditions: All source files ready
    Steps:
      1. npm run build && npm test
    Expected Result: Build succeeds, all tests pass
    Evidence: .omo/evidence/task-6-build-test.txt

  Scenario: Runtime import works
    Tool: Bash (Node)
    Preconditions: Build completed
    Steps:
      1. node -e "
          const path = require('path');
          const fs = require('fs');
          const theme = require('./dist/cjs/index.js');
          const tp = theme.getThemePath();
          const cm = theme.getClientModules();
          console.log('getThemePath():', tp, '| exists:', fs.existsSync(tp));
          console.log('getClientModules():', cm, '| all exist:', cm.every(p => fs.existsSync(p)));
        "
    Expected Result: Both functions return valid paths, files exist
    Evidence: .omo/evidence/task-6-runtime.txt
  ```

  **Evidence to Capture**:
  - [ ] task-6-build-test.txt
  - [ ] task-6-runtime.txt

  **Commit**: YES (groups with Task 5)
  - Message: `chore(build): verify build pipeline and runtime imports`
  - Pre-commit: `npm run build && npm test`

---

- [ ] 7. **Set up GitHub Actions CI (lint, build, test, publish)**

  **What to do**:
  - Create `.github/workflows/publish.yml`:
    ```yaml
    name: Publish to GitHub Packages
    on:
      push:
        tags:
          - 'v*'
    jobs:
      publish:
        runs-on: ubuntu-latest
        permissions:
          contents: read
          packages: write
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: 20
              registry-url: https://npm.pkg.github.com
              scope: '@aldo-f'
          - run: npm ci
          - run: npm run typecheck
          - run: npm test
          - run: npm run build
          - run: npm publish
            env:
              NODE_AUTH_TOKEN: ${{secrets.GITHUB_TOKEN}}
    ```
  - Create `.github/workflows/ci.yml` for PRs/pushes to main (test only, no publish):
    ```yaml
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: 20
              registry-url: https://npm.pkg.github.com
              scope: '@aldo-f'
          - run: npm ci
          - run: npm run typecheck
          - run: npm test
          - run: npm run build
    ```
  - Push to GitHub and verify CI runs green

  **Must NOT do**:
  - Do NOT use secrets.GITHUB_TOKEN for anything outside the workflow
  - Do NOT publish on every push — only on tags

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: GitHub Actions + GitHub Packages authentication requires careful setup
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (with Task 8)
  - **Blocks**: Publishing step
  - **Blocked By**: Task 6

  **References**:
  - GitHub Packages publishing: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry#publishing-a-package
  - GITHUB_TOKEN permissions: https://docs.github.com/en/actions/security-guides/automatic-token-authentication

  **Acceptance Criteria**:
  - [ ] `.github/workflows/publish.yml` exists and is valid YAML
  - [ ] `.github/workflows/ci.yml` exists and is valid YAML
  - [ ] Pushed to GitHub, CI runs without error
  - [ ] Package can be published (dry-run: `npm publish --dry-run` succeeds)

  **QA Scenarios**:
  ```
  Scenario: YAML validation
    Tool: Bash
    Preconditions: Workflow files written
    Steps:
      1. node -e "require('js-yaml').load(require('fs').readFileSync('.github/workflows/publish.yml','utf8'))"
      2. node -e "require('js-yaml').load(require('fs').readFileSync('.github/workflows/ci.yml','utf8'))"
    Expected Result: No errors — valid YAML
    Evidence: .omo/evidence/task-7-yaml-valid.txt

  Scenario: npm publish dry-run
    Tool: Bash
    Preconditions: npm run build completed
    Steps:
      1. npm publish --dry-run 2>&1
    Expected Result: Dry run succeeds, shows package name and version (no actual publish)
    Evidence: .omo/evidence/task-7-dry-run.txt
  ```

  **Evidence to Capture**:
  - [ ] task-7-yaml-valid.txt
  - [ ] task-7-dry-run.txt

  **Commit**: YES
  - Message: `ci(gh-actions): add GitHub Actions workflows for CI and publish`
  - Files: `.github/workflows/publish.yml`, `.github/workflows/ci.yml`

---

- [ ] 8. **Create local example site for pre-publish verification**

  **What to do**:
  - Create `example/` directory inside the theme repo
  - Scaffold a minimal Docusaurus site inside `example/`:
    - `example/package.json` — depends on the theme via `"@aldo-f/docusaurus-theme": "file:.."` (local path)
    - `example/docusaurus.config.ts` — uses the theme:
      ```ts
      import { themes } from '@aldo-f/docusaurus-theme';
      // or use themes array:
      export default {
        title: 'Test Site',
        presets: [
          ['classic', {
            theme: {
              customCss: require('@aldo-f/docusaurus-theme').getClientModules()[0],
            },
          }],
        ],
        themes: ['@aldo-f/docusaurus-theme'],
      };
      ```
    - `example/src/pages/index.tsx` — minimal page that uses theme
    - `example/sidebars.js` — minimal (empty)
  - Install deps and run `npm run build` in example/
  - Verify the site builds without errors
  - (Optional) Run `npm run start` and visually confirm CSS loads

  **Must NOT do**:
  - Do NOT commit `node_modules` or `.docusaurus` from example to the theme repo
  - Do NOT make the example site a dependency of the theme package

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Creating a consumer-facing test site requires understanding of how the theme is consumed
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 7)
  - **Parallel Group**: Wave 3 (with Task 7)
  - **Blocks**: Final verification
  - **Blocked By**: Task 6

  **References**:
  - Docusaurus configuration reference: https://docusaurus.io/docs/api/docusaurus-config
  - Built theme package from Task 3/6

  **Acceptance Criteria**:
  - [ ] `example/` directory exists with minimal Docusaurus site
  - [ ] `npm install` in example/ succeeds (installs theme from local path)
  - [ ] `npm run build` in example/ succeeds
  - [ ] Build output includes custom theme CSS

  **QA Scenarios**:
  ```
  Scenario: Example site builds with theme
    Tool: Bash
    Preconditions: Build completed in theme repo, example/ exists
    Steps:
      1. cd example && npm install && npm run build 2>&1
    Expected Result: Build succeeds, output shows "getClientModules" is called, CSS is processed
    Evidence: .omo/evidence/task-8-example-build.txt

  Scenario: Custom CSS appears in build output
    Tool: Bash
    Preconditions: Build completed in example/
    Steps:
      1. grep -c "custom" example/build/assets/css/*.css || echo "checking for known class:"
      2. grep "tailwind\|--ifm" example/build/assets/css/*.css | head -5
    Expected Result: Build output contains custom CSS classes from the theme
    Evidence: .omo/evidence/task-8-css-in-output.txt
  ```

  **Evidence to Capture**:
  - [ ] task-8-example-build.txt
  - [ ] task-8-css-in-output.txt

  **Commit**: YES
  - Message: `test(example): add example Docusaurus site for local verification`
  - Files: `example/package.json`, `example/docusaurus.config.ts`, `example/src/pages/index.tsx`, `example/sidebars.js`, `example/.gitignore`
  - Pre-commit: `cd example && npm install && npm run build`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run build). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + `npm test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test example site building with theme. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | VERDICT`

---

## Commit Strategy

| Task(s) | Message | Files | Pre-commit |
|---------|---------|-------|------------|
| 1 | `chore(repo): scaffold package skeleton` | package.json, tsconfig.json, rollup.config.js, .gitignore, LICENSE, .npmrc, README.md | — |
| 2,3 | `feat(theme): add theme entry point, CSS, and Rollup build` | src/index.ts, src/theme/index.ts, src/css/custom.css | — |
| 4 | `chore(test): add Jest configuration` | jest.config.js, src/__mocks__/styleMock.js | — |
| 5 | `test(theme): add test suite for theme exports` | src/__tests__/theme.test.ts, src/__tests__/css.test.ts | `npm test` |
| 5,6 | `chore(build): verify build pipeline and runtime imports` | (no new files) | `npm run build && npm test` |
| 7 | `ci(gh-actions): add GitHub Actions workflows` | .github/workflows/publish.yml, .github/workflows/ci.yml | — |
| 8 | `test(example): add example Docusaurus site` | example/** | `cd example && npm install && npm run build` |

---

## Success Criteria

### Verification Commands
```bash
# Full pipeline
npm run typecheck     # Expected: no errors
npm test              # Expected: all tests pass
npm run build         # Expected: dist/ populated

# Publish readiness
npm publish --dry-run # Expected: shows package details, no errors
```

### Final Checklist
- [ ] Private GitHub repo `aldo-f/docusaurus-theme` exists and is pushed
- [ ] All custom CSS from thuis/website migrated
- [ ] `getThemePath()` + `getClientModules()` work correctly
- [ ] CI workflow runs green
- [ ] Example site builds with theme
- [ ] Package published to GitHub Packages
- [ ] Other repos can `npm install @aldo-f/docusaurus-theme` and use it


