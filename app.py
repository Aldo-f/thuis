#!/usr/bin/env python3
"""Thuis Web UI - Flask server for VRT MAX downloads"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Paths
BASE_DIR = Path(__file__).parent
COOKIE_FILE = BASE_DIR / "cookies.json"
THUIS_SCRIPT = BASE_DIR / "thuis.py"


def load_cookies():
    """Load cookies from file"""
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE) as f:
            return json.load(f)
    return None


def save_cookies(cookies):
    """Save cookies to file"""
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)


def check_login_status():
    """Check if user is logged in via cookies"""
    cookies = load_cookies()
    if not cookies:
        return False, "No cookies found"

    # Check if cookies are still valid by looking at expiry
    # For now, assume cookies are valid if they exist
    # A more sophisticated check would test against the VRT API
    return True, "Cookies exist"


def get_episodes_from_url(url: str) -> dict:
    """Get episodes from URL using thuis.py logic"""
    # Import the parsing functions from thuis
    sys.path.insert(0, str(BASE_DIR))
    from thuis import detect_url_type, parse_episode_info

    url_type = detect_url_type(url)
    info = parse_episode_info(url)

    return {
        "url": url,
        "type": url_type,
        "program": info.get("program", ""),
        "season": info.get("season", ""),
        "episode": info.get("episode", ""),
    }


def run_thuis_download(
    url: str, output_dir: str = None, start_episode: int = None
) -> tuple:
    """Run thuis.py to download"""
    cmd = [sys.executable, str(THUIS_SCRIPT)]

    if output_dir:
        cmd.extend(["-o", output_dir])
    if start_episode:
        cmd.extend(["-s", str(start_episode)])

    cmd.append(url)

    # Run in background
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    return process.pid, cmd


@app.route("/")
def index():
    """Main page"""
    login_status, login_message = check_login_status()
    return render_template(
        "index.html", logged_in=login_status, login_message=login_message
    )


@app.route("/api/check-login", methods=["POST"])
def api_check_login():
    """Check login status"""
    login_status, login_message = check_login_status()
    return jsonify({"logged_in": login_status, "message": login_message})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Analyze URL and get episode info"""
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        result = get_episodes_from_url(url)

        # For season URLs, we'd need to actually scrape the page to get episode count
        # For now, return what we can parse
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    """Start download"""
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        pid, cmd = run_thuis_download(url)
        return jsonify(
            {"success": True, "pid": pid, "message": f"Download started (PID: {pid})"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/downloads/status")
def api_downloads_status():
    """Check running downloads"""
    # Find running thuis.py processes
    try:
        result = subprocess.run(
            ["pgrep", "-f", "thuis.py"], capture_output=True, text=True
        )
        pids = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return jsonify({"running": len(pids) > 0, "count": len(pids), "pids": pids})
    except Exception:
        return jsonify({"running": False, "count": 0})


if __name__ == "__main__":
    # Create templates folder if not exists
    templates_dir = BASE_DIR / "templates"
    templates_dir.mkdir(exist_ok=True)

    print("Starting Thuis Web UI...")
    print("Go to http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
