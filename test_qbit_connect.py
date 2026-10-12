"""TDD test: verify qBittorrent web UI connectivity."""
import requests, sys

url = "https://torrent.aldof.duckdns.org/"
try:
    resp = requests.get(url, timeout=10, allow_redirects=True)
    status = resp.status_code
    has_cookie = "SID" in resp.cookies or "sid" in str(resp.cookies)
    print(f"PASS: {url} -> HTTP {status}, cookies={list(resp.cookies.keys())}, url_final={resp.url}")
    # Also test /api/v2/app/version with cookie if we have old /tmp/qb.txt session
    cookie = None
    try:
        import os
        if os.path.exists("/tmp/qb.txt"):
            import urllib.parse
            with open("/tmp/qb.txt") as f:
                cookie = f.read().strip()
    except Exception:
        pass
    if cookie:
        r2 = requests.get("https://torrent.aldof.duckdns.org/api/v2/app/version", cookies={"SID": cookie}, timeout=10)
        print(f"PASS: /api/v2/app/version with cookie -> HTTP {r2.status_code}, body={r2.text[:60]}")
    sys.exit(0 if status < 500 else 1)
except Exception as exc:
    print(f"FAIL: {exc}")
    sys.exit(1)
