# Cleanup & Logging — thuis VRT MAX downloader

## TL;DR

> **Quick Summary**: Dode code opruimen en gestructureerde logging (bestand + optioneel console) toevoegen aan de thuis VRT MAX downloader, zonder bestaande functionaliteit of tests te breken.
>
> **Deliverables**:
> - Verwijderde dode bestanden: `poc.py`, `thuis/downloader_yt.py`, `thuis/config.py`, `tests/test_downloader_yt.py`, `src/thuis/main.py.backup`, `__init__.py` (project root)
> - Vereenvoudigde `thuis/__init__.py` en `src/thuis/__init__.py`
> - Gestructureerde logging naar `logs/thuis.log` (INFO, altijd) met optionele console output via `--log-level`
> - Geüpdatete documentatie (README, website)
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Wave 1 (cleanup) → Wave 2 (logging) → Wave 3 (docs) → Final QA

---

## Context

### Original Request
> "Enkele verbeteringen: Ik wil logs kunnen raadplegen. Opkuis van wat we niet meer nodig hebben. Alles gaat door ./thuis.sh of thuis.bat, is poc.py nog nodig?"

### Interview Summary
**Key Discussions**:
- **poc.py**: Wordt nergens gebruikt (thuis.sh en thuis.bat roepen `src/thuis/main.py`). Tests gebruiken `sys.argv = ["poc.py", ...]` maar dat is cosmetisch — geen file dependency. → Verwijderen.
- **Root `thuis/` package**: `downloader_yt.py` en `config.py` worden niet gebruikt door main.py. Enkel `test_downloader_yt.py` importeert ze. → Verwijderen.
- **Logging**: Altijd naar bestand (`logs/thuis.log`) op INFO level. Console output optioneel via `--log-level` CLI flag (default uit).
- **print() vs logging**: Prints blijven behouden voor user-facing output (tests checken `captured.out`). Logging komt er naast.
- **Package structuur**: Huidige layout blijft (`src/thuis/`). Enkel `__init__.py` bestanden worden vereenvoudigd.

**Research Findings**:
- `test_season_expand.py` checkt `captured.out` — bevestigt dat prints moeten blijven.
- `src/thuis/__init__.py` heeft een `[DEBUG]` print die bij elke import vuurt — moet opgeruimd.
- `logs/` staat nog niet in `.gitignore` — moet toegevoegd.
- `thuis/__init__.py` importeert `downloader_yt` — moet aangepast voordat `downloader_yt.py` verwijderd wordt.

### Metis Review
**Key Gaps Identified** (all addressed):
- **Print→logging zou tests breken**: Opgelost — prints blijven, logging komt er naast.
- **Test import patterns**: Geverifieerd dat alle patterns overleven na cleanup.
- **`test_season_handling.py` importeert private functies**: Genoteerd, buiten scope.
- **`logs/` niet in `.gitignore`**: Toegevoegd aan plan.

---

## Work Objectives

### Core Objective
Dode code opruimen en gestructureerde logging (bestand + optioneel console) toevoegen aan de thuis VRT MAX downloader, zonder bestaande functionaliteit of tests te breken.

### Concrete Deliverables
- Schonere project structuur (geen dode bestanden, geen kruisverwijzingen in `__init__.py`)
- Gestructureerde logging naar `logs/thuis.log` (altijd, INFO level)
- Nieuwe CLI optie: `--log-level {DEBUG,INFO,WARNING,ERROR}` voor console output
- Geüpdatete README en website docs

### Definition of Done
- [ ] `git status` toont enkel verwachte wijzigingen (geen onbedoelde)
- [ ] `python -m pytest tests/ -v` — alle tests slagen (exclusief verwijderde `test_downloader_yt.py`)
- [ ] `python src/thuis/main.py --help` — werkt en toont `--log-level` optie
- [ ] `python src/thuis/main.py --dry-run https://www.vrt.be/vrtmax/a-z/test/1/` — logt naar `logs/thuis.log`
- [ ] Zonder `--log-level`: geen console output van logs, enkel log bestand
- [ ] Met `--log-level DEBUG`: console toont DEBUG+ messages

### Must Have
- Verwijder `poc.py`, `thuis/downloader_yt.py`, `thuis/config.py`, `tests/test_downloader_yt.py`, `src/thuis/main.py.backup`, `__init__.py` (root)
- Vereenvoudig `thuis/__init__.py` (verwijder `from . import downloader_yt`, behoud path redirect)
- Clean `src/thuis/__init__.py` (verwijder cross-ref naar root `thuis/`, verwijder DEBUG print)
- Voeg gestructureerde logging toe aan `src/thuis/main.py` (file handler + optionele console handler)
- `--log-level` CLI argument
- `logs/` toevoegen aan `.gitignore`
- `print()` statements behouden (niet vervangen door logging)
- Bestaande tests blijven slagen
- README + website/docs updaten

### Must NOT Have (Guardrails)
- **Geen** vervanging van `print()` door logging
- **Geen** wijzigingen aan `url_parser.py`, `classifier.py`, `metadata_fetcher.py`, `scene_namer.py`
- **Geen** verhuis van `src/thuis/` naar root
- **Geen** refactor van yt-dlp argument building logic
- **Geen** wijziging aan tests behalve `test_downloader_yt.py` verwijderen
- **Geen** log rotation (enkel append)

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALLE verificatie wordt door agents uitgevoerd.

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: tests-after (bestaande tests moeten blijven slagen; geen nieuwe tests voor logging)
- **Framework**: pytest
- **Agent-Executed QA**: ALTIJD — zie QA scenarios per task

### QA Policy
Elke task heeft agent-uitvoerbare QA scenarios. Bewijs opgeslagen in `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Bestandsoperaties**: Bash — `ls`, `cat`, `git status` voor verificatie
- **CLI werking**: Bash — run `python src/thuis/main.py` met argumenten, check exit code
- **Log verificatie**: Bash — `cat logs/thuis.log` en `test -f logs/thuis.log`
- **Import verificatie**: Bash — `python -c "from thuis.main import ..."`

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — cleanup, max parallel):
├── Task 1: Delete dead files (poc.py, downloader_yt.py, config.py, test_downloader_yt.py, backup, root __init__)
├── Task 2: Simplify thuis/__init__.py (remove downloader_yt import, keep path redirect)
├── Task 3: Clean src/thuis/__init__.py (remove cross-ref, remove DEBUG print)
└── Task 4: Clear stale __pycache__ directories

Wave 2 (After Wave 1 — logging):
├── Task 5: Add logs/ to .gitignore
├── Task 6: Add logging setup + --log-level to main.py
└── Task 7: Verify logging works (file + console via --log-level)

Wave 3 (After Wave 2 — docs):
├── Task 8: Update README (remove poc.py ref, update structure, add logging section)
└── Task 9: Update website/docs/development.md

Wave FINAL (After ALL tasks — parallel review + user ok):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Full test suite + QA scenarios
├── Task F3: Scope fidelity check
└── -> Present results -> Get explicit user ok

Critical Path: Task 1 → Task 5 → Task 6 → Task 7 → Task F1-F3
Parallel Speedup: ~50% faster (Wave 1 heeft 4 parallelle taken)
Max Concurrent: 4 (Wave 1)
```

### Dependency Matrix
- **1-4**: None — Wave 1, all parallel
- **5**: 1, 2, 3 → 6 (blocks)
- **6**: 5 → 7 (blocks)
- **7**: 6 → 8, 9 (blocks)
- **8, 9**: 7 — Wave 3, parallel
- **F1-F3**: 8, 9 — Final wave, parallel

### Agent Dispatch Summary
- **Wave 1**: 4 tasks — all `quick`
- **Wave 2**: 3 tasks — T5 `quick`, T6 `unspecified-high`, T7 `unspecified-high`
- **Wave 3**: 2 tasks — T8 `writing`, T9 `writing`
- **Final**: 3 tasks — F1 `oracle`, F2 `unspecified-high`, F3 `deep`

---

## TODOs

- [x] 1. Delete dead files

  **What to do**:
  - Delete files (use `git rm` for tracked files, `rm` for untracked):
    - `poc.py` — obsolete POC entry point, no code imports it
    - `thuis/downloader_yt.py` — dead module, not used by main.py
    - `thuis/config.py` — dead module, not used by main.py
    - `tests/test_downloader_yt.py` — tests the dead module
    - `src/thuis/main.py.backup` — backup file, not needed
    - `__init__.py` (project root) — unnecessary path manipulation
  - After deletion: `git status` to verify

  **Must NOT do**:
  - Don't delete `thuis/__init__.py` — needed for `python -m thuis.main`
  - Don't delete any `src/thuis/` files

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file deletions, no complex logic
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Tasks 5, 6, 7, 8, 9
  - **Blocked By**: None

  **References**:
  - `git rm` for tracked files, `rm` for untracked
  - Verify with `git status`

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Verify dead files are removed
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: ls poc.py 2>&1 && echo EXISTS || echo GONE
      2. Run: ls thuis/downloader_yt.py 2>&1 && echo EXISTS || echo GONE
      3. Run: ls thuis/config.py 2>&1 && echo EXISTS || echo GONE
      4. Run: ls tests/test_downloader_yt.py 2>&1 && echo EXISTS || echo GONE
      5. Run: ls src/thuis/main.py.backup 2>&1 && echo EXISTS || echo GONE
      6. Run: ls __init__.py 2>&1 && echo EXISTS || echo GONE
    Expected Result: All 6 files report "GONE"
    Evidence: .omo/evidence/task-1-deleted-files.txt

  Scenario: Verify thuis/__init__.py still exists (NOT deleted)
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: test -f thuis/__init__.py && echo EXISTS || echo GONE
    Expected Result: "EXISTS"
    Evidence: .omo/evidence/task-1-init-kept.txt
  ```

  **Commit**: YES
  - Message: `chore: remove dead files (poc.py, downloader_yt, config, backup, root __init__)`
  - Files: All deleted files
  - Pre-commit: `python -m pytest tests/ -v --ignore=tests/test_downloader_yt.py -x`

- [x] 2. Simplify `thuis/__init__.py`

  **What to do**:
  - Current content:
    ```python
    import os, sys
    package_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'thuis')
    if os.path.isdir(package_dir):
        __path__.append(package_dir)
    try:
        from . import downloader_yt  # noqa: F401
    except ImportError:
        pass
    ```
  - Remove the `try/except` block for `from . import downloader_yt`
  - Keep the path redirect to `src/thuis/` (needed for `python -m thuis.main`)
  - Final content:
    ```python
    import os
    package_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'thuis')
    if os.path.isdir(package_dir):
        __path__.append(package_dir)
    ```

  **Must NOT do**:
  - Don't remove the redirect logic — `python -m thuis.main` depends on it

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple edit, one file, 2 lines to remove
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Tasks 5, 6, 7
  - **Blocked By**: None

  **References**:
  - `thuis/__init__.py` — current file to edit

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Verify simplified __init__.py imports correctly
    Tool: Bash
    Preconditions: Task 1 completed (files deleted)
    Steps:
      1. Run: cat thuis/__init__.py
      2. Run: python -c "import thuis; print('OK')" 2>&1
    Expected Result: thuis/__init__.py has no import statements (only path.append). "OK" prints without ImportError.
    Evidence: .omo/evidence/task-2-init-simplified.txt

  Scenario: Verify python -m thuis.main still works
    Tool: Bash
    Preconditions: Task 1 completed
    Steps:
      1. Run: python -m thuis.main --help
    Expected Result: Exit 0, shows help text
    Evidence: .omo/evidence/task-2-module-help.txt
  ```

  **Commit**: NO (groups with Task 1)
  - Files: `thuis/__init__.py`

- [x] 3. Clean `src/thuis/__init__.py`

  **What to do**:
  - Current content:
    ```python
    import os, sys, pathlib
    print(f"[DEBUG] Loading src/thuis __init__.py from {__file__}")
    project_root = pathlib.Path(__file__).resolve().parents[2]
    parent_package = project_root / "thuis"
    if parent_package.is_dir():
        __path__.append(str(parent_package))
    ```
  - Remove the DEBUG print line
  - Remove the cross-reference to the root `thuis/` package (no longer needed after cleanup)
  - Remove unused `sys` import
  - Final content: empty `__init__.py` (or just a docstring/comment)

  **Must NOT do**:
  - Don't delete the file entirely — needed to mark `src/thuis/` as a Python package

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple edit, one file
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Tasks 5, 6, 7
  - **Blocked By**: None

  **References**:
  - `src/thuis/__init__.py` — current file to edit

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: No DEBUG print on import
    Tool: Bash
    Preconditions: Tasks 1, 2 completed
    Steps:
      1. Run: python -c "from thuis.main import get_credentials; print('OK')" 2>&1
    Expected Result: No "[DEBUG]" line in output. Just "OK".
    Evidence: .omo/evidence/task-3-no-debug-print.txt

  Scenario: Imports from src/thuis still work
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: python -c "from thuis.url_parser import parse_vrt_url; print('OK')" 2>&1
    Expected Result: Exit 0, prints "OK"
    Evidence: .omo/evidence/task-3-imports-work.txt
  ```

  **Commit**: NO (groups with Task 1)
  - Files: `src/thuis/__init__.py`

- [x] 4. Clear stale `__pycache__` directories

  **What to do**:
  - Remove all `__pycache__` directories and `.pyc` files that may reference deleted modules
  - Run: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete`
  - This clears bytecode cache from deleted modules (e.g., `downloader_yt`)
  - After cleanup: run a quick `python -c "from thuis.main import *"` to verify no stale cache issues

  **Must NOT do**:
  - Don't modify any source files — only remove cache artifacts

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: None (cosmetic cleanup)
  - **Blocked By**: None

  **References**: none

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: No __pycache__ dirs remain
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: find . -type d -name __pycache__ 2>/dev/null; echo "DONE"
    Expected Result: No __pycache__ directories found (or only .git ones)
    Evidence: .omo/evidence/task-4-pycache-cleared.txt
  ```

  **Commit**: NO (groups with Task 1)
  - Files: N/A (cache files, gitignored)

- [x] 5. Add `logs/` to `.gitignore`

  **What to do**:
  - Add `logs/` entry to `.gitignore` with a comment `# Log files`
  - Verify: `git check-ignore logs/thuis.log` returns the path
  - Create `logs/` directory (can be empty, or created on first run by logging setup)

  **Must NOT do**:
  - Don't commit the `logs/` directory itself (it's gitignored)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 6)
  - **Blocks**: None (independent from Task 6 but related)
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `.gitignore` — file to edit
  - Current content starts with `.venv/`, `media/`, `.omo/`

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: logs/ is gitignored
    Tool: Bash
    Preconditions: logs/ directory exists
    Steps:
      1. Run: mkdir -p logs
      2. Run: git check-ignore logs/thuis.log
    Expected Result: `git check-ignore` returns `logs/thuis.log`
    Evidence: .omo/evidence/task-5-gitignore-logs.txt
  ```

  **Commit**: YES (standalone commit)
  - Message: `chore: add logs/ to .gitignore`
  - Files: `.gitignore`

- [x] 6. Add logging setup + `--log-level` to `src/thuis/main.py`

  **What to do**:
  - Add a `setup_logging(level: str | None = None)` function that:
    - Creates `logs/` directory if it doesn't exist (using `Path("logs").mkdir(parents=True, exist_ok=True)`)
    - Sets up a file handler: `logs/thuis.log`, level INFO, format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
    - If `level` is provided (from `--log-level`): adds a console handler (StreamHandler) at that level
    - Returns the logger: `logging.getLogger('thuis')`
    - Uses `RotatingFileHandler` is nice-to-have but per guardrails: simple append is fine
  - Add `--log-level` argument to argparse:
    ```python
    parser.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None, help="Enable console logging at specified level (default: file only)")
    ```
  - Call `setup_logging(args.log_level)` early in `main()`, before any operations
  - Replace some bare `print()` with `logger.info()` calls **only for diagnostic messages**:
    - `print(f"Warning: could not apply patch: {e}", flush=True)` → `logger.warning(...)`
    - `print(f"Warning: Failed to process {url}: {e}", flush=True)` → `logger.warning(...)`
    - **Keep** `print(f"[DRY-RUN] ...")` — user-facing output, tests check this
    - **Keep** `print("Running:", ...)` — user-facing output
    - **Keep** `print("\nInterrupted")` — user-facing

  **Must NOT do**:
  - Don't replace the `[DRY-RUN]` and `Running:` prints (tests check `captured.out`)
  - Don't change filename output format
  - Don't add log rotation (simple append only)
  - Don't modify anything outside `main.py`

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding of argparse, logging module, file I/O
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (depends on Wave 1 cleanup)
  - **Blocks**: Task 7
  - **Blocked By**: Task 5

  **References**:
  - `src/thuis/main.py` — file to edit
  - Python logging docs: `https://docs.python.org/3/library/logging.html` — for handler setup
  - `src/thuis/main.py` line 410-417: argparse setup — add new argument here
  - `src/thuis/main.py` line 459-462: existing patch print → replace with logger.warning
  - `src/thuis/main.py` line 542-543: existing Warning print → replace with logger.warning

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: --log-level in help text
    Tool: Bash
    Preconditions: All Wave 1 tasks done
    Steps:
      1. Run: python src/thuis/main.py --help 2>&1
      2. Grep output for "log-level"
    Expected Result: "--log-level" appears in help text with choices DEBUG, INFO, WARNING, ERROR
    Evidence: .omo/evidence/task-6-help-shows-loglevel.txt

  Scenario: Log file created on dry-run (default, no --log-level)
    Tool: Bash
    Preconditions: All Wave 1 tasks done, logs/ not present
    Steps:
      1. Run: rm -rf logs
      2. Run: python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test-show/1/' 2>&1 || true
      3. Run: cat logs/thuis.log 2>&1 || echo "NO LOG FILE"
    Expected Result: logs/thuis.log exists with content (at least one log line, no ERROR level necessary)
    Evidence: .omo/evidence/task-6-log-file-created.txt

  Scenario: No console logs without --log-level
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: output=$(python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>&1); echo "$output"
      2. Check: output does NOT contain log lines with "[INFO]" or "[DEBUG]"
    Expected Result: Console only shows user-facing output (DRY-RUN, Running:), not log lines
    Evidence: .omo/evidence/task-6-no-console-logs.txt

  Scenario: Console logs WITH --log-level DEBUG
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: output=$(python src/thuis/main.py --dry-run --log-level DEBUG 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>&1); echo "$output"
      2. Check: output contains "[DEBUG]" or "[INFO]" log lines
    Expected Result: Console shows log lines with timestamps and levels
    Evidence: .omo/evidence/task-6-console-logs-debug.txt

  Scenario: existing prints still visible in stdout
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: output=$(python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>&1); echo "$output"
      2. Check: output contains "[DRY-RUN]" or "Running:"
    Expected Result: Existing print() output is still visible in stdout
    Evidence: .omo/evidence/task-6-prints-still-work.txt
  ```

  **Commit**: YES (standalone commit)
  - Message: `feat: add structured logging to file with --log-level console option`
  - Files: `src/thuis/main.py`
  - Pre-commit: `python -m pytest tests/ -v --ignore=tests/test_downloader_yt.py -x`

- [x] 7. Verify logging works end-to-end

  **What to do**:
  - Verify the complete logging setup:
    1. Clean log file: `rm -f logs/thuis.log`
    2. Run with dry-run: `python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test/1/'`
    3. Check log file has content with expected format
    4. Check warning messages are logged
    5. Test with `--log-level DEBUG` shows console output
  - Verify both file and console handlers produce correct format

  **Must NOT do**:
  - Don't modify any files — pure verification task

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential after Task 6
  - **Blocks**: Tasks 8, 9
  - **Blocked By**: Task 6

  **References**:
  - `logs/thuis.log` — expected output file

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Log format verification
    Tool: Bash
    Preconditions: Task 6 completed, run dry-run once
    Steps:
      1. Run: head -5 logs/thuis.log 2>&1
      2. Check: lines match format "2025-07-06 HH:MM:SS [LEVEL] thuis: message"
    Expected Result: Log lines follow expected timestamp format
    Evidence: .omo/evidence/task-7-log-format.txt

  Scenario: --log-level DEBUG affects console
    Tool: Bash
    Preconditions: Task 6 completed
    Steps:
      1. Run: python src/thuis/main.py --dry-run --log-level DEBUG 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>&1 | grep -c "\[DEBUG\]"
      2. Run: python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>&1 | grep -c "\[DEBUG\]"
    Expected Result: | First run output > 0 (DEBUG shown). Second run output == 0 (no DEBUG without flag)
    Evidence: .omo/evidence/task-7-loglevel-contrast.txt
  ```

  **Commit**: NO (verification only)

- [x] 8. Update README

  **What to do**:
  - Update project structure section in `README.md`:
    - Remove `poc.py` line
    - Add `logs/` to the structure (with description "Log files (gitignored)")
    - Update description: `poc.py` entry is gone, add logging entry
  - Update any reference to `poc.py` in the README text
  - Logging section (optional): mention that logs go to `logs/thuis.log` and `--log-level` is available
  - Use `read` to get current README content first, then edit precisely

  **Must NOT do**:
  - Don't rewrite the entire README — only targeted updates
  - Don't change installation or usage instructions (unless they reference poc.py)

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 9)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: None (independent doc tasks)

  **References**:
  - `README.md` — current file
  - Read file first, then edit sections that reference `poc.py` or project structure

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: No poc.py references in README
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: grep -n "poc.py" README.md || echo "NO_MATCHES"
    Expected Result: "NO_MATCHES" — no references to poc.py remain
    Evidence: .omo/evidence/task-8-readme-no-poc.txt

  Scenario: logs/ mentioned in project structure
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: grep -c "logs/" README.md
    Expected Result: Output >= 1 (logs/ is mentioned somewhere in README)
    Evidence: .omo/evidence/task-8-readme-logs.txt
  ```

  **Commit**: YES (groups with Task 9)
  - Message: `docs: update README and development docs for cleanup + logging`
  - Files: `README.md`, `website/docs/development.md`

- [x] 9. Update `website/docs/development.md`

  **What to do**:
  - Update project structure in `website/docs/development.md`:
    - Remove `poc.py` line
    - No need to add `logs/` to this condensed structure (it's a high-level overview)
  - Use `read` to get current file content first

  **Must NOT do**:
  - Don't change installation or test instructions

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 8)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: None

  **References**:
  - `website/docs/development.md` — current file

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: No poc.py references in development.md
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: grep -n "poc.py" website/docs/development.md || echo "NO_MATCHES"
    Expected Result: "NO_MATCHES" — no references to poc.py remain
    Evidence: .omo/evidence/task-9-dev-docs-no-poc.txt
  ```

  **Commit**: NO (groups with Task 8)
  - Files: `website/docs/development.md`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 3 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run test, check git log). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Full Test Suite + QA** — `unspecified-high`
  Run full test suite (excluding deleted test_downloader_yt.py):
  - `python -m pytest tests/ -v --ignore=tests/test_downloader_yt.py`
  Execute ALL QA scenarios from ALL tasks — follow exact steps, capture evidence.
  Save to `.omo/evidence/final-qa/`.
  Output: `Tests [N pass/N fail] | QA Scenarios [N/N pass] | VERDICT`

- [x] F3. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in scope was done (no missing), nothing beyond scope was done (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Commit 1** (Wave 1): `chore: remove dead files (poc.py, downloader_yt, config, backup, root __init__)` — includes init.py simplifications
- **Commit 2** (Task 5): `chore: add logs/ to .gitignore`
- **Commit 3** (Task 6): `feat: add structured logging to file with --log-level console option`
- **Commit 4** (Tasks 8+9): `docs: update README and development docs for cleanup + logging`

---

## Success Criteria

### Verification Commands
```bash
# Full test suite passes
python -m pytest tests/ -v --ignore=tests/test_downloader_yt.py -x

# Entry points work
python src/thuis/main.py --help
python -m thuis.main --help
./thuis.sh --help

# Log file created
python src/thuis/main.py --dry-run 'https://www.vrt.be/vrtmax/a-z/test/1/' 2>/dev/null
test -f logs/thuis.log && echo "LOG EXISTS"

# Dead files gone
ls poc.py 2>&1 | grep -q "No such file" && echo "POC REMOVED"

# No DEBUG print on import
python -c "from thuis.main import get_credentials; print('OK')" 2>&1 | grep -v "\[DEBUG\]"
```

### Final Checklist
- [x] All dead files removed
- [x] `thuis/__init__.py` simplified (no downloader_yt import)
- [x] `src/thuis/__init__.py` cleaned (no DEBUG print, no cross-ref)
- [x] `logs/` in `.gitignore`
- [x] Logging works: file always, console via `--log-level`
- [x] All `print()` statements preserved
- [x] README updated (no poc.py refs)
- [x] website/docs/development.md updated (no poc.py refs)
- [x] All tests pass
- [x] `python -m thuis.main --help` works
