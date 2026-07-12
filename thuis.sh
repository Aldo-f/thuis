#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

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

# Intercept --follow / -f to tail the current log file
for arg in "$@"; do
    case "$arg" in
        --follow|-f)
            LOG_FILE=$(find "$SCRIPT_DIR/logs" -name "*.log" -type f -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
            if [ -n "$LOG_FILE" ]; then
                exec tail -F "$LOG_FILE"
            else
                echo "No log file found. Run the script first to create logs."
                exit 1
            fi
            ;;
    esac
done

exec "$PYTHON" -m thuis.main "$@"
