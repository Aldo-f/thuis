#!/usr/bin/env python3
"""
Proof-of-concept script to download VRT MAX videos using yt-dlp directly.
This is a simple wrapper that:
- Reads credentials from environment or .env (optional)
- Falls back to default credentials if none are provided
- Accepts one or more URLs as command-line arguments
- Optionally reads URLs from a file (--file)
- Supports a dry-run flag (--dry-run)
- Works on both Linux and Windows
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present
except Exception:
    pass  # dotenv optional

# Default credentials (for demonstration / testing only)
DEFAULT_EMAIL = "kuxelu@ipdeer.com"
DEFAULT_PASSWORD = "Els123456"


def get_credentials():
    """Return (email, password) from environment, falling back to defaults."""
    email = os.getenv("VRT_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("VRT_PASSWORD", DEFAULT_PASSWORD)
    return email, password


def get_yt_dlp_cmd():
    """Return the command to invoke yt-dlp with the VRT patch (version ≥ 2026.06.09)."""
    candidates = []
    path_ytdlp = shutil.which('yt-dlp')
    if path_ytdlp:
        candidates.append(path_ytdlp)
    candidates.append(os.path.join(os.path.dirname(sys.executable), 'yt-dlp'))
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        candidates.append(os.path.join(venv, 'bin', 'yt-dlp'))
    # Also check .venv/bin/yt-dlp relative to project root (parent of src/thuis/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(project_root, '.venv', 'bin', 'yt-dlp'))

    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            proc = subprocess.Popen(
                [candidate, '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, _ = proc.communicate(timeout=5)
            version = stdout.strip()
            if version >= '2026.06.09':
                return [candidate]
        except Exception:
            continue

    return [sys.executable, "-m", "yt_dlp"]


def get_yt_dlp_location():
    """Return the directory where yt-dlp is installed."""
    result = subprocess.run(
        [sys.executable, "-c", "import yt_dlp, os, sys; print(os.path.dirname(yt_dlp.__file__))"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def patch_ytdlp_if_needed():
    """No-op: patch is already included in the yt-dlp fork tag v2026.06.09-patch1.
    Kept for backward compatibility; does nothing."""
    pass


def build_yt_dlp_args(urls, dry_run=False, output_dir=Path("media")):
    """Build yt-dlp argument list."""
    args = []
    args.extend(get_yt_dlp_cmd())
    # Common options: best video+audio, merge to mp4, no warnings, no color
    args += [
        "-f", "bestvideo+bestaudio",
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--no-color",
    ]
    if dry_run:
        args.append("--simulate")
    # Add output template
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title)s.%(ext)s")
    args.extend(["-o", output_template])
    # Add credentials
    email, password = get_credentials()
    if email and password:
        args.extend(["--username", email, "--password", password])
    # Append URLs
    args.extend(urls)
    return args


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download VRT MAX videos using yt-dlp (POC)")
    parser.add_argument("urls", nargs="*", help="VRT MAX URL(s) to download")
    parser.add_argument("--file", type=Path, help="Path to a file containing URLs (one per line)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate download without downloading")
    parser.add_argument("-S", "--output-dir", type=Path, default=Path("media"), help="Directory to save downloaded files (default: media)")
    args = parser.parse_args()

    # Collect URLs
    urls = list(args.urls)
    if args.file:
        if not args.file.is_file():
            sys.exit(f"Error: file not found: {args.file}")
        with args.file.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    if not unique_urls:
        parser.print_help()
        sys.exit(1)

    # Optionally apply patch before running
    try:
        patch_ytdlp_if_needed()
    except Exception as e:
        print(f"Warning: could not apply patch: {e}", flush=True)

    # Build yt-dlp arguments
    args_list = build_yt_dlp_args(unique_urls, dry_run=args.dry_run, output_dir=args.output_dir)

    # Run yt-dlp
    print("Running:", " ".join(args_list))
    try:
        result = subprocess.run(args_list, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()