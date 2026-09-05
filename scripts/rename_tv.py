#!/usr/bin/env python3
"""
Rename TV show files to standard naming:
{Title}.S{nn}E{nn}.{height}p.WEB-DL.AAC.x264.mp4

Usage:
  python3 rename_tv.py [--dir DIR] [--title TITLE] [--dry-run] [--execute]
"""

import subprocess
import re
import os
import sys
import argparse
from pathlib import Path


def probe_resolution(path: Path) -> str:
    """Return height tag like '1080p', '720p', '540p' from video stream (vertical resolution)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            # ffprobe csv: width,height
            parts = out.stdout.strip().split(",")
            if len(parts) == 2:
                w, h = int(parts[0]), int(parts[1])
                return f"{h}p"
    except Exception:
        pass
    return "?p"


def parse_season_episode(fname: str):
    """Extract (season, episode) from filename, zero-padded to 2 digits."""
    m = re.search(r"S(\d+)E(\d+)", fname, re.IGNORECASE)
    if m:
        return m.group(1).zfill(2), m.group(2).zfill(2)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Rename TV files to standard format")
    parser.add_argument("--dir", default=".", help="Directory containing files")
    parser.add_argument("--title", required=True, help="Show title (e.g., 'Fc.De.Kampioenen')")
    parser.add_argument("--pattern", default=r"S\d+E\d+", help="Regex to identify episode files")
    parser.add_argument("--skip-patterns", nargs="*", default=[".part", ".ytdl", ".part-Frag"],
                        help="Substrings to skip (incomplete files)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show plan only (default)")
    parser.add_argument("--execute", action="store_true", help="Actually rename files")
    args = parser.parse_args()

    if args.execute:
        args.dry_run = False

    root = Path(args.dir).expanduser().resolve()
    if not root.exists():
        print(f"Directory not found: {root}")
        sys.exit(1)

    entries = sorted(root.iterdir())
    plan = []

    for fpath in entries:
        if not fpath.is_file():
            continue
        fname = fpath.name

        # Skip incomplete files
        if any(skip in fname for skip in args.skip_patterns):
            plan.append((fname, None, "SKIP (incomplete)"))
            continue

        # Extract season/episode
        s, e = parse_season_episode(fname)
        if not s:
            plan.append((fname, None, "SKIP (no SxxExx)"))
            continue

        res_tag = probe_resolution(fpath)
        new_name = f"{args.title}.S{s}E{e}.{res_tag}.WEB-DL.AAC.x264.mp4"

        if new_name == fname:
            plan.append((fname, new_name, "ALREADY CORRECT"))
        else:
            plan.append((fname, new_name, res_tag))

    # Print plan
    print(f"{'OLD':<65} {'NEW':<70} {'STATUS'}")
    print("-" * 160)
    to_rename = 0
    for old, new, status in plan:
        if new is None:
            print(f"{old:<65} {'':<70} {status}")
        else:
            print(f"{old:<65} {new:<70} {status}")
            if status not in ("SKIP (incomplete)", "ALREADY CORRECT"):
                to_rename += 1

    print(f"\nTotal: {len(plan)} files, {to_rename} to rename")

    if args.dry_run:
        print("\n>>> DRY RUN — use --execute to apply changes")
        return

    # Execute
    renamed = 0
    for old, new, status in plan:
        if new is None or "SKIP" in status or "ALREADY" in status:
            continue
        src = root / old
        dst = root / new
        try:
            src.rename(dst)
            print(f"Renamed: {old} -> {new}")
            renamed += 1
        except Exception as e:
            print(f"FAILED: {old} -> {new}  ({e})")

    print(f"\nDone: {renamed} files renamed.")


if __name__ == "__main__":
    main()