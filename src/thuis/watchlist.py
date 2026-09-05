#!/usr/bin/env python3
"""
Watchlist parser, scheduler, and state database for automated downloads.

File format:
  Line 1: output directory (~/path, /absolute/path, or relative/path)
  Lines 2+: [schedule] URL  # optional comment

Schedule formats:
  daily
  daily 08:30
  weekly
  week
  1 week
  2 weeks
  monday
  monday 08:00
  tuesday,wednesday,friday
  weekdays
  weekends
  monday 8:00, wednesday 7:00, weekend 8:00
"""

import os
import re
import sqlite3
import glob
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


# ┌─── Data Classes ───────────────────────────────────────────────────────┐

@dataclass
class WatchlistEntry:
    """Single entry in a watchlist file."""
    url: str
    schedule: Optional[str] = None  # e.g. "daily 08:30", "monday,wednesday", None


@dataclass
class WatchlistFile:
    """Parsed watchlist file with output dir and entries."""
    path: str
    output_dir: str
    entries: list[WatchlistEntry] = field(default_factory=list)


# ┌─── Watchlist File Parser ───────────────────────────────────────────────┐

def parse_watchlist_file(path: str) -> WatchlistFile:
    """
    Parse a watchlist file.

    First non-comment, non-blank line = output directory.
    Subsequent lines: optional [schedule] tag + URL, comments and blanks skipped.
    """
    output_dir = ""
    entries: list[WatchlistEntry] = []
    output_dir_found = False

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()

            # Skip blank lines
            if not stripped:
                continue

            # Skip pure comments (first non-whitespace char is #)
            if stripped.startswith("#"):
                continue

            # First non-comment, non-blank line is the output directory
            if not output_dir_found:
                output_dir = stripped
                output_dir_found = True
                continue

            # Parse entry lines
            entry = _parse_entry_line(stripped)
            if entry:
                entries.append(entry)

    return WatchlistFile(path=path, output_dir=output_dir, entries=entries)


def _parse_entry_line(line: str) -> Optional[WatchlistEntry]:
    """Parse a single entry line: [schedule] URL # comment"""
    # Remove inline comments
    if "#" in line:
        line = line.split("#", 1)[0].strip()

    if not line:
        return None

    # Check for schedule tag at start: [schedule] url
    schedule_tag_match = re.match(r"^\[(.+?)\]\s*(.+)$", line)
    if schedule_tag_match:
        schedule = schedule_tag_match.group(1).strip()
        url = schedule_tag_match.group(2).strip()
        return WatchlistEntry(url=url, schedule=schedule)

    # No schedule tag — just a URL
    url = line.strip()
    return WatchlistEntry(url=url, schedule=None)


# ┌─── Output Directory Resolution ───────────────────────────────────────────┐

def resolve_output_dir(output_dir: str) -> str:
    """
    Resolve an output directory path.

    - ~/path → expands to home directory
    - /absolute/path → used as-is
    - relative/path → relative to cwd
    - empty → falls back to OUTPUT_DIR env var or 'media'
    """
    if not output_dir or output_dir.strip() == "":
        # Try .env / environment variable
        env_dir = os.getenv("OUTPUT_DIR", "")
        if env_dir:
            return resolve_output_dir(env_dir)
        return "media"

    if output_dir.startswith("~/"):
        return str(Path(output_dir).expanduser())

    if output_dir.startswith("/"):
        return output_dir

    # Relative path — join with cwd
    return str(Path.cwd() / output_dir)


# ┌─── Schedule Parser & Checker ─────────────────────────────────────────────┐

def should_trigger(schedule: Optional[str],
                    now: datetime,
                    last_run: Optional[datetime]) -> bool:
    """
    Check if a schedule entry should trigger at the given time.

    Args:
        schedule: Schedule string (e.g. "daily 08:30", "monday", "weekly") or None
        now: Current time
        last_run: Last run time for this entry (None = never ran)

    Returns:
        True if the entry should trigger now.
    """
    # No schedule = always triggers (manual only, runs with --now)
    if schedule is None:
        return True  # Only triggered explicitly via --now

    # If there are multiple comma-separated sub-schedules, return True if ANY matches
    sub_schedules = [s.strip().rstrip(",") for s in schedule.split(",")]
    for sub in sub_schedules:
        if _should_trigger_single(sub, now, last_run):
            return True
    return False


def _should_trigger_single(schedule: str,
                           now: datetime,
                           last_run: Optional[datetime]) -> bool:
    """
    Check a single (non-comma-separated) schedule string.
    """
    # Separate the day/time components
    parts = schedule.strip().split()
    time_str = None
    day_part = None
    week_interval = 1  # Default for weekly

    for p in parts:
        if p == "daily":
            day_part = "daily"
        elif p == "weekly":
            day_part = "week"
            week_interval = 1
        elif p in ("monday", "tuesday", "wednesday", "thursday",
                   "friday", "saturday", "sunday"):
            day_part = p
        elif p in ("weekdays", "weekday"):
            day_part = "weekdays"
        elif p in ("weekends", "weekend"):
            day_part = "weekends"
        elif _is_week_interval_token(parts, p):
            # This handles "1 week" and "2 weeks" as two-word schedules
            idx = parts.index(p)
            week_interval = int(p)
            day_part = "week"
        elif _is_time(p):
            time_str = p

    # Handle week interval patterns like "1 week" or "2 weeks"
    for i in range(len(parts)):
        if _is_week_interval_token(parts, parts[i]):
            week_interval = int(parts[i])
            day_part = "week"
            break

    # Default: daily with no time
    if day_part is None:
        day_part = "daily"
        time_str = parts[0] if parts and _is_time(parts[0]) else None

    # Determine the day(s) this schedule covers
    target_days = _get_target_days(day_part, now.weekday())

    if now.weekday() not in target_days:
        return False  # Today is not in the target days

    # Check if already ran
    if last_run is not None:
        if day_part == "week":
            # Weekly/N-weekly: strictly > interval days (not >=)
            interval_days = week_interval * 7
            if (now - last_run).days <= interval_days:
                return False
        else:
            # Daily / weekday / day-specific: check if ran today
            if _same_day(last_run, now):
                return False  # Already ran today

    # For first run (last_run is None) OR new period: check time
    if time_str:
        target_hour, target_minute = _parse_time(time_str)
        current_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if now < current_time:
            return False  # Before the scheduled time

    return True


def _is_week_interval_token(parts: list[str], token: str) -> bool:
    """Check if a token is part of a week interval like '1 week' or '2 weeks'."""
    try:
        num = int(token)
        idx = parts.index(token)
        if idx + 1 < len(parts):
            next_word = parts[idx + 1].lower()
            if next_word in ("week", "weeks"):
                return True
    except (ValueError, IndexError):
        pass
    return False


def _is_time(token: str) -> bool:
    """Check if token is a time like HH:MM or H:MM (optional trailing comma)."""
    token = token.rstrip(",")
    pattern = r"^(\d{1,2}):(\d{2})$"
    match = re.match(pattern, token)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    return False


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' into (hour, minute)."""
    time_str = time_str.rstrip(",")
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def _get_target_days(day_part: str, current_weekday: int) -> set[int]:
    """
    Get set of weekdays (0=Monday) that this schedule covers on the current date.
    For 'week', we interpret it as every day (run interval-based).
    """
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    if day_part == "daily" or day_part == "week":
        return set(range(7))  # Every day

    if day_part == "weekdays":
        return set(range(5))  # Mon-Fri

    if day_part in ("weekends", "weekend"):
        return {5, 6}  # Sat, Sun

    if day_part in day_map:
        return {day_map[day_part]}

    return set(range(7))  # Fallback


def _same_day(dt1: datetime, dt2: datetime) -> bool:
    """Check if two datetimes are on the same day."""
    return dt1.date() == dt2.date()


# ┌─── State Database (SQLite) ───────────────────────────────────────────────┐

class WatchlistDB:
    """SQLite state database for watchlist tracking."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            home = Path.home()
            state_dir = home / ".thuis"
            state_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(state_dir / "state.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS entries (
                url TEXT PRIMARY KEY,
                schedule TEXT,
                last_run TIMESTAMP,
                last_status TEXT,
                output_dir TEXT
            );
            CREATE TABLE IF NOT EXISTS watchlist_scans (
                path TEXT PRIMARY KEY,
                last_scan TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS downloaded_files (
                url TEXT,
                filename TEXT,
                output_dir TEXT,
                downloaded_at TIMESTAMP,
                PRIMARY KEY (url, filename, output_dir)
            );
            CREATE TABLE IF NOT EXISTS episode_progress (
                show_slug TEXT NOT NULL,
                season INTEGER NOT NULL,
                last_episode INTEGER DEFAULT 0,
                PRIMARY KEY (show_slug, season)
            );
            CREATE TABLE IF NOT EXISTS episode_cache (
                cache_key TEXT PRIMARY KEY,
                episodes_json TEXT NOT NULL,
                cached_at TIMESTAMP NOT NULL
            );
        """)
        self.conn.commit()

    def set_last_run(self, url: str, status: str = "ok", timestamp: Optional[datetime] = None):
        """Record/update the last run time for a URL."""
        now = timestamp if timestamp is not None else datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entries (url, last_run, last_status)
            VALUES (?, ?, ?)
        """, (url, now.isoformat(), status))
        self.conn.commit()
        return now

    def get_last_run(self, url: str) -> Optional[datetime]:
        """Get the last run timestamp for a URL."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_run FROM entries WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None

    def get_last_status(self, url: str) -> Optional[str]:
        """Get the last status for a URL."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_status FROM entries WHERE url = ?", (url,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_schedule(self, url: str, schedule: Optional[str], output_dir: str):
        """Set schedule and output dir for a URL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entries (url, schedule, output_dir)
            VALUES (?, ?, ?)
        """, (url, schedule, output_dir))
        self.conn.commit()

    def set_last_scan(self, path: str, timestamp: Optional[datetime] = None):
        """Record the last scan time for a watchlist file."""
        if timestamp is None:
            timestamp = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO watchlist_scans (path, last_scan)
            VALUES (?, ?)
        """, (path, timestamp.isoformat()))
        self.conn.commit()

    def get_last_scan(self, path: str) -> Optional[datetime]:
        """Get the last scan time for a watchlist file."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_scan FROM watchlist_scans WHERE path = ?", (path,))
        row = cursor.fetchone()
        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None

    def record_download(self, url: str, filename: str, output_dir: str):
        """Record that a download completed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO downloaded_files (url, filename, output_dir, downloaded_at)
            VALUES (?, ?, ?, ?)
        """, (url, filename, output_dir, str(datetime.now().isoformat())))
        self.conn.commit()

    def file_was_downloaded(self, url: str, filename: str, output_dir: str) -> bool:
        """Check if a file was recorded as downloaded in this directory."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM downloaded_files
            WHERE url = ? AND filename = ? AND output_dir = ?
        """, (url, filename, output_dir))
        return cursor.fetchone() is not None

    def any_file_for_url(self, url: str, output_dir: str) -> bool:
        """Check if any file is recorded for the given URL and output_dir."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM downloaded_files
            WHERE url = ? AND output_dir = ?
            LIMIT 1
        """, (url, output_dir))
        return cursor.fetchone() is not None

    def get_last_episode(self, show_slug: str, season: int) -> int:
        """Get the last seen episode number for a show+season."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT last_episode FROM episode_progress WHERE show_slug = ? AND season = ?",
            (show_slug, season)
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    def set_last_episode(self, show_slug: str, season: int, episode: int) -> None:
        """Update the last seen episode number for a show+season."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO episode_progress (show_slug, season, last_episode)
            VALUES (?, ?, ?)
            ON CONFLICT(show_slug, season) DO UPDATE SET last_episode = excluded.last_episode
        """, (show_slug, season, episode))
        self.conn.commit()

    def get_cached_episodes(self, cache_key: str, max_age_hours: int = 24) -> Optional[list]:
        """Get cached episodes if still fresh (default: 24h)."""
        import json
        from datetime import timedelta
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT episodes_json, cached_at FROM episode_cache
            WHERE cache_key = ?
        """, (cache_key,))
        row = cursor.fetchone()
        if not row:
            return None
        cached_at = datetime.fromisoformat(row[1])
        if datetime.now() - cached_at > timedelta(hours=max_age_hours):
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return None

    def set_cached_episodes(self, cache_key: str, episodes: list) -> None:
        """Cache episode list with current timestamp."""
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO episode_cache (cache_key, episodes_json, cached_at)
            VALUES (?, ?, ?)
        """, (cache_key, json.dumps(episodes), datetime.now().isoformat()))
        self.conn.commit()

    def close(self):
        self.conn.close()


# ┌─── File Existence Check ───────────────────────────────────────────────────┐

def check_file_exists(output_dir: str, scene_filename: str) -> bool:
    """
    Check if a file matching the scene filename already exists in output_dir.
    Also checks for .part partial downloads.

    Returns True if the complete file exists (should skip).
    """
    if not os.path.isdir(output_dir):
        return False

    target_path = os.path.join(output_dir, scene_filename)
    if os.path.exists(target_path):
        return True

    # Check for partial download — if .part exists but final doesn't,
    # we should proceed (download will complete it or overwrite)
    partial_path = target_path + ".part"
    if os.path.exists(partial_path) and not os.path.exists(target_path):
        # Remove stale partial
        try:
            os.remove(partial_path)
        except OSError:
            pass

    return False


# ┌─── Scene Filename Generation ──────────────────────────────────────────────┐

def generate_scene_filename(url: str, profile: Optional[int] = None) -> str:
    """
    Generate a scene-compliant filename for a URL.
    Uses the existing scene_namer pipeline if available.
    """
    try:
        # Try to use the existing scene_namer
        from .scene_namer import build_scene_filename
        return build_scene_filename(url, resolution=profile)
    except ImportError:
        # Fallback: use url_parser
        try:
            from .url_parser import parse_vrt_url
            vrt_info = parse_vrt_url(url)
            # Basic scene name
            if vrt_info.show_slug and vrt_info.episode_name:
                show = vrt_info.show_slug.replace("-", ".").title()
                season = vrt_info.season or "01"
                episode = vrt_info.episode_name or "E01"
                return f"{show}.S{int(season):02d}E{int(episode):02d}.WEB-DL.AAC.x264.mp4"
            return "unknown_video.mp4"
        except Exception:
            return "unknown_video.mp4"
