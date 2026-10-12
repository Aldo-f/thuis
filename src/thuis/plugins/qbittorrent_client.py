"""
qBittorrent API client for thuis-v4.
Provides methods to add torrents to qBittorrent WebUI with category and tags.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import requests
import time

log = logging.getLogger(__name__)


class QBittorrentClient:
    """Client for qBittorrent WebUI API."""

    def __init__(
        self,
        host: str = "localhost:8080",
        username: str = "",
        password: str = "",
        api_key: str = "",
        socks5_proxy: Optional[str] = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.api_key = api_key
        self.socks5_proxy = socks5_proxy
        self.url_base = (
            f"https://{self.host}"
            if self.host.startswith("torrent.aldof.duckdns.org") or self.host.startswith("http")
            else f"http://{self.host}"
        )
        self.session = requests.Session()
        if self.socks5_proxy:
            self.session.proxies = {
                "http": f"socks5://{self.socks5_proxy}",
                "https": f"socks5://{self.socks5_proxy}",
            }
        self._auth_cookie = None


    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests.
        
        Only set X-Api-Key if cookie auth is NOT used.
        """
        headers = {}
        if self.api_key and not self._auth_cookie:
            headers["X-Api-Key"] = self.api_key
        return headers

    def _normalize_save_path(self, save_path: str, host_mounts: list[str] | None = None, download_prefix: str = "/downloads") -> str:
        """Normalize save_path for qBittorrent container compatibility.
        
        Configurable via config: qbittorrent.host_mounts + qbittorrent.download_prefix.
        Defaults preserved for backward compatibility.
        """
        if host_mounts is None:
            host_mounts = [
                "/mnt/HDD1/nextcloud/data/aldo/files",
                "/mnt/HDD1/services/nextcloud/data/aldo/files",
            ]
        for prefix in host_mounts:
            if save_path.startswith(prefix):
                return download_prefix + save_path[len(prefix):]
        return save_path

    def _has_valid_session(self) -> bool:
        """Return True if the session cookie is usable for API calls."""
        if self.api_key:
            # API key takes precedence; server may reject it.
            return False
        if self._auth_cookie:
            return True
        return False

    def auth_log_in(self) -> bool:
        """Log in to qBittorrent WebUI (cookie auth) or verify API key."""
        # If username is configured, prefer cookie auth (more reliable
        # with the current server that rejects the API key).
        if self.username or self.password:
            data = {
                "username": self.username or "aldo",
                "password": self.password or "",
            }
            try:
                resp = self.session.post(
                    f"{self.url_base}/api/v2/auth/login",
                    data=data,
                )
                resp.raise_for_status()
                # qBittorrent returns 204 No Content on success (not "Ok.")
                if resp.status_code in (200, 204):
                    cookies = self.session.cookies.get_dict()
                    # Cookie name varies by port (QBT_SID_8080 vs SID)
                    self._auth_cookie = (
                        cookies.get("SID")
                        or cookies.get("QBT_SID_8080")
                        or cookies.get("QBT_SID_443")
                    )
                    return self._auth_cookie is not None
                return False
            except Exception as exc:
                log.error("Failed to log in to qBittorrent: %s", exc)
                return False
        # Fallback to API key (may fail with 403 on some servers).
        if self.api_key:
            return True
        return False

    def auth_log_out(self) -> None:
        """Log out from qBittorrent WebUI."""
        if self._auth_cookie:
            try:
                self.session.get(f"{self.url_base}/api/v2/auth/logout")
            except Exception:
                pass
            self._auth_cookie = None

    def app_version(self) -> Optional[str]:
        """Get qBittorrent application version."""
        try:
            resp = self.session.get(
                f"{self.url_base}/api/v2/app/version",
                headers=self._get_auth_headers(),
            )
            resp.raise_for_status()
            return resp.text.strip()
        except Exception as e:
            log.error(f"Failed to get qBittorrent version: {e}")
            return None

    def add_torrent(
        self,
        torrent_file: Path,
        save_path: str = ".",
        category: str = "",
        tags: str = "",
        skip_checking: bool = False,
        paused: bool = False,
        root_folder: bool = False,
        rename: str = "",
        up_limit: int = 0,
        dl_limit: int = 0,
        auto_managed: bool = True,
        sequential_download: bool = False,
        first_last_prio: bool = False,
    ) -> bool:
        """Add a torrent file to qBittorrent.

        Args:
            torrent_file: str | Path,
            save_path: str,
            category: Category to assign
            tags: Comma-separated tags
            skip_checking: Skip hash checking
            paused: Start torrent in paused state
            root_folder: Create root folder
            rename: Rename the torrent
            up_limit: Upload speed limit (0 = unlimited)
            dl_limit: Download speed limit (0 = unlimited)
            auto_managed: Enable auto-management
            sequential_download: Download sequentially
            first_last_prio: Prioritize first/last pieces

        Returns:
            True if torrent added successfully
        """
        torrent_file = Path(torrent_file)
        if not torrent_file.exists():
            log.error(f"Torrent file not found: {torrent_file}")
            return False

        url = f"{self.url_base}/api/v2/torrents/add"
        headers = self._get_auth_headers()
        # Do NOT set Content-Type manually; requests handles multipart/form-data
        # automatically when files= is used (required boundary).

        with open(torrent_file, "rb") as f:
            files = {"torrents": (torrent_file.name, f, "application/x-bittorrent")}
            data = {
                "savepath": self._normalize_save_path(save_path),
                "category": category,
                "tags": tags,
                "skip_checking": str(skip_checking).lower(),
                "paused": str(paused).lower(),
                "root_folder": str(root_folder).lower(),
                "rename": rename,
                "up_limit": str(up_limit),
                "dl_limit": str(dl_limit),
                "auto_managed": str(auto_managed).lower(),
                "sequential_download": str(sequential_download).lower(),
                "first_last_prio": str(first_last_prio).lower(),
            }
            for attempt in range(2):
                try:
                    # Re-open file on each attempt to avoid EOF issues
                    with open(torrent_file, "rb") as f2:
                        files2 = {"torrents": (torrent_file.name, f2, "application/x-bittorrent")}
                        resp2 = self.session.post(url, headers=headers, files=files2, data=data)
                        # 409 Conflict = torrent already exists (idempotent — not an error)
                        if resp2.status_code == 409:
                            log.info("Torrent already in qBittorrent (409 Conflict, savepath=%s)", save_path)
                            return True
                        resp2.raise_for_status()
                        result2 = resp2.text.strip() == "Ok."
                        if result2:
                            log.info("Torrent added to qBittorrent (savepath=%s, attempt=%d)", save_path, attempt + 1)
                        return result2
                except Exception as e2:
                    if attempt == 0:
                        log.warning("qBittorrent add attempt %d failed (%s), retrying...", attempt + 1, e2)
                        time.sleep(1)
                        continue
                    log.error("Failed to add torrent to qBittorrent after retries: %s (savepath=%s)", e2, save_path)
                    return False

    def set_torrent_category(self, hash: str, category: str) -> bool:
        """Set category for a torrent by hash."""
        url = f"{self.url_base}/api/v2/torrents/setCategory"
        headers = self._get_auth_headers()
        data = {"hash": hash, "category": category}
        try:
            resp = self.session.post(url, headers=headers, data=data)
            resp.raise_for_status()
            return resp.text.strip() == "Ok."
        except Exception as e:
            log.error(f"Failed to set torrent category: {e}")
            return False

    def set_torrent_tags(self, hash: str, tags: str) -> bool:
        """Set tags for a torrent by hash."""
        url = f"{self.url_base}/api/v2/torrents/addTags"
        headers = self._get_auth_headers()
        data = {"hash": hash, "tags": tags}
        try:
            resp = self.session.post(url, headers=headers, data=data)
            resp.raise_for_status()
            return resp.text.strip() == "Ok."
        except Exception as e:
            log.error(f"Failed to set torrent tags: {e}")
            return False

    def torrents_info(self, hash: Optional[str] = None) -> list[dict]:
        """Get information about torrents."""
        url = f"{self.url_base}/api/v2/torrents/info"
        headers = self._get_auth_headers()
        params = {}
        if hash:
            params["hash"] = hash
        try:
            resp = self.session.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            log.error(f"Failed to get torrent info: {e}")
            return []

    def close(self) -> None:
        """Close the session."""
        self.auth_log_out()
        self.session.close()