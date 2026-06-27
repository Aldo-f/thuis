#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer venv Python (has patched yt-dlp for VRT MAX)
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo "Then run this script again."
    exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/src/thuis/main.py" "$@"
