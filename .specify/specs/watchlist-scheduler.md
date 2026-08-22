# Watchlist Scheduler Feature Specification

**Feature Branch**: `feature/watchlist-scheduler`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Add a watchlist-driven download scheduler with inline schedule tags, SQLite state tracking, cron auto-creation, and scene filename-based new episode detection"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Schedule-based downloads (Priority: P1)

As a user who wants to automatically download new episodes of TV shows and movies from VRT MAX without manually running the tool each time.

**Why this priority**: Core automation feature that reduces manual effort

**Independent Test**: Create a watchlist file with `[daily]` tag, run `thuis.sh --watchlist` with `--now`, verify the file downloads to the correct output directory. Then run without `--now` and verify state DB is checked.

**Acceptance Scenarios**:
1. **Given** a watchlist file with `[daily]` tag, **When** `--watchlist --now` is called, **Then** all URLs are downloaded immediately to the specified output dir
2. **Given** a watchlist file with `[monday]`, **When** it's Wednesday and `--watchlist` runs, **Then** entries are NOT triggered (already past this week's Monday)
3. **Given** a watchlist file with `[monday]`, **When** it's Monday at 00:00 and `--watchlist` runs, **Then** entries ARE triggered once
4. **Given** a watchlist file with `[daily 08:30]`, **When** it's 09:00 on the same day, **Then** the daily entry is NOT triggered (time already passed)
5. **Given** a watchlist file with `[daily 08:30]`, **When** it's 07:00 the next day, **Then** the entry IS triggered at the next hourly cron run

---

### User Story 2 - Multiple watchlist files (Priority: P2)

As a user who wants to organize downloads into separate categories (TV, movies, podcasts) with different output directories and schedules.

**Why this priority**: Organization and flexibility

**Independent Test**: Create `watchlists/tv.txt` and `watchlists/movies.txt`, each with different output dirs, run `thuis.sh --watchlist watchlists/tv.txt watchlists/movies.txt --now`, verify files go to correct directories.

**Acceptance Scenarios**:
1. **Given** multiple watchlist files with different first-line output dirs, **When** `--watchlist file1 file2 --now` is called, **Then** each URL downloads to its respective file's output dir
2. **Given** a watchlist file without a first-line output dir, **When** it's processed, **Then** it falls back to `.env` OUTPUT_DIR or default `media`

---

### User Story 3 - State tracking & new episode detection (Priority: P1)

As a user who wants the system to automatically skip files that already exist and only download new episodes.

**Why this priority**: Core deduplication logic

**Independent Test**: Download an episode with `--watchlist --now`, then run again with `--now` and verify the same episode is skipped.

**Acceptance Scenarios**:
1. **Given** an episode already exists in output dir, **When** the URL is processed again, **Then** it is skipped (file matching by scene filename)
2. **Given** a partial download exists (.part file), **When** processing, **Then** the download is completed if final file doesn't exist, or partial is deleted if final exists
3. **Given** the state DB exists, **When** `--watchlist` runs without `--now`, **Then** it compares last-run timestamp against schedule

---

### User Story 4 - Cron auto-management (Priority: P2)

As a user who wants hands-off scheduling without manually configuring cron.

**Why this priority**: Zero-setup automation

**Independent Test**: Run `thuis.sh --watchlist thuis.txt` (without `--now`), check `crontab -l` shows an hourly cron entry pointing to `thuis.sh --watchlist`.

**Acceptance Scenarios**:
1. **Given** no existing cron entry for thuis, **When** `--watchlist` is run (without `--now`), **Then** an hourly cron job is auto-created
2. **Given** an existing cron entry pointing to old `thuis.sh` path, **When** `--watchlist` runs, **Then** the cron is updated to the current `thuis.sh` path

---

### Edge Cases

- What happens when a URL is invalid or VRT returns an error? → Log error, mark entry status as `error` in DB, continue with next URL
- What happens when the output directory doesn't exist? → Create it (parents=True)
- What happens when `.env` file has `OUTPUT_DIR` set? → Used as fallback when watchlist file has no first-line output dir
- What happens when `thuis.sh` is moved? → Cron auto-update detects path change
- Podcast URLs that aren't supported yet → Attempt download, log error if unsupported

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept `--watchlist FILE1 [FILE2 ...]` flag accepting one or more watchlist file paths
- **FR-002**: System MUST accept `--now` flag that bypasses schedule checks and runs all entries immediately
- **FR-003**: System MUST parse the first non-comment line of each watchlist file as the output directory
- **FR-004**: System MUST resolve output dir paths starting with `~` using `os.path.expanduser()`
- **FR-005**: System MUST resolve output dir paths starting with `/` as absolute
- **FR-006**: System MUST resolve output dir paths without `~` or `/` as relative to current working directory
- **FR-007**: System MUST support schedule tags in format `[schedule]` at start of URL lines
- **FR-008**: System MUST support schedule formats: `daily`, `weekly`, `week`, `1 week`, `2 weeks`, `weekdays`, `weekends`, `monday`-`sunday`, `daily HH:MM`, `weekday HH:MM`
- **FR-009**: System MUST support comma-separated sub-schedules: `[monday 8:00, wednesday 7:00, weekend 8:00]`
- **FR-010**: System MUST use SQLite database at `~/.thuis/state.db` to track: watchlist file paths, last-scan times, next-check times, entry URLs, entry schedules, last-run timestamps, last-status
- **FR-011**: System MUST check the SQLite state DB to determine if an entry should trigger (comparing schedule + last-run against current time)
- **FR-012**: System MUST auto-create an hourly cron entry for `thuis.sh --watchlist` if one doesn't exist
- **FR-013**: System MUST detect and update cron entries if `thuis.sh` path has changed
- **FR-014**: System MUST reject `--output-dir` when used with `--watchlist` (output dir comes from file)
- **FR-015**: System MUST use scene filename matching to skip already-downloaded files
- **FR-016**: System MUST complete partial downloads if final file doesn't exist; delete partials if final exists
- **FR-017**: System MUST log all watchlist runs to `logs/YYYY-MM-DD.log`
- **FR-018**: System MUST fall back to `.env` OUTPUT_DIR or `media` when watchlist file has no output dir line
- **FR-019**: System MUST handle podcast/VRT MAX URLs gracefully (attempt download, log error if unsupported)

### Key Entities

- **WatchlistFile**: Path, first-line output_dir, list of WatchlistEntry
- **WatchlistEntry**: URL, schedule, output_dir, last_run timestamp, last_status
- **Schedule**: Type (daily/weekly/weekdays/weekends/day-name), optional time, optional week interval
- **StateDB**: SQLite tables for watchlists, entries, downloaded_files

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `--watchlist file.txt --now` downloads all URLs in the file to the correct output directory
- **SC-002**: `--watchlist` (without `--now`) only triggers entries whose schedule permits running at the current time
- **SC-003**: Running `--watchlist file.txt --now` twice skips already-downloaded files (scene filename match)
- **SC-004**: Cron entry is auto-created when `--watchlist` is used without `--now`
- **SC-005**: `--output-dir` with `--watchlist` produces an error message
- **SC-006**: Schedule `daily 08:30` does not trigger at 12:30 the same day, but does trigger at 07:00 the next day
- **SC-007**: Schedule `monday` triggers once on Monday, not on Tuesday
- **SC-008**: `[daily]` without time triggers at every hourly cron run if not already run that day

## Assumptions

- User has `python-dotenv` installed (for `.env` loading)
- SQLite3 module is available (Python stdlib)
- Cron is available and accessible via `crontab` command
- Output directories are writable
- VRT MAX URLs require valid credentials (from env vars / .env)
- Scene filename format is used for matching existing files (e.g., `Thuis.S31E6108.1080p.WEB-DL.AAC.x264.mp4`)

## Technical Constraints

- Python 3.13+ (current environment)
- Must integrate with existing `thuis.sh` / `thuis.bat` wrappers
- Must use existing credential handling (env vars → .env → defaults)
- Must use existing scene naming pipeline (`scene_namer.py`, `metadata_fetcher.py`, etc.)
- Must handle `--profile/-p` resolution flag from watchlist context if needed

## Implementation Phases

### Phase 1: Core Watchlist Parser
- Parse watchlist file format (output dir + URL lines with tags)
- Resolve output directory paths (`~`, `/`, relative)
- Parse schedule tags (basic: daily, weekly, weekday names, time)
- Integrate with `--watchlist` and `--now` CLI args

### Phase 2: State Tracking
- Create SQLite database at `~/.thuis/state.db`
- Track watchlist files, entries, last-run timestamps
- Implement schedule checking logic (compare next-run against current time)

### Phase 3: Cron Auto-Management
- Detect existing cron entries
- Auto-create hourly cron for `thuis.sh --watchlist`
- Update cron if `thuis.sh` path changed

### Phase 4: Testing & Edge Cases
- Unit tests for parser, schedule checker, state DB
- Integration tests for full `--watchlist --now` flow
- Test all schedule format variations
- Test error handling
