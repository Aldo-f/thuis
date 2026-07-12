import sys
import os
import signal
import time
import subprocess
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


def test_ctrl_c_handler():
    """Run the main script, send SIGINT, and verify graceful interruption.

    The script should catch KeyboardInterrupt and print "Interrupted by user".
    No stack trace should appear in stdout.
    """
    # Use a dummy URL; the script will start and then we interrupt it immediately.
    dummy_url = "https://www.vrt.be/vrtmax/a-z/thuis/2/"
    cmd = [sys.executable, "-u", str(Path('src/thuis/main.py')), dummy_url]

    # Start the process
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    # Give the script time to start and install signal handler
    time.sleep(2)

    # Send SIGINT (Ctrl+C) immediately without waiting
    proc.send_signal(signal.SIGINT)

    try:
        out, _ = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()

    # Assertions
    # Expect non-zero exit code indicating interruption and no traceback.
    assert proc.returncode != 0, f"Expected non-zero exit code, got {proc.returncode}"
    assert any(msg in out for msg in ["Interrupted by user", "Interrupted"]), "Expected interruption message not found"
    assert "Traceback" not in out, "Unexpected traceback in output"


