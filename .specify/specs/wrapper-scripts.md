# Wrapper Scripts Specification

## thuis.sh (Linux/macOS)
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtualenv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run main module
python -m thuis.main "$@"
```

## thuis.bat (Windows)
```bat
@echo off
setlocal
cd /d "%~dp0"

rem Activate virtualenv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m thuis.main %*
```

## Requirements
- Both scripts must be in project root
- Must `cd` to project root so relative paths work
- Must activate `.venv` if present (so `python` uses correct env)
- Must pass all arguments through to `python -m thuis.main`
- `thuis.sh` must be executable (`chmod +x thuis.sh`)

## Tests
- Manual: `./thuis.sh --help`, `./thuis.sh --dry-run "https://..."`
- Manual: `thuis.bat --help`