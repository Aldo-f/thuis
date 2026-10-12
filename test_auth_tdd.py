"""TDD: verify qBittorrent connectivity with multiple auth methods."""
import requests, sys, yaml, urllib.parse

with open("/home/aldo/dev/06-apps-thuis-v4/config.yaml") as f:
    cfg = yaml.safe_load(f)
qb = cfg.get("qbittorrent", {})
host = qb.get("host", "torrent.aldof.duckdns.org")
base = f"https://{host}"

results = {}
# 1. No auth
r1 = requests.get(f"{base}/api/v2/app/version", timeout=10)
results["no_auth"] = r1.status_code

# 2. API key header
r2 = requests.get(f"{base}/api/v2/app/version",
    headers={"X-Api-Key": qb.get("api_key", "")}, timeout=10)
results["api_key"] = r2.status_code

# 3. Cookie auth with config creds
session = requests.Session()
r3 = session.post(f"{base}/api/v2/auth/login",
    data={"username": qb.get("username", "aldo"),
          "password": qb.get("password", "")}, timeout=10)
results["cookie_login"] = r3.status_code
results["cookie_text"] = r3.text.strip()
if session.cookies.get_dict().get("SID"):
    r3b = session.get(f"{base}/api/v2/app/version", timeout=10)
    results["cookie_version"] = r3b.status_code
else:
    results["cookie_version"] = "no_cookie"

print(f"Results: {results}")
# If any method works for version endpoint, print PASS
if results.get("cookie_version") == 200 or results.get("api_key") == 200:
    print("PASS: At least one auth method works for /api/v2/app/version")
else:
    print("FAIL: No auth method works. Check server config or credentials.")
