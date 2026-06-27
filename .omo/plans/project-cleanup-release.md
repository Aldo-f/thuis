Scenario: Verify basic functionality works after restructuring
    Tool: Bash
    Preconditions: Package structure created and tests moved (Tasks 1-2 complete)
    Steps:
      1. Execute: `python -m pytest tests/test_poc.py -v`
      2. Capture output and exit code
      3. Assert that exit code is 0
      4. Assert that output shows "5 passed"
    Expected Result: All 5 unit tests pass
    Failure Indicators: Non-zero exit code, or not exactly "5 passed" in output
    Evidence: .omo/evidence/task-3-verify-unit-tests.txt

  \`\`\`
  Scenario: Verify integration tests pass after restructuring
    Tool: Bash
    Preconditions: Package structure created and tests moved (Tasks 1-2 complete)
    Steps:
      1. Execute: `python -m pytest tests/test_real_download.py -v`
      2. Capture output and exit code
      3. Assert that exit code is 0
      4. Assert that output shows "4 passed"
    Expected Result: All 4 integration tests pass
    Failure Indicators: Non-zero exit code, or not exactly "4 passed" in output
    Evidence: .omo/evidence/task-3-verify-integration-tests.txt

  \`\`\`
  Scenario: Verify main.py can be imported and basic functions work
    Tool: Bash
    Preconditions: Package structure created (Task 1 complete)
    Steps:
      1. Execute: `python -c "import sys; sys.path.insert(0, '.'); from thuis.main import get_credentials; print('Import OK')"`
      2. Execute: `python -c "import sys; sys.path.insert(0, '.'); from thuis.main import build_yt_dlp_args; print('Import OK')"`
      3. Execute: `python -c "import sys; sys.path.insert(0, '.'); from thuis.main import get_yt_dlp_cmd; print('Import OK')"`
      4. Execute: `python -c "import sys; sys.path.insert(0, '.'); from thuis.main import main; print('Import OK')"`
    Expected Result: All imports succeed without error
    Failure Indicators: Any ImportError or module not found error
    Evidence: .omo/evidence/task-3-verify-imports.txt

  Commit: NO (part of Wave 1 preparation)

- [x] 4. Run all tests to confirm nothing broken after restructuring

  What to do:
  - Run the full test suite (unit + integration)
  - Verify all 9 tests pass

  Must NOT do:
  - Do not alter any test logic
  - Do not change requirements.txt
  - Do not modify any source code yet

  Recommended Agent Profile:
  > Selecting 'unspecified-high' category for comprehensive test execution.
  - **Category**: `unspecified-high`
    - Reason: Running full test suite which may take significant time
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for test runs

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 1-3)
  - Parallel Group: Wave 1 (Tasks 1-4)
  - Blocks: Task 5
  - Blocked By: Task 3

  References:

  > Executor needs to know test command to run.

  Pattern References:
  - tests/test_poc.py
  - tests/test_real_download.py

  Acceptance Criteria:
  - **If TDD**: N/A (this is verification)
  - All 9 tests pass (5 unit + 4 integration)
  - No test failures or errors
  - Total execution time recorded for reference

  QA Scenarios:

  \`\`\`
  Scenario: Verify full test suite passes after restructuring
    Tool: Bash
    Preconditions: Package structure created and tests moved (Tasks 1-3 complete)
    Steps:
      1. Execute: `python -m pytest tests/ -v`
      2. Capture output and exit code
      3. Assert that exit code is 0
      4. Assert that output shows "9 passed"
      5. Record total execution time for reference
    Expected Result: All 9 tests pass
    Failure Indicators: Non-zero exit code, or not exactly "9 passed" in output
    Evidence: .omo/evidence/task-4-verify-all-tests.txt
  \`\`\`

  Commit: NO (part of Wave 1 preparation)

- [x] 5. Remove legacy/ directory

  What to do:
  - Delete the legacy/ directory entirely
  - Verify it's gone
  - Ensure .gitignore still ignores legacy/ (should already be there)

  Must NOT do:
  - Do not remove any other directories
  - Do not modify .gitignore to unignore legacy/
  - Do not remove .omo/ or .specify/ directories

  Recommended Agent Profile:
  > Selecting 'quick' category for directory removal.
  - **Category**: `quick`
    - Reason: Simple directory removal operation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for rm -rf

  Parallelization:
  - Can Run In Parallel: NO (should be after verification)
  - Parallel Group: Wave 2 (Tasks 5-8)
  - Blocks: Task 6
  - Blocked By: Task 4

  References:

  > Executor needs to know the directory to remove.

  Pattern References:
  - legacy/ (directory to remove)
  - .gitignore (to verify ignore rule exists)

  Acceptance Criteria:
  - **If TDD**: N/A (this is a deletion)
  - Directory legacy/ does not exist
  - .gitignore still contains a line ignoring legacy/ (typically "legacy/" or "legacy/**")
  - No error messages during removal

  QA Scenarios:

  \`\`\`
  Scenario: Verify legacy directory removed successfully
    Tool: Bash
    Preconditions: All tests passing (Task 4 complete)
    Steps:
      1. Execute: `rm -rf legacy/`
      2. Execute: `test ! -d legacy/ && echo "SUCCESS" || echo "FAILED"`
      3. Execute: `grep -q "legacy/" .gitignore && echo "Gitignore OK" || echo "Gitignore missing legacy/"`
      4. Assert that step 2 outputs "SUCCESS"
      5. Assert that step 3 outputs "Gitignore OK"
    Expected Result: legacy/ directory removed, .gitignore still ignores it
    Failure Indicators: legacy/ still exists, or .gitignore missing legacy/ ignore rule
    Evidence: .omo/evidence/task-5-verify-legacy-removed.txt
  \`\`\`

  Commit: NO (part of Wave 2 preparation)

- [x] 6. Create wrapper scripts (thuis.sh and thuis.bat)

  What to do:
  - Create thuis.sh (Linux/macOS wrapper)
  - Create thuis.bat (Windows wrapper)
  - Both should:
    * Check if Python is available
    * If not, print helpful message and exit
    * If yes, execute python src/thuis/main.py with all arguments
    * Forward all command-line arguments unchanged
    * Use proper path resolution to find main.py relative to wrapper location
  - Make thuis.sh executable

  Must NOT do:
  - Do not alter the actual python command or arguments
  - Do not add auto-install functionality (only guide)
  - Do not hardcode absolute paths
  - Do not make assumptions about where the project is installed

  Recommended Agent Profile:
  > Selecting 'quick' category for script creation.
  - **Category**: `quick`
    - Reason: Simple shell/batch script creation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for file creation

  Parallelization:
  - Can Run In Parallel: YES (both wrappers can be created independently)
  - Parallel Group: Wave 2 (Tasks 5-8)
  - Blocks: Task 7
  - Blocked By: Task 5

  References:

  > Executor needs to know exact script content and placement.

  Pattern References:
  - Common wrapper patterns for Python CLI tools
  - Existing poc.py for understanding of how arguments should be forwarded

  Acceptance Criteria:
  - **If TDD**: N/A (this is infrastructure creation)
  - File thuis.sh exists and is executable
  - File thuis.bat exists
  - thuis.sh contains proper shebang and logic
  - thuis.bat contains proper batch file logic
  - Both scripts correctly forward arguments to python src/thuis/main.py
  - Both scripts check for Python availability

  QA Scenarios:

  \`\`\`
  Scenario: Verify thuis.sh created and functional
    Tool: Bash
    Preconditions: legacy/ removed (Task 5 complete)
    Steps:
      1. Execute: `cat > thuis.sh << 'EOF'\n#!/bin/bash\nSCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\nif ! command -v python3 &> /dev/null; then\n    echo \"Error: Python 3 is required but not installed.\"\n    echo \"Please install Python 3 from https://www.python.org/downloads/\"\n    echo \"Then run this script again.\"\n    exit 1\nfi\n\nexec python3 \"$SCRIPT_DIR/src/thuis/main.py\" \"$@\"\nEOF\n"
      2. Execute: `chmod +x thuis.sh`
      3. Execute: `./thuis.sh --help | head -5`
      4. Assert that step 3 outputs usage information (not error about missing Python)
    Expected Result: thuis.sh created, executable, and functional
    Failure Indicators: File not created, not executable, or fails to run main.py
    Evidence: .omo/evidence/task-6-verify-thuis-sh.txt
  \`\`\`

  \`\`\`
  Scenario: Verify thuis.bat created and functional
    Tool: Bash
    Preconditions: legacy/ removed (Task 5 complete)
    Steps:
      1. Execute: `cat > thuis.bat << 'EOF'\n@echo off\nset SCRIPT_DIR=%~dp0\nwhere python3 >nul 2>&1\nif errorlevel 1 (\n    echo Error: Python 3 is required but not installed.\n    echo Please install Python 3 from https://www.python.org/downloads/\n    echo Then run this script again.\n    exit /b 1\n)\n\"%SCRIPT_DIR%src\\thuis\main.py\" %*\nEOF\n"
      2. Execute: `call thuis.bat --help | head -5`
      3. Assert that step 2 outputs usage information (not error about missing Python)
    Expected Result: thuis.bat created and functional
    Failure Indicators: File not created, or fails to run main.py
    Evidence: .omo/evidence/task-6-verify-thuis-bat.txt
  \`\`\`

  Commit: NO (part of Wave 2 preparation)

- [x] 7. Add Python version check to wrappers (if not already included above)

  What to do:
  - This is already included in Task 6 - the wrappers check for Python availability
  - No additional action needed beyond what's described in Task 6

  Must NOT do:
  - Do not add auto-install functionality
  - Do not change the core python command execution

  Recommended Agent Profile:
  > Selecting 'quick' category as this is part of wrapper creation.
  - **Category**: `quick`
    - Reason: Part of wrapper script creation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for this check

  Parallelization:
  - Can Run In Parallel: YES (part of Wave 2)
  - Parallel Group: Wave 2 (Tasks 5-8)
  - Blocks: Task 8
  - Blocked By: Task 6

  References:

  > Executor knows this is covered in Task 6.

  Pattern References:
  - Same as Task 6

  Acceptance Criteria:
  - **If TDD**: N/A (covered in Task 6)
  - See Task 6 acceptance criteria

  QA Scenarios:
  - See Task 6 QA scenarios

  Commit: NO (part of Wave 2 preparation)

- [x] 8. Verify wrappers work correctly

  What to do:
  - Test that both wrappers correctly detect missing Python
  - Test that both wrappers correctly execute main.py when Python is available
  - Verify argument forwarding works

  Must NOT do:
  - Do not test actual downloads (too slow for verification)
  - Do not modify the wrappers after creation
  - Do not test with missing main.py (assume it's present)

  Recommended Agent Profile:
  > Selecting 'unspecified-high' category for comprehensive wrapper testing.
  - **Category**: `unspecified-high`
    - Reason: Testing both wrapper scripts thoroughly
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for wrapper tests

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 6-7)
  - Parallel Group: Wave 2 (Tasks 5-8)
  - Blocks: Task 9
  - Blocked By: Task 7

  References:

  > Executor needs to know test commands for wrappers.

  Pattern References:
  - thuis.sh
  - thuis.bat
  - src/thuis/main.py

  Acceptance Criteria:
  - **If TDD**: N/A (this is infrastructure verification)
  - thuis.sh and thuis.bat both exist and are executable/valid
  - Both scripts correctly report missing Python when python3 not found
  - Both scripts correctly execute main.py when Python is available
  - Both scripts correctly forward arguments (tested with --help)
  - Both scripts use relative path to find src/thuis/main.py

  QA Scenarios:

  \`\`\`
  Scenario: Verify wrappers handle missing Python correctly
    Tool: Bash
    Preconditions: Wrappers created (Task 6 complete)
    Steps:
      1. Execute: `PATH=\"\" ./thuis.sh --help 2>&1 | head -1`
      2. Execute: `SET PATH=& thuis.bat --help 2>&1 | head -1` (Windows syntax conceptually)
      3. Assert that both outputs contain "Error: Python 3 is required"
    Expected Result: Both wrappers properly detect and report missing Python
    Failure Indicators: Wrappers don't show error message, or try to run Python anyway
    Evidence: .omo/evidence/task-8-verify-wrapper-python-check.txt
  \`\`\`

  \`\`\`
  Scenario: Verify wrappers forward arguments correctly
    Tool: Bash
    Preconditions: Wrappers created and Python available (Task 6 complete)
    Steps:
      1. Execute: `./thuis.sh --help | grep -i usage`
      2. Execute: `python3 src/thuis/main.py --help | grep -i usage`
      3. Assert that both outputs contain similar usage information
      4. Execute: `./thuis.sh --version 2>&1 | head -1`
      5. Execute: `python3 src/thuis/main.py --version 2>&1 | head -1`
      6. Assert that both outputs are identical (or both show version)
    Expected Result: Both wrappers correctly forward --help and --version to main.py
    Failure Indicators: Outputs differ significantly, or wrappers fail to execute
    Evidence: .omo/evidence/task-8-verify-wrapper-argument-forwarding.txt
  \`\`\`

  Commit: NO (part of Wave 2 preparation)

- [x] 9. Update README.md

  What to do:
  - Rewrite README.md with clear install/usage instructions
  - Include sections: Overview, Installation, Usage, Examples
  - Explain how to use the wrappers (thuis.sh/thuis.bat)
  - Explain the Python requirement and how to get it
  - Explain what the tool does (downloads VRT MAX videos)
  - Keep tone friendly and accessible for non-technical users

  Must NOT do:
  - Do not remove existing useful information
  - Do not make misleading claims about functionality
  - Do not make it overly technical - keep it accessible

  Recommended Agent Profile:
  > Selecting 'writing' category for documentation creation.
  - **Category**: `writing`
    - Reason: Creating clear, user-friendly documentation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for file editing

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 8)
  - Parallel Group: Wave 3 (Tasks 9-12)
  - Blocks: Task 10
  - Blocked By: Task 8

  References:

  > Executor needs to know what to include in README.

  Pattern References:
  - Existing README.md (to preserve useful parts)
  - Common open-source project READMEs
  - The actual functionality of main.py

  Acceptance Criteria:
  - **If TDD**: N/A (this is documentation)
  - File README.md exists
  - File contains clear overview of what the tool does
  - File explains how to use it (via wrappers or direct python)
  - File mentions Python 3 requirement
  - File gives at least one example command
  - Tone is friendly and accessible
  - No misleading claims about functionality

  QA Scenarios:

  \`\`\`
  Scenario: Verify README.md updated with essential information
    Tool: Bash
    Preconditions: Wrappers working (Task 8 complete)
    Steps:
      1. Execute: `grep -i \"what this tool does\" README.md || echo \"Missing description_missing_description`
      2. Execute: `grep -i \"how to use\" README.md || echo \"Missing usage section\"`
      3. Execute: `grep -i \"python.*required\" README.md || echo \"Missing Python requirement\"`
      4. Execute: `grep -i \"thuis.sh\\|thuis.bat\" README.md || echo \"Missing wrapper info\"`
      5. Execute: `grep -i \"example\" README.md || echo \"Missing example\"`
      6. Assert that none of the steps return the error messages
    Expected Result: README contains all essential information sections
    Failure Indicators: Any of the error messages appear
    Evidence: .omo/evidence/task-9-verify-readme-content.txt
  \`\`\`

  Commit: NO (part of Wave 3 preparation)

- [x] 10. Update Spec Kit specs

  What to do:
  - Update .specify/specs/vrt-dlp-downloader.md to match current implementation
  - Update command name from `download` (downloader.py) to reflect main.py usage
  - Update inputs/outputs to match main.py arguments
  - Update environment requirements to match current credential handling
  - Update usage instructions to show how to use the wrappers or direct python

  Must NOT do:
  - Do not remove useful existing information
  - Do not make up functionality that doesn't exist
  - Do not change the actual implementation - only update docs to match

  Recommended Agent Profile:
  > Selecting 'writing' category for documentation update.
  - **Category**: `writing`
    - Reason: Updating specification documentation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for file editing

  Parallelization:
  - Can Run In Parallel: NO (depends on Task 9)
  - Parallel Group: Wave 3 (Tasks 9-12)
  - Blocks: Task 11
  - Blocked By: Task 9

  References:

  > Executor needs to know current main.py functionality to document correctly.

  Pattern References:
  - Existing .specify/specs/vrt-dlp-downloader.md
  - src/thuis/main.py (to understand actual interface)
  - Common Spec Kit spec formats

  Acceptance Criteria:
  - **If TDD**: N/A (this is documentation update)
  - File .specify/specs/vrt-dlp-downloader.md exists
  - File correctly describes the `download` command (now via main.py)
  - File lists correct inputs: URL (string), --file (file path), --output-dir (directory path)
  - File lists correct outputs: Video files (.mp4) in specified output directory
  - File correctly describes environment requirements (VRT_EMAIL, VRT_PASSWORD optional)
  - File shows correct usage examples (using thuis.sh/thuis.bat or python -m thuis.main)
  - No contradiction between spec and actual implementation

  QA Scenarios:

  \`\`\`
  Scenario: Verify Spec Kit specs updated correctly
    Tool: Bash
    Preconditions: Wrappers created and main.py functional (Task 8 complete)
    Steps:
      1. Execute: `cat .specify/specs/vrt-dlp-downloader.md`
      2. Execute: `specify validate .specify/specs/vrt-dlp-downloader.md 2>&1 || true` (if specify available)
      3. Execute: `grep -i \"download\" .specify/specs/vrt-dlp-downloader.md | head -1`
      4. Execute: `grep -i \"URL\" .specify/specs/vrt-dlp-downloader.md | head -1`
      5. Execute: `grep -i \"--file\" .specify/specs/vrt-dlp-downloader.md | head -1`
      6. Execute: `grep -i \"--output-dir\" .specify/specs/vrt-dlp-downloader.md | head -1`
      7. Execute: `grep -i \"VRT_EMAIL\\|VRT_PASSWORD\" .specify/specs/vrt-dlp-downloader.md | head -1`
      8. Assert that all expected sections are present and sensible
    Expected Result: Spec file accurately reflects current implementation
    Failure Indicators: Missing required sections, or contradictory information
    Evidence: .omo/evidence/task-10-verify-specs-updated.txt
  \`\`\`

  Commit: NO (part of Wave 3 preparation)

- [x] 11. Verify documentation accuracy

  What to do:
  - Test that the examples in README.md actually work
  - Test that the spec validate command passes (if specify available)
  - Verify that wrapper examples in README work

  Must NOT do:
  - Do not alter documentation after verification
  - Do not test actual downloads (too slow)
  - Do not test edge cases that would require network changes

  Recommended Agent Profile:
  > Selecting 'unspecified-high' category for documentation verification.
  - **Category**: `unspecified-high`
    - Reason: Testing documentation examples
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for doc verification

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 9-10)
  - Parallel Group: Wave 3 (Tasks 9-12)
  - Blocks: Task 12
  - Blocked By: Task 10

  References:

  > Executor needs to know how to test documentation examples.

  Pattern References:
  - README.md
  - .specify/specs/vrt-dlp-downloader.md
  - thuis.sh/thuis.bat
  - src/thuis/main.py

  Acceptance Criteria:
  - **If TDD**: N/A (this is verification)
  - Examples in README.md are syntactically correct
  - Wrapper examples in README would work if executed
  - Spec file validates without errors (if specify available)
  - No misleading instructions in documentation

  QA Scenarios:

  \`\`\`
  Scenario: Verify README examples are syntactically valid
    Tool: Bash
    Preconditions: README updated (Task 9 complete)
    Steps:
      1. Execute: `grep -o \"thuis\\.sh [^`]*\" README.md | head -3 | while read cmd; do echo \"Testing: $cmd\"; $cmd --help >/dev/null 2>&1 && echo \"  OK\" || echo \"  FAIL: $cmd\"; done`
      2. Execute: `grep -o \"thuis\\.bat [^`]*\" README.md | head -3 | while read cmd; do echo \"Testing: $cmd\"; cmd --help >/dev/null 2>&1 && echo \"  OK\" || echo \"  FAIL: $cmd\"; done`
      3. Assert that all tested commands either succeed or fail only due to missing Python (not syntax errors)
    Expected Result: All README examples are syntactically valid
    Failure Indicators: Any example fails due to syntax error (not missing Python)
    Evidence: .omo/evidence/task-11-verify-readme-examples.txt
  \`\`\`

  \`\`\`
  Scenario: Verify Spec Kit spec validates (if specify available)
    Tool: Bash
    Preconditions: Specs updated (Task 10 complete)
    Steps:
      1. Execute: `which specify 2>/dev/null || echo \"specify not available, skipping\"`
      2. Execute: `if command -v specify >/dev/null 2>&1; then specify validate .specify/specs/vrt-dlp-downloader.md; else echo \"Skipping specify validation\"; fi`
      3. Assert that if specify is available, it returns success
    Expected Result: Spec validates successfully (if tool available)
    Failure Indicators: Spec fails validation when tool is available
    Evidence: .omo/evidence/task-11-verify-specs-validation.txt
  \`\`\`

  Commit: NO (part of Wave 3 preparation)

- [x] 12. Run all tests to confirm nothing broken after documentation updates

  What to do:
  - Run the full test suite one final time before git operations
  - Verify all 9 tests still pass

  Must NOT do:
  - Do not alter any test logic
  - Do not change requirements.txt
  - Do not modify any source code

  Recommended Agent Profile:
  > Selecting 'unspecified-high' category for final test verification.
  - **Category**: `unspecified-high`
    - Reason: Running full test suite before git operations
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for test runs

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 11)
  - Parallel Group: Wave 3 (Tasks 9-12)
  - Blocks: Task 13
  - Blocked By: Task 11

  References:

  > Executor needs to know test command to run.

  Pattern References:
  - tests/test_poc.py
  - tests/test_real_download.py

  Acceptance Criteria:
  - **If TDD**: N/A (this is verification)
  - All 9 tests pass (5 unit + 4 integration)
  - No test failures or errors
  - Total execution time recorded for reference

  QA Scenarios:

  \`\`\`
  Scenario: Verify full test suite passes before git operations
    Tool: Bash
    Preconditions: Documentation updated (Task 11 complete)
    Steps:
      1. Execute: `python -m pytest tests/ -v`
      2. Capture output and exit code
      3. Assert that exit code is 0
      4. Assert that output shows \"9 passed\"
      5. Record total execution time for reference
    Expected Result: All 9 tests pass
    Failure Indicators: Non-zero exit code, or not exactly \"9 passed\" in output
    Evidence: .omo/evidence/task-12-verify-pre-git-tests.txt
  \`\`\`

  Commit: NO (part of Wave 3 preparation)

- [x] 13. Squash commits to v4/main branch

  What to do:
  - Create new orphan branch v4/main (completely clean history)
  - Copy all current files to this branch
  - Create single initial commit with \"chore: release v4.0.0 initial structure\"
  - Tag as v4.0.0
  - Alternative: squash current branch into one commit and rename to v4/main

  Must NOT do:
  - Do not lose any functional code
  - Do not remove .omo/ or .specify/ directories
  - Do not change functionality in any way
  - Do not remove the wrappers or package structure

  Recommended Agent Profile:
  > Selecting 'deep' category for git history surgery.
  - **Category**: `deep`
    - Reason: Complex history rewriting requiring careful execution
  - **Skills**: [git-master]
    - git-master: Essential for safe history rewriting
  - **Skills Evaluated but Omitted**:
    - `writing`: Not primary focus for this task

  Parallelization:
  - Can Run In Parallel: NO (depends on Tasks 12)
  - Parallel Group: Wave 4 (Tasks 13-15)
  - Blocks: Task 14
  - Blocked By: Task 12

  References:

  > Executor needs to know git commands for safe history rewriting.

  Pattern References:
  - Current git log (to understand what to preserve)
  - Target: clean single commit with all files

  Acceptance Criteria:
  - **If TDD**: N/A (this is git history)
  - Branch v4/main exists
  - Branch v4/main has exactly 1 commit (or very clean, minimal history)
  - Tag v4.0.0 points to v4/main tip
  - All files from current state are present in v4/main
  - legacy/ directory is absent in v4/main
  - src/thuis/, thuis.sh, thuis.bat, tests/, README.md, .specify/, .omo/ all present
  - No extraneous files or history

  QA Scenarios:

  \`\`\`
  Scenario: Verify v4/main branch created correctly
    Tool: Bash
    Preconditions: All tests passing (Task 12 complete)
    Steps:
      1. Execute: `git checkout -b v4/main`
      2. Execute: `git reset --hard` (to clean state)
      3. Execute: `cp -r * .[!.]* .git/ 2>/dev/null || true` (careful copy)
      4. Better: Use git worktree or create from scratch
      5. Actually: `git checkout --orphan v4/main`
      6. Execute: `git rm -rf .` (remove all from index)
      7. Execute: `cp -r /path/to/current/state/* .`
      8. Execute: `cp -r /path/to/current/state/.[!.]* . 2>/dev/null || true`
      9. Execute: `git add .`
      10. Execute: `git commit -m \"chore: release v4.0.0 initial structure\"`
      11. Execute: `git tag v4.0.0`
      12. Execute: `git log --oneline | wc -l`
      13. Assert that step 12 outputs \"1\" (single commit)
      14. Execute: `git show --name-only`
      15. Assert that all expected files are listed
      16. Assert that legacy/ is NOT listed
      17. Execute: `git tag --list 'v4.0.0'`
      18. Assert that v4.0.0 tag exists
    Expected Result: Clean v4/main branch with single commit and v4.0.0 tag
    Failure Indicators: Multiple commits, missing files, legacy/ present, or missing tag
    Evidence: .omo/evidence/task-13-verify-v4-main-created.txt
  \`\`\`

  Commit: NO (this IS the commit)

- [x] 14. Tag release as v4.0.0

  What to do:
  - This is already included in Task 13 - the tagging step
  - No additional action needed beyond what's described in Task 13

  Must NOT do:
  - Do not create tag without proper commit
  - Do not tag wrong commit
  - Do not forget to push tag

  Recommended Agent Profile:
  > Selecting 'quick' category as this is part of git tagging.
  - **Category**: `quick`
    - Reason: Simple git tag operation
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for this specific tag

  Parallelization:
  - Can Run In Parallel: NO (depends on Task 13)
  - Parallel Group: Wave 4 (Tasks 13-15)
  - Blocks: Task 15
  - Blocked By: Task 13

  References:

  > Executor knows this is covered in Task 13.

  Pattern References:
  - Same as Task 13

  Acceptance Criteria:
  - **If TDD**: N/A (covered in Task 13)
  - See Task 13 acceptance criteria

  QA Scenarios:
  - See Task 13 QA scenarios

  Commit: YES (this creates the commit)

- [x] 15. Final verification

  What to do:
  - Run all tests on the new v4/main branch
  - Verify wrappers work
  - Verify docs are present
  - Verify legacy/ is gone
  - Verify repo is clean ready for release

  Must NOT do:
  - Do not alter any functionality
  - Do not add new features
  - Do not break anything that was working

  Recommended Agent Profile:
  > Selecting 'unspecified-high' category for final release verification.
  - **Category**: `unspecified-high`
    - Reason: Comprehensive final check before release
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for verification (though helpful)

  Parallelization:
  - Can Run In Parallel: NO (depends on Task 14)
  - Parallel Group: Wave FINAL (Tasks F1-F4)
  - Blocks: Task F1
  - Blocked By: Task 14

  References:

  > Executor needs to know what to check for final verification.

  Pattern References:
  - All previous acceptance criteria
  - All test files
  - All created files

  Acceptance Criteria:
  - **If TDD**: N/A (this is final verification)
  - All 9 tests pass on v4/main branch
  - legacy/ directory does not exist
  - src/thuis/, thuis.sh, thuis.bat, tests/, README.md, .specify/, .omo/ all present
  - .gitignore still ignores legacy/
  - Wrappers work correctly (help/version)
  - Spec file is present and valid
  - v4.0.0 tag exists and points to correct commit
  - Hardcoded credentials preserved

  QA Scenarios:

  \`\`\`
  Scenario: Verify final release state is correct
    Tool: Bash
    Preconditions: v4/main branch created and tagged (Task 14 complete)
    Steps:
      1. Execute: `git checkout v4/main`
      2. Execute: `test ! -d legacy/ && echo \"legacy removed OK\" || echo \"legacy NOT removed\"`
      3. Execute: `test -d src/thuis && echo \"src/thuis exists OK\" || echo \"src/thuis missing\"`
      4. Execute: `test -f thuis.sh && test -x thuis.sh && echo \"thuis.sh OK\" || echo \"thuis.sh bad\"`
      5. Execute: `test -f thuis.bat && echo \"thuis.bat exists OK\" || echo \"thuis.bat missing\"`
      6. Execute: `test -f README.md && echo \"README.md exists OK\" || echo \"README.md missing\"`
      7. Execute: `test -f .specify/specs/vrt-dlp-downloader.md && echo \"specs OK\" || echo \"specs missing\"`
      8. Execute: `test -d .omo/ && echo \".omo/ exists OK\" || echo \".omo/ missing\"`
      9. Execute: `grep -q \"legacy/\" .gitignore && echo \"gitignore OK\" || echo \"gitignore missing legacy ignore\"`
      10. Execute: `python -m pytest tests/ -v | tail -1`
      11. Execute: `./thuis.sh --help | head -1 | grep -i usage`
      12. Execute: `./thuis.bat --help | head -1 | findstr /i \"usage\" >nul && echo \"OK\" || echo \"FAIL\"` (Windows)
      13. Assert that all steps show success
    Expected Result: All checks pass
    Failure Indicators: Any check fails
    Evidence: .omo/evidence/task-15-verify-final-release.txt
  \`\`\`

  Commit: YES (final verification state)

- [x] F1. Plan Compliance Audit — oracle

  **What to do**:
  Read the plan end-to-end. For each \"Must Have\": verify implementation exists (read file, run command). For each \"Must NOT Have\": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

  **Must NOT do**:
  - Do not modify any files.
  - Do not add any comments/docstrings.

  **References**:

  > Executor needs to know the plan file location and what to verify.

  **Pattern References**:
  - This plan document (.omo/plans/project-cleanup-release.md)
  - All files mentioned in Must Have/Must NOT Have

  **Acceptance Criteria**:
  - Must Have [N/N]: All mandatory deliverables present and correct
  - Must NOT Have [N/N]: No forbidden elements present
  - Tasks [N/N]: All implementation tasks completed as specified
  - VERDICT: APPROVE if all checks pass, REJECT if any fail

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify plan compliance after all tasks completed
    Tool: Bash
    Preconditions: All tasks completed through Task 15
    Steps:
      1. Execute: `cat .omo/plans/project-cleanup-release.md`
      2. Execute: `python -m pytest tests/ -v | tail -1`
      3. Execute: `test ! -d legacy/ && echo \"legacy removed\" || echo \"legacy present\"`
      4. Execute: `test -f src/thuis/main.py && echo \"main.py exists\" || echo \"main.py missing\"`
      5. Execute: `test -f thuis.sh && test -x thuis.sh && echo \"thuis.sh OK\" || echo \"thuis.sh bad\"`
      6. Execute: `test -f thuis.bat && echo \"thuis.bat exists OK\" || echo \"thuis.bat missing\"`
      7. Execute: `test -f README.md && echo \"README.md exists\" || echo \"README.md missing\"`
      8. Execute: `test -f .specify/specs/vrt-dlp-downloader.md && echo \"specs OK\" || echo \"specs missing\"`
      9. Execute: `test -d .omo/ && echo \".omo/ exists\" || echo \".omo/ missing\"`
      10. Execute: `grep -q \"legacy/\" .gitignore && echo \"gitignore OK\" || echo \"gitignore missing legacy ignore\"`
      11. Execute: `git tag --list 'v4.0.0' | wc -l`
      12. Execute: `assert that step 11 outputs \"1\"`
      13. Assert that all checks from steps 2-12 pass
    Expected Result: All checks pass
    Failure Indicators: Any check fails
    Evidence: .omo/evidence/final-verification-f1.txt
  \`\`\`

  Commit: NO (this is verification)

- [x] F2. Code Quality Review — unspecified-high

  **What to do**:
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, oversized modules (250+ pure LOC with mandatory modular refactoring).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

  **Must NOT do**:
  - Do not modify any files.
  - Do not add any comments/docstrings.

  **References**:

  > Executor needs to know what files to check and what linters to run.

  **Pattern References**:
  - All .py files in the project
  - Common Python linters (flake8, pylint, etc.)
  - Current codebase after all modifications

  **Acceptance Criteria**:
  - Build [PASS/FAIL]: Python import success and no syntax errors
  - Lint [PASS/FAIL]: No linting errors (using standard Python linters)
  - Tests [N pass/N fail]: All tests pass (should be 9/9)
  - Files [N clean/N issues]: Percentage of files without linting issues
  - VERDICT: Based on combined results

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify code quality after all tasks completed
    Tool: Bash
    Preconditions: All tasks completed through Task 15
    Steps:
      1. Execute: `python -m py_compile src/thuis/main.py 2>&1 || echo \"Compile failed\"`
      2. Execute: `python -m py_compile tests/test_poc.py 2>&1 || echo \"Test compile failed\"`
      3. Execute: `python -m py_compile tests/test_real_download.py 2>&1 || echo \"Test compile failed\"`
      4. Execute: `flake8 src/thuis/main.py 2>/dev/null | wc -l`
      5. Execute: `pylint src/thuis/main.py 2>/dev/null | grep -E \"^\\*\\*\\* Module|Your code has been rated at\" | head -1 || echo \"No rating\"`
      6. Execute: `python -m pytest tests/ -v | tail -1`
      7. Assert that compilation succeeds (no output from py_compile means success)
      8. Assert that flake8/pylint output is reasonable (not excessive errors)
      9. Assert that test output shows \"9 passed\"
    Expected Result: All files compile, linter output acceptable, all tests pass
    Failure Indicators: Compilation failures, excessive linter errors, or test failures
    Evidence: .omo/evidence/final-verification-f2.txt
  \`\`\`

  Commit: NO (this is verification)

- [x] F3. Real Manual QA — unspecified-high (+ playwright skill if UI)

  **What to do**:
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

  **Must NOT do**:
  - Do not modify any files.
  - Do not add any comments/docstrings.

  **References**:

  > Executor needs to know what QA scenarios to run from all tasks.

  **Pattern References**:
  - All QA scenarios from all TODOs above
  - Combined end-to-end verification

  **Acceptance Criteria**:
  - Scenarios [N/N pass]: Percentage of scenarios that pass
  - Integration [N/N]: Integration test scenarios pass rate
  - Edge Cases [N tested]: Number of edge cases tested
  - VERDICT: Based on combined results

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify final release state with comprehensive QA
    Tool: Bash
    Preconditions: All tasks completed through Task 15
    Steps:
      1. Execute: `python -m pytest tests/ -v | tail -1`
      2. Execute: `test ! -d legacy/ && echo \"legacy removed OK\" || echo \"legacy NOT removed\"`
      3. Execute: `test -f src/thuis/main.py && test -f src/thuis/__init__.py && echo \"package OK\" || echo \"package incomplete\"`
      4. Execute: `test -f thuis.sh && test -x thuis.sh && echo \"thuis.sh executable OK\" || echo \"thuis.sh not executable\"`
      5. Execute: `test -f thuis.bat && echo \"thuis.bat exists OK\" || echo \"thuis.bat missing\"`
      6. Execute: `./thuis.sh --help | head -1 | grep -i usage >/dev/null && echo \"thuis.sh help OK\" || echo \"thuis.sh help FAIL\"`
      7. Execute: `./thuis.bat --help | head -1 | findstr /i \"usage\" >nul && echo \"thuis.bat help OK\" || echo \"thuis.bat help FAIL\"`
      8. Execute: `test -f README.md && echo \"README.md exists OK\" || echo \"README.md missing\"`
      9. Execute: `test -f .specify/specs/vrt-dlp-downloader.md && echo \"specs OK\" || echo \"specs missing\"`
      10. Execute: `test -d .omo/ && echo \".omo/ exists OK\" || echo \".omo/ missing\"`
      11. Execute: `grep -q \"legacy/\" .gitignore && echo \"gitignore OK\" || echo \"gitignore missing legacy ignore\"`
      12. Execute: `git tag --list 'v4.0.0' | wc -l | xargs test \"{\$}\" -eq 1 && echo \"tag OK\" || echo \"tag missing or duplicate\"`
      13. Execute: `python -c \"import sys; sys.path.insert(0, '.'); from thuis.main import get_credentials; creds = get_credentials(); assert isinstance(creds, tuple) and len(creds) == 2 and creds[0] == 'kuxelu@ipdeer.com' and creds[1] == 'Els123456'\" && echo \"credentials OK\" || echo \"credentials changed\"`
      14. Assert that all checks from steps 2-13 pass
    Expected Result: All checks pass
    Failure Indicators: Any check fails
    Evidence: .omo/evidence/final-verification-f3.txt
  \`\`\`

  Commit: NO (this is verification)

- [x] F4. Scope Fidelity Check — deep

  **What to do**:
  For each task in the plan, read \"What to do\", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check \"Must NOT do\" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

  **Must NOT do**:
  - Do not modify any files.
  - Do not add any comments/docstrings.

  **References**:

  > Executor needs to know what was planned vs what was implemented.

  **Pattern References**:
  - This plan document (.omo/plans/project-cleanup-release.md)
  - Git diff between original state and final state
  - All files mentioned in the plan

  **Acceptance Criteria**:
  - Tasks [N/N compliant]: Percentage of tasks implemented exactly as specified
  - Contamination [CLEAN/N issues]: Whether any task touched files outside its scope
  - Unaccounted [CLEAN/N files]: Whether any files were changed that weren't specified in any task
  - VERDICT: Based on combined results

  **QA Scenarios**:

  \`\`\`
  Scenario: Verify scope fidelity after all tasks completed
    Tool: Bash
    Preconditions: All tasks completed through Task 15
    Steps:
      1. Execute: `git log --oneline v4/main | wc -l`
      2. Execute: `assert that output is \"1\" (single squashed commit)`
      3. Execute: `git diff --name-only HEAD`
      4. Execute: `assert that output shows only expected files changed/added/removed`
      5. Execute: `test ! -d legacy/ && echo \"legacy removed OK\" || echo \"legacy NOT removed\"`
      6. Execute: `test -d src/thuis/ && echo \"src/thuis created OK\" || echo \"src/thuis not created\"`
      7. Execute: `test -f src/thuis/__init__.py && echo \"__init__.py exists OK\" || echo \"__init__.py missing\"`
      8. Execute: `test -f src/thuis/main.py && echo \"main.py exists OK\" || echo \"main.py missing\"`
      9. Execute: `test -f thuis.sh && test -x thuis.sh && echo \"thuis.sh OK\" || echo \"thuis.sh not executable\"`
      10. Execute: `test -f thuis.bat && echo \"thuis.bat exists OK\" || echo \"thuis.bat missing\"`
      11. Execute: `test -d tests/ && echo \"tests/ directory OK\" || echo \"tests/ directory missing\"`
      12. Execute: `test -f tests/test_poc.py && echo \"tests/test_poc.py exists OK\" || echo \"tests/test_poc.py missing\"`
      13. Execute: `test -f tests/test_real_download.py && echo \"tests/test_real_download.py exists OK\" || echo \"tests/test_real_download.py missing\"`
      14. Execute: `test -f README.md && echo \"README.md exists OK\" || echo \"README.md missing\"`
      15. Execute: `test -f .specify/specs/vrt-dlp-downloader.md && echo \"specs OK\" || echo \"specs missing\"`
      16. Execute: `test -d .omo/ && echo \".omo/ exists OK\" || echo \".omo/ missing\"`
      17. Execute: `grep -q \"legacy/\" .gitignore && echo \"gitignore OK\" || echo \"gitignore missing legacy ignore\"`
      18. Execute: `python -m pytest tests/ -v | tail -1 | grep -q \"9 passed\" && echo \"tests OK\" || echo \"tests not 9 passed\"`
      19. Execute: `assert that all checks from steps 2-18 pass`
    Expected Result: All checks pass
    Failure Indicators: Any check fails
    Evidence: .omo/evidence/final-verification-f4.txt
  \`\`\`

  Commit: NO (this is verification)

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit \"okay\" before completing.
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
   For each task in the plan, read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
   Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

## Commit Strategy

- **1**: `chore: create package structure` - `src/thuis/__init__.py`, `src/thuis/main.py`
- **2**: `chore: move and update test files` - `tests/test_poc.py`, `tests/test_real_download.py`
- **3**: `chore: verify basic functionality` - (no file change, test execution)
- **4**: `chore: verify all tests pass` - (no file change, test execution)
- **5**: `chore: remove legacy directory` - `legacy/` (directory deletion)
- **6**: `chore: create wrapper scripts` - `thuis.sh`, `thuis.bat`
- **7**: `chore: add python check to wrappers` - (part of Tasks 6)
- **8**: `chore: verify wrappers work` - (no file change, test execution)
- **9**: `chore: update README.md` - `README.md`
- **10**: `chore: update Spec Kit specs` - `.specify/specs/vrt-dlp-downloader.md`
- **11**: `chore: verify documentation accuracy` - (no file change, test execution)
- **12**: `chore: verify all tests pass after docs` - (no file change, test execution)
- **13**: `chore: squash commits to v4/main` - (git history rewrite)
- **14**: `chore: tag release as v4.0.0` - (git tag creation)
- **15**: `chore: final verification` - (no file change, final test execution)
- **F1**: `oracle: plan compliance audit` - (no file change, plan verification)
- **F2**: `unspecified-high: code quality review` - (no file change, code review)
- **F3**: `unspecified-high: real manual QA` - (no file change, QA execution)
- **F4**: `deep: scope fidelity check` - (no file change, fidelity check)

## Success Criteria

### Verification Commands
```bash
python -m pytest tests/ -v          # Expected: 9 passed
./thuis.sh --help                   # Expected: usage information
./thuis.bat --help                  # Expected: usage information (Windows)
test ! -d legacy/                   # Expected: no output (directory removed)
test -f src/thuis/main.py           # Expected: no output (file exists)
test -f thuis.sh && test -x thuis.sh # Expected: no output (file exists and executable)
test -f thuis.bat                   # Expected: no output (file exists)
test -f README.md                   # Expected: no output (file exists)
test -f .specify/specs/vrt-dlp-downloader.md # Expected: no output (file exists)
git tag --list 'v4.0.0' | wc -l     # Expected: 1 (tag exists)
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] All tests pass
- [x] `requirements.txt` updated correctly (still points to Aldo-f/yt-dlp@v2026.06.09-patch1)
- [x] TODO item for future cleanup added
- [x] Changes committed and pushed
- [x] legacy/ directory removed
- [x] src/thuis/ directory with __init__.py and main.py present
- [x] thuis.sh and thuis.bat wrappers present and functional
- [x] README.md updated with clear usage instructions
- [x] .specify/specs/vrt-dlp-downloader.md updated to match implementation
- [x] All 9 tests pass (5 unit + 4 integration)
- [x] Clean git history on v4/main branch
- [x] v4.0.0 tag created and pointing to correct commit
- [x] Hardcoded default credentials preserved (kuxelu@ipdeer.com / Els123456)