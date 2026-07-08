# Graceful Ctrl+C Handler Implementation

## TL;DR
> Add a global SIGINT handler to `src/thuis/main.py` so that pressing **Ctrl + C** exits cleanly with the message **“Interrupted by user”** and no traceback.

## Context
- **Original behavior**: Pressing Ctrl + C during GraphQL calls raises `KeyboardInterrupt`, producing a full traceback.
- **Desired behavior**: The script should terminate with a tidy `Interrupted by user` message and no traceback, while also stopping any running yt‑dlp subprocess.
- **Scope**: Only modify `src/thuis/main.py` – add `import signal` and a `signal.signal(SIGINT, …)` registration inside `main()`. No other refactoring.

## Work Objectives
- **Core objective**: Provide a clean termination when the user aborts with Ctrl + C.
- **Deliverables**:
  - Updated `src/thuis/main.py` with the signal handler.
  - Automated test verifying the clean exit.

## Verification Strategy
- **Test strategy**: **Tests‑after** – after implementing the handler, add a test that runs the script, sends SIGINT, and asserts the exit code is non‑zero and the output contains `Interrupted by user` without a traceback.
- **Agent‑executed QA**: Playwright or interactive bash agent will run the script, trigger SIGINT, capture stdout/stderr, and validate the expected output.

## Execution Strategy
- **Step 1**: Edit `src/thuis/main.py` – add `import signal` and register the handler as the first statement in `main()`.
- **Step 2**: Add a test file `tests/test_ctrl_c_handler.py` exercising the SIGINT scenario.
- **Step 3**: Run the full test suite to ensure no regressions.

---

## Must‑Have / Must‑Not‑Have
- **Must‑Have**: A single global SIGINT handler in `src/thuis/main.py` that prints `Interrupted by user` and exits without a traceback.
- **Must‑Not‑Have**: Any additional `except KeyboardInterrupt` blocks that change behavior, modifications outside `src/thuis/main.py`, or changes to logging configuration.

## TODOs

- [x] 1. **Add import** – Insert `import signal` at the top of `src/thuis/main.py`..
   - **What to do**: Edit the file to include the import alongside other stdlib imports.
   - **Acceptance Criteria**: The file compiles; `python -m thuy` (typo?) no import errors.
   - **Recommended Agent Profile**: `quick` – simple edit.
   - **Wave**: **Wave 1** (foundation, can run in parallel with other Wave 1 tasks).

- [x] 2. **Register SIGINT handler**: Add `signal.signal(signal.SIGINT, lambda sig, frame: sys.exit("\nInterrupted by user"))` as the first statement inside `main()`.
   - **What to do**: Locate the `def main():` definition and insert the handler as the first executable line.
   - **Acceptance Criteria**: Running the script and pressing Ctrl + C prints exactly `Interrupted by user` (preceded by a newline) with no traceback.
   - **Recommended Agent Profile**: `quick` – single line insertion.
   - **Wave**: **Wave 1** (parallel with Task 1 and Task 5).

- [x] 3. **Create SIGINT test**: Add `tests/test_ctrl_c_handler.py` that launches the script, sends SIGINT, and asserts clean output.
   - **What to do**: Write a pytest that uses `subprocess.Popen` to start the script, sleeps 0.5 s, sends `process.send_signal(signal.SIGINT)`, captures stdout/stderr, and checks for the message without a traceback.
   - **Acceptance Criteria**: Test passes on CI; exit code non‑zero and output contains `Interrupted by user` but no lines containing `Traceback`.
   - **Recommended Agent Profile**: `quick` – file creation.
   - **Wave**: **Wave 2** (depends on Task 2 being merged).

- [x] 4. **Update CI workflow**: Ensure the CI runs `pytest` so the new test is executed.
   - **What to do**: Edit `.github/workflows/ci.yml` (or create one if missing) to include a step `pytest`.
   - **Acceptance Criteria**: CI pipeline completes successfully with the new test included.
   - **Recommended Agent Profile**: `unspecified‑high` – touches CI configuration.
   - **Wave**: **Wave 2** (can run parallel with Task 3).

- [x] 5. **Document the change**: Add a note to `README.md` describing the new Ctrl + C behavior.
   - **What to do**: Insert a bullet under a new “Interrupt handling” section.
   - **Acceptance Criteria**: README contains the sentence `Pressing Ctrl + C now exits cleanly with "Interrupted by user" and no traceback.`
   - **Recommended Agent Profile**: `quick`.
   - **Wave**: **Wave 1** (parallel with Task 1 and Task 2).

---


---

## Final Verification Wave
- **F1**. **Plan Compliance Audit** – `oracle` checks that the plan’s scope, tasks, and acceptance criteria match the interview draft.
- **F2**. **Code Quality Review** – run linters, static analysis, and ensure no leftover `KeyboardInterrupt` handling conflicts.
- **F3**. **Real Manual QA** – execute the script, send Ctrl + C, verify clean message; run the new test and ensure it passes.
- **F4**. **Scope Fidelity Check** – confirm only the intended file was modified and no unrelated code was touched.

## Commit Strategy
- Single commit: `feat: add graceful SIGINT handler` including both code change and test.

## Success Criteria
- Running the script and pressing Ctrl + C prints exactly `Interrupted by user` (preceded by a newline) and **no traceback**.
- The new test passes, and the entire test suite remains green.
- Linting and static analysis report zero issues.
