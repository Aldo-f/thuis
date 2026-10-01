"""ext.to upload client — logs in and submits .torrent files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ExtToClient:
    """HTTP client for ext.to torrent uploads.

    Handles login (session cookie) and multipart form upload
    of .torrent files with metadata.
    """

    BASE_URL = "https://ext.to"
    LOGIN_URL = f"{BASE_URL}/login/"
    UPLOAD_URL = f"{BASE_URL}/uploader/"

    def __init__(
        self,
        username: str,
        password: str,
    ) -> None:
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._logged_in = False

    def login(self) -> bool:
        """Log into ext.to and store session cookies.

        Returns True on success, False on failure.
        """
        try:
            # First GET to pick up any CSRF token / cookies
            resp = self._session.get(self.LOGIN_URL, timeout=30)
            resp.raise_for_status()

            # Extract CSRF token if present (look for hidden input)
            csrf_token = ""
            if "csrf" in resp.text.lower():
                import re
                match = re.search(
                    r'name=["\']csrf[_\w]*["\']\s+value=["\']([^"\']+)["\']',
                    resp.text,
                    re.IGNORECASE,
                )
                if match:
                    csrf_token = match.group(1)

            data = {
                "username": self._username,
                "password": self._password,
            }
            if csrf_token:
                data["csrf_token"] = csrf_token

            resp = self._session.post(
                self.LOGIN_URL,
                data=data,
                timeout=30,
                allow_redirects=True,
            )
            # Check if we're logged in by looking for logout link or
            # absence of login form
            if resp.status_code == 200 and "logout" in resp.text.lower():
                self._logged_in = True
                logger.info("ext.to login successful")
                return True
            # Some sites redirect to dashboard on success
            if resp.status_code == 200 and "Sign in" not in resp.text:
                self._logged_in = True
                logger.info("ext.to login successful (no sign-in form)")
                return True
            logger.warning(
                "ext.to login may have failed (status=%d)", resp.status_code
            )
            return False
        except Exception as exc:
            logger.error("ext.to login error: %s", exc)
            return False

    def upload_torrent(
        self,
        torrent_path: Path,
        title: str,
        category: str = "TV",
        description: str = "",
    ) -> bool:
        """Upload a .torrent file to ext.to.

        Parameters
        ----------
        torrent_path:
            Path to the .torrent file to upload.
        title:
            Torrent title (e.g. "FC.De.Kampioenen.S01.1080p.WEB-DL.AAC.x264").
        category:
            Category string for ext.to (default "TV").
        description:
            Torrent description text.

        Returns True on success, False on failure.
        """
        if not self._logged_in:
            raise RuntimeError("Not logged in — call login() first")

        torrent_path = Path(torrent_path)
        if not torrent_path.exists():
            raise FileNotFoundError(f"Torrent file not found: {torrent_path}")

        try:
            # GET upload page to pick up any CSRF token
            resp = self._session.get(self.UPLOAD_URL, timeout=30)
            resp.raise_for_status()

            # Extract CSRF token if present
            csrf_token = ""
            if "csrf" in resp.text.lower():
                import re
                match = re.search(
                    r'name=["\']csrf[_\w]*["\']\s+value=["\']([^"\']+)["\']',
                    resp.text,
                    re.IGNORECASE,
                )
                if match:
                    csrf_token = match.group(1)

            # Determine category ID — ext.to uses numeric category IDs
            # Map common categories; may need adjustment after inspecting the form
            category_map = {
                "TV": "2",       # TV series
                "Movies": "1",    # Movies
                "Music": "3",     # Music
                "Other": "6",     # Other
            }
            cat_id = category_map.get(category, "2")

            data = {
                "title": title,
                "category": cat_id,
                "description": description,
            }
            if csrf_token:
                data["csrf_token"] = csrf_token

            with open(torrent_path, "rb") as f:
                files = {"torrent_file": (torrent_path.name, f, "application/x-bittorrent")}
                resp = self._session.post(
                    self.UPLOAD_URL,
                    data=data,
                    files=files,
                    timeout=120,
                    allow_redirects=True,
                )

            # Check for success — ext.to may redirect to the torrent page
            # or show a success message
            if resp.status_code in (200, 201, 302):
                if "success" in resp.text.lower() or "uploaded" in resp.text.lower() or resp.status_code == 302:
                    logger.info("ext.to upload successful: %s", title)
                    return True

            logger.warning(
                "ext.to upload may have failed (status=%d)", resp.status_code
            )
            # Save response for debugging
            logger.debug("ext.to upload response: %s", resp.text[:500])
            return False
        except Exception as exc:
            logger.error("ext.to upload error: %s", exc)
            return False
