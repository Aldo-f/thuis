# Work Plan: Update yt-dlp Dependency for VRT MAX Downloader

## TL;DR

> **Quick Summary**: Update the project to use a specific tag from the `Aldo-f/yt-dlp` fork (`v2026.06.09-patch1`) which includes a necessary patch for the VRT MAX extractor. This resolves the HTTP 400 Bad Request error encountered during video asset JSON extraction. The plan includes steps to update the dependency, verify functionality with existing tests, and add a future-proofing TODO for when the patch is merged upstream.
>
> **Deliverables**:
> - Updated `requirements.txt` to pin `yt-dlp` to the specified fork tag.
> - Verification that existing tests pass with the updated dependency.
> - A TODO item in the plan for future cleanup once PR #17065 is merged upstream.
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO - sequential
> **Critical Path**: Update dependency → Run tests → Commit changes

---

## Context

### Original Request
The VRT MAX downloader was encountering an "HTTP Error 400: Bad Request" when trying to download VRT MAX videos, specifically during the extraction of asset JSON. This was traced back to a known issue in `yt-dlp`'s VRT MAX extractor that was not yet merged into the main branch. The user wants to resolve this by using a specific release tag (`v2026.06.09-patch1`) from their fork (`Aldo-f/yt-dlp`) which contains the necessary fix.

### Interview Summary
**Key Discussions**:
- Use the release tag `v2026.06.09-patch1` from `Aldo-f/yt-dlp` for the `yt-dlp` dependency.
- Add a TODO to remove this direct dependency once PR #17065 (which contains the fix) is merged upstream.
- The scope is limited to updating the dependency and verifying existing functionality.
- Testing strategy: Update dependency, run existing tests to confirm. If existing tests are insufficient, add new ones.

**Research Findings**:
- PR #15866 and #17065 on `yt-dlp` address the VRT MAX extractor issue.
- The tag `v2026.06.09-patch1` from `Aldo-f/yt-dlp` incorporates these fixes.
- Manual patch application failed due to code divergence.

### Metis Review
**Identified Gaps** (addressed):
- **Clarified Testing Strategy**: Pragmatic approach chosen: update dependency first, then run existing tests. New tests only if necessary.
- **Scope Confirmation**: Confirmed focus on dependency update and verification.

---

## Work Objectives

### Core Objective
Update the `yt-dlp` dependency to a specific version from the `Aldo-f/yt-dlp` fork that includes the VRT MAX extractor fix, ensuring continued functionality of the VRT MAX downloader.

### Concrete Deliverables
- Project configuration updated to use `Aldo-f/yt-dlp` tag `v2026.06.09-patch1`.
- All existing tests (unit, integration, real download) pass with the updated dependency.

### Definition of Done
- `requirements.txt` reflects the pinned `yt-dlp` version.
- All tests in `test_poc.py` and `test_real_download.py` pass.
- A TODO item is added to the plan for future cleanup.

### Must Have
- `yt-dlp` updated to `Aldo-f/yt-dlp` tag `v2026.06.09-patch1`.
- All existing tests must pass.

### Must NOT Have (Guardrails)
- No manual patching of `yt-dlp` source code within the project.
- Do not remove the `poc.py` script or its tests.
- Do not alter the existing test suite's functionality or structure, beyond ensuring it passes.

### Spec Framework Integration (if detected)

- **Detected Framework**: Spec Kit
- **Config File**: .specify/config.yml
- **Active Specs**: .specify/specs/vrt_max_downloader.md
- **Active Changes/Proposals**: N/A
- **Available Commands**: `specify plan` (for generating plans), `specify task` (for creating tasks)
- **Spec-to-Task Mapping**: This plan directly addresses requirements outlined in `.specify/specs/vrt_max_downloader.md` related to VRT MAX extractor functionality.

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed. No exceptions.
> Acceptance criteria requiring "user manually tests/confirms" are FORBIDDEN.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests after (existing tests will be run)
- **Framework**: pytest
- **If TDD**: N/A for this specific task. Tests will be run against the updated dependency.

### QA Policy
Every task MUST include agent-executed QA scenarios (see TODO template below).
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) - Navigate, interact, assert DOM, screenshot
- **TUI/CLI**: Use interactive_bash (tmux) - Run command, send keystrokes, validate output
- **API/Backend**: Use Bash (curl) - Send requests, assert status + response fields
- **Library/Module**: Use Bash (bun/node REPL) - Import, call functions, compare output

---

## Execution Strategy

### Parallel Execution Waves

> This is a sequential task. Only one wave is needed.

Wave 1 (Start Immediately):
├── Task 1: Update `requirements.txt`
├── Task 2: Install `yt-dlp` from the specified tag
├── Task 3: Run existing unit tests (`test_poc.py`)
├── Task 4: Run existing integration tests (`test_real_download.py`)
├── Task 5: Add TODO for future upstream merge cleanup
└── Task 6: Commit and push changes

### Dependency Matrix (abbreviated - show ALL tasks in your generated plan)

- **1**: - (None)
- **2**: 1
- **3**: 2
- **4**: 2
- **5**: 2, 3, 4
- **6**: 5

### Agent Dispatch Summary

- **1**: **1** - T1 → `quick`
- **2**: **1** - T2 → `quick`
- **3**: **1** - T3 → `quick`
- **4**: **1** - T4 → `quick`
- **5**: **1** - T5 → `quick`
- **6**: **1** - T6 → `quick`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**
> **FORMAT**: Task labels MUST use bare numbers: `1.`, `2.`, `3.` — NOT `T1.`, `Task 1.`, `Phase 1:`.
> The /start-work progress counter requires exact format. Deviation = progress shows 0/0.
> Final Verification Wave labels MUST use `F1.`, `F2.`, etc. — NOT `T-F1.`, `F-1.`, `Final 1.`.

- [x] 1. Update `requirements.txt` with `yt-dlp` fork tag

  **What to do**:
  - Replace the current `yt-dlp` entry in `requirements.txt` with the pinned version from your fork: `git+https://github.com/Aldo-f/yt-dlp.git@v2026.06.09-patch1#egg=yt-dlp`.

  **Must NOT do**:
  - Do not change any other dependencies.

  **Recommended Agent Profile**:
  > Selecting 'quick' category as this is a simple file edit. No specific skills needed beyond basic file manipulation.
  - **Category**: `quick`
    - Reason: Simple file content modification.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for editing requirements.txt.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: Task 2
  - **Blocked By**: None (can start immediately)

  **References**:

  > Executor needs to know the exact line to modify in `requirements.txt`.

  **Pattern References**:
  - `requirements.txt`: The file to be modified.

  **Acceptance Criteria**:
  - **If TDD**: N/A (this is a configuration change)
  - File `requirements.txt` content is updated to include the line: `git+https://github.com/Aldo-f/yt-dlp.git@v2026.06.09-patch1#egg=yt-dlp`

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify requirements.txt is updated with the correct yt-dlp fork tag
    Tool: Read
    Preconditions: The existing requirements.txt file.
    Steps:
      1. Read the content of requirements.txt.
      2. Assert that the line `git+https://github.com/Aldo-f/yt-dlp.git@v2026.06.09-patch1#egg=yt-dlp` is present in the file content.
    Expected Result: The specific yt-dlp dependency line is found in requirements.txt.
    Failure Indicators: The line is missing, or requirements.txt does not exist.
    Evidence: .omo/evidence/task-1-verify-requirements-update.txt
  \`\`\`

  **Commit**: YES
  - Message: `chore(deps): update yt-dlp to v2026.06.09-patch1 from fork`
  - Files: `requirements.txt`

- [x] 2. Install `yt-dlp` from the specified tag

  **What to do**:
  - Run `pip install -r requirements.txt` to install `yt-dlp` from the pinned fork tag.
  - This will ensure the patched version is used in the project environment.

  **Must NOT do**:
  - Do not install any other dependencies manually; rely on `requirements.txt`.

  **Recommended Agent Profile**:
  > Selecting 'quick' category for package installation. No specific skills needed beyond basic shell commands.
  - **Category**: `quick`
    - Reason: Standard package installation via pip.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not applicable for pip install.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: Task 3, Task 4, Task 5
  - **Blocked By**: Task 1

  **References**:

  > Executor needs to know the command to run for installation.

  **Pattern References**:
  - `requirements.txt`: File containing the pinned dependency.

  **Acceptance Criteria**:
  - `pip install -r requirements.txt` completes successfully without errors.
  - The installed `yt-dlp` version corresponds to the tagged commit.

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify yt-dlp installation from the specified fork tag completes successfully
    Tool: interactive_bash
    Preconditions: requirements.txt is updated, virtual environment is active.
    Steps:
      1. Execute: `pip install -r requirements.txt`
      2. Capture the output.
      3. Assert that the installation output indicates successful installation of yt-dlp from the specified git URL and tag.
      4. Assert that the exit code is 0.
    Expected Result: yt-dlp is installed successfully from the specified fork tag without errors.
    Failure Indicators: Non-zero exit code, error messages related to installation or patch conflicts.
    Evidence: .omo/evidence/task-2-verify-ytdlp-install.log
  \`\`\`

  **Commit**: YES
  - Message: `chore(deps): install pinned yt-dlp fork`
  - Files: `requirements.txt` (implicit change from install)

- [x] 3. Run existing unit tests (`test_poc.py`)

  **What to do**:
  - Execute the unit tests for `poc.py` using pytest.
  - Ensure all tests pass, confirming basic functionality and VRT MAX extractor fix.

  **Must NOT do**:
  - Do not modify the test files themselves.

  **Recommended Agent Profile**:
  > Selecting 'quick' category for running existing tests. No specific skills needed beyond shell execution.
  - **Category**: `quick`
    - Reason: Running an existing test suite.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `pytest`: Not a direct skill, but implicitly handled by shell execution.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: Task 5
  - **Blocked By**: Task 2

  **References**:

  > Executor needs to know the command to run for unit tests.

  **Pattern References**:
  - `test_poc.py`: The file containing unit tests.

  **Acceptance Criteria**:
  - `pytest test_poc.py` command executes successfully.
  - All unit tests in `test_poc.py` pass (0 failures).

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify unit tests for poc.py pass successfully
    Tool: interactive_bash
    Preconditions: Virtual environment active, yt-dlp installed from fork, test_poc.py exists.
    Steps:
      1. Execute: `pytest test_poc.py`
      2. Capture the output and exit code.
      3. Assert that the output shows all tests passed (e.g., "X passed").
      4. Assert that the exit code is 0.
    Expected Result: All unit tests for poc.py pass.
    Failure Indicators: Any test failures, errors during execution, or non-zero exit code.
    Evidence: .omo/evidence/task-3-verify-poc-unit-tests.log
  \`\`\`

  **Commit**: YES
  - Message: `test(poc): pass unit tests with updated yt-dlp`
  - Files: `test_poc.py` (implicit change due to passing)

- [x] 4. Run existing integration tests (`test_real_download.py`)

  **What to do**:
  - Execute the integration tests for `test_real_download.py`.
  - Ensure all tests pass, confirming the VRT MAX downloader works correctly with the patched `yt-dlp`.

  **Must NOT do**:
  - Do not modify the test files themselves.

  **Recommended Agent Profile**:
  > Selecting 'quick' category for running existing tests. No specific skills needed beyond shell execution.
  - **Category**: `quick`
    - Reason: Running an existing test suite.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `pytest`: Not a direct skill, but implicitly handled by shell execution.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: Task 5
  - **Blocked By**: Task 2

  **References**:

  > Executor needs to know the command to run for integration tests.

  **Pattern References**:
  - `test_real_download.py`: The file containing integration tests.

  **Acceptance Criteria**:
  - `pytest test_real_download.py` command executes successfully.
  - All integration tests in `test_real_download.py` pass (0 failures).

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify integration tests for VRT MAX downloader pass successfully
    Tool: interactive_bash
    Preconditions: Virtual environment active, yt-dlp installed from fork, test_real_download.py exists.
    Steps:
      1. Execute: `pytest test_real_download.py`
      2. Capture the output and exit code.
      3. Assert that the output shows all tests passed (e.g., "X passed").
      4. Assert that the exit code is 0.
    Expected Result: All integration tests for the VRT MAX downloader pass.
    Failure Indicators: Any test failures, errors during execution (like HTTP 400), or non-zero exit code.
    Evidence: .omo/evidence/task-4-verify-real-download-tests.log
  \`\`\`

  **Commit**: YES
  - Message: `test(vrt-downloader): pass integration tests with updated yt-dlp`
  - Files: `test_real_download.py` (implicit change due to passing)

- [x] 5. Add TODO for future upstream merge cleanup

- TODO: Once PR #17065 is merged upstream, replace the fork tag with the official yt-dlp package in requirements.txt.

  **What to do**:
  - Add a TODO item to the plan or relevant code comments.
  - This TODO should state that once the fix from PR #17065 is merged upstream into the main `yt-dlp` repository, the direct dependency on `Aldo-f/yt-dlp` should be removed and replaced with the official `yt-dlp` package.

  **Must NOT do**:
  - Do not implement the cleanup now; just add the TODO.

  **Recommended Agent Profile**:
  > Selecting 'quick' category for adding a TODO item. No specific skills needed.
  - **Category**: `quick`
    - Reason: Adding a comment/TODO.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `writing`: Overkill for a simple TODO comment.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: Task 6
  - **Blocked By**: Task 3, Task 4

  **References**:

  > Executor needs to know where to add the TODO. This plan itself is the primary reference.

  **Pattern References**:
  - This plan document (`.omo/plans/update-ytdlp-dependency.md`).

  **Acceptance Criteria**:
  - A clear TODO item exists within the plan or relevant code, referencing PR #17065 and specifying the need to revert to the official `yt-dlp` package once merged.

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify a TODO item for future upstream merge cleanup is present
    Tool: Read
    Preconditions: The plan file `.omo/plans/update-ytdlp-dependency.md` exists.
    Steps:
      1. Read the content of `.omo/plans/update-ytdlp-dependency.md`.
      2. Search for a TODO mentioning "upstream merge", "PR #17065", and "revert to official yt-dlp".
    Expected Result: A clear TODO item related to the upstream merge of the VRT MAX fix is found in the plan.
    Failure Indicators: No such TODO is found.
    Evidence: .omo/evidence/task-5-verify-todo-present.txt
  \`\`\`

  **Commit**: YES
  - Message: `chore: add TODO for future yt-dlp upstream merge`
  - Files: `.omo/plans/update-ytdlp-dependency.md` (or relevant code comment if added elsewhere)

- [x] 6. Commit and push changes

  **What to do**:
  - Commit all the staged changes (requirements.txt update, test passing, TODO addition).
  - Push the changes to the remote repository.

  **Must NOT do**:
  - Do not force push.
  - Do not amend previous commits.

  **Recommended Agent Profile**:
  > Selecting 'quick' category for Git operations. Using `git-master` skill for robust Git handling.
  - **Category**: `quick`
    - Reason: Standard Git workflow.
  - **Skills**: [`git-master`]
    - `git-master`: Essential for managing commits and pushes.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 1)
  - **Blocks**: None (This is the final task)
  - **Blocked By**: Task 5

  **References**:

  > Executor needs to know the standard Git commit and push workflow.

  **Pattern References**:
  - `.git/hooks/pre-commit`: The pre-commit hook will run automatically before commit.

  **Acceptance Criteria**:
  - `git status` shows no uncommitted changes.
  - `git log` shows the new commit(s) with appropriate messages.
  - `git push` completes successfully.

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify changes are committed and pushed successfully
    Tool: git-master
    Preconditions: All previous tasks completed, changes are staged.
    Steps:
      1. Execute: `git status`
      2. Assert that the working directory is clean.
      3. Execute: `git log --oneline -1`
      4. Assert that the latest commit message matches the expected message for this task (e.g., "chore(deps): update yt-dlp...").
      5. Execute: `git push`
      6. Assert that the push command completes successfully.
    Expected Result: Changes are committed and pushed to the remote repository.
    Failure Indicators: Working directory not clean, incorrect commit message, push failure.
    Evidence: .omo/evidence/task-6-verify-commit-push.log
  \`\`\`

  **Commit**: N/A (This task IS the commit and push)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay. Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.**

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, oversized modules (250+ pure LOC with mandatory modular refactoring).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `chore(deps): update yt-dlp to v2026.06.09-patch1 from fork` - `requirements.txt`
- **2**: `chore(deps): install pinned yt-dlp fork` - `requirements.txt` (implicit change from install)
- **3**: `test(poc): pass unit tests with updated yt-dlp` - `test_poc.py` (implicit change due to passing)
- **4**: `test(vrt-downloader): pass integration tests with updated yt-dlp` - `test_real_download.py` (implicit change due to passing)
- **5**: `chore: add TODO for future yt-dlp upstream merge` - `.omo/plans/update-ytdlp-dependency.md` (or relevant code comment)
- **6**: `chore(deps): finalize yt-dlp update and tests` - (combines changes from 1-5)

---

## Success Criteria

### Verification Commands
```bash
pytest test_poc.py # Expected: All tests pass
pytest test_real_download.py # Expected: All tests pass
pip install -r requirements.txt # Expected: Success, no errors
git status # Expected: Working directory clean
git log --oneline -1 # Expected: Latest commit message matches Task 6 description
git push # Expected: Success
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] All tests pass
- [x] `requirements.txt` updated correctly
- [x] TODO item for future cleanup added
- [x] Changes committed and pushed
