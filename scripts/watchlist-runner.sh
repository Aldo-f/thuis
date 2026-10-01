#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCK_FILE="/run/lock/thuis-watchlist.lock"
CRON_TAG="# HOME: thuis-watchlist"
CRON_LINE="0 * * * * /usr/local/bin/run-serial.sh thuis-watchlist --max-wait=7200 -- $REPO_DIR/scripts/watchlist-runner.sh >> $REPO_DIR/logs/watchlist.log 2>&1"

# Prevent concurrent invocations: acquire flock with 0s wait (non-blocking).
# If the lock is already held, skip this run entirely.
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[watchlist] SKIP: another instance is already running (lock held)" >&2
    exit 0
fi

ensure_cron_entry() {
    if ! crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
        (crontab -l 2>/dev/null || true; echo "") | grep -v "$CRON_TAG" | grep -v "thuis-watchlist" | crontab -
        { crontab -l; echo "$CRON_TAG"; echo "$CRON_LINE"; } | crontab -
        echo "[watchlist] cron entry added: $CRON_LINE" >&2
    else
        # Update existing entry in case path changed
        local current
        current="$(crontab -l 2>/dev/null | grep -v "$CRON_TAG" | grep -v "thuis-watchlist" || true)"
        { echo "$current"; echo "$CRON_TAG"; echo "$CRON_LINE"; } | grep -v '^$' | crontab -
    fi
}

ensure_cron_entry
cd "$REPO_DIR"
./thuis.sh \
  --auto-upload \
  --watchlist watchlists/Fc_De_Kampioenen.txt \
  --watchlist watchlists/Flikken.txt \
  --watchlist watchlists/Flikken_Maastricht.txt \
  --watchlist watchlists/Thuis.txt \
  --watchlist watchlists/podcast.txt \
  "$@"
