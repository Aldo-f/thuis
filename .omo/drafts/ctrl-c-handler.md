# Draft: Graceful Ctrl+C handling

## Core Objective
Provide a clean termination with the message **“Interrupted by user”** when the user aborts the script via Ctrl + C, without emitting a traceback.

## Scope IN/OUT
- **IN**: Add `import signal` and register a global `SIGINT` handler in the main entry point (`main()`), ensuring the yt‑dlp subprocess receives the same signal.
- **OUT**: No refactoring of existing logic, no additional `KeyboardInterrupt` handlers beyond the safety net, and no changes to logging or other unrelated code.

## Test Strategy (Tests‑after)
- After adding the signal handler, write a test that runs the script, sends a SIGINT, and asserts that the exit code is non‑zero and the output contains `Interrupted by user` without a traceback.

## Open Questions
None

## Requirements (confirmed)
- Ctrl+C must produce a tidy message, no traceback.
- Simple global handler via `signal.signal()`.
- yt‑dlp subprocess must also stop (process‑group SIGINT from terminal).

## Technical Decisions
- Implementation: `signal.signal(signal.SIGINT, lambda sig, frame: sys.exit("\nInterrupted by user"))`
- Keep existing `except KeyboardInterrupt` as a safety net (harmless if unreachable).
- No extra try/except around the expansion phase; the signal handler catches everything.
- yt‑dlp receives SIGINT directly from the terminal (same process group) and stops accordingly.

## Scope Boundaries
- **INCLUDE**: Single rule change – add `import signal` and the `signal.signal()` call in `main()`.
- **EXCLUDE**: No refactors, no additional `KeyboardInterrupt` handlers, no logging changes.
