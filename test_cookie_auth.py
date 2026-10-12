"""TDD test 2: verify cookie auth to qBittorrent."""
import requests, sys, yaml

with open("/home/aldo/dev/06-apps-thuis-v4/config.yaml") as f:
    cfg = yaml.safe_load(f)
qb = cfg.get("qbittorrent", {})
user = qb.get("username", "aldo")
pw = qb.get("password", "")
print(f"Testing cookie auth as user={user}...")

session = requests.Session()
resp = session.post("https://torrent.aldof.duckdns.org/api/v2/auth/login",
    data={"username": user, "password": pw}, timeout=10)
print(f"Login response: HTTP {resp.status_code}, body={resp.text.strip()}")
if resp.text.strip() == "Ok." and session.cookies.get_dict().get("SID"):
    sid = session.cookies.get_dict()["SID"]
    print(f"PASS: Cookie SID={sid}")
    r = session.get("https://torrent.aldof.duckdns.org/api/v2/app/version", timeout=10)
    print(f"PASS: Version endpoint -> HTTP {r.status_code}, body={r.text[:60]}")
    sys.exit(0)
else:
    print(f"FAIL: Cookie auth did not return SID (cookies={session.cookies.get_dict()})")
    sys.exit(1)
