# Watchlist Runner Script Specification

## File
`scripts/watchlist-runner.sh`

## Purpose
Wrapper that ensures cron entry exists, then runs `thuis.sh` with all configured watchlist files.

## Logic
1. Define cron tag: `# HOME: thuis-watchlist`
2. Define cron line:
   ```
   0 * * * * /usr/local/bin/run-serial.sh thuis-watchlist --max-wait=7200 -- REPO_DIR/scripts/watchlist-runner.sh >> REPO_DIR/logs/watchlist.log 2>&1
   ```
3. `ensure_cron_entry()`:
   - If no existing cron entry with tag → add it
   - If exists but path changed → update it
4. Change to repo directory
5. Run `./thuis.sh` with all watchlist files:
   ```
   ./thuis.sh \
     --watchlist watchlists/Fc_De_Kampioenen.txt \
     --watchlist watchlists/Flikken.txt \
     --watchlist watchlists/Flikken_Maastricht.txt \
     --watchlist watchlists/Thuis.txt \
     --watchlist watchlists/podcast.txt \
     "$@"
   ```

## Variables
- `REPO_DIR` — absolute path to repo (computed from script location)
- `CRON_TAG` — unique identifier for cron management
- `CRON_LINE` — full cron line with run-serial.sh

## Cron Management
- Uses `run-serial.sh` for serialized execution (shared lock file `/run/lock/pi-heavy-jobs.lock`)
- `--max-wait=7200` — max wait for lock (2 hours)
- Output logged to `logs/watchlist.log`

## Tests
- Manual: run `./scripts/watchlist-runner.sh --dry-run`
- Verify cron entry with `crontab -l | grep thuis-watchlist`