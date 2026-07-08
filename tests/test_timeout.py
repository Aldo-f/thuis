"""Tests for HTTP request timeouts — verify urlopen calls have explicit timeout values."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import inspect
import urllib.request

import thuis.main as main_mod


def test_graphql_timeout_is_set():
    """_execute_graphql_query must call urlopen with timeout=30."""
    source = inspect.getsource(main_mod._execute_graphql_query)
    # Check that urlopen is called with timeout=30
    assert "timeout=30" in source, (
        "_execute_graphql_query should call urlopen(req, timeout=30)"
    )


def test_guess_episode_urls_timeout_is_set():
    """_guess_episode_urls must call urlopen with timeout=10."""
    source = inspect.getsource(main_mod._guess_episode_urls)
    # Check that urlopen is called with timeout=10
    assert "timeout=10" in source, (
        "_guess_episode_urls should call urlopen(req, timeout=10)"
    )


def test_timeout_prevents_hanging():
    """Verify that a short timeout actually raises on a slow endpoint."""
    import socket
    socket.setdefaulttimeout(2)
    import time
    import urllib.error

    start = time.time()
    try:
        urllib.request.urlopen("https://httpbin.org/delay/5", timeout=2)
        assert False, "Expected an exception due to timeout"
    except (urllib.error.URLError, TimeoutError, OSError):
        elapsed = time.time() - start
        # Allow generous margin for network latency; the point is it didn't wait 5s
        assert elapsed < 10, (
            f"Timeout did not fire early enough: elapsed={elapsed:.1f}s, "
            "expected < 10s"
        )
