#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo "Then run this script again."
    exit 1
fi
exec python3 "$SCRIPT_DIR/src/thuis/main.py" "$@"
