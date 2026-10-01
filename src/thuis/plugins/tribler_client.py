"""Tribler REST API client — submits torrents for anonymous seeding."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class TriblerClient:
    """Submits .torrent files to Tribler for anonymous seeding.

    Uses the Tribler REST API (default port 8085) to add torrents
    with configurable anonymity hops and safe_seeding.
    """

    def __init__(
        self,
        api_port: int = 8085,
        api_key: str = "",
        anon_hops: int = 3,
        safe_seeding: bool = True,
    ) -> None:
        self._api_port = api_port
        self._api_key = api_key
        self._anon_hops = anon_hops
        self._safe_seeding = safe_seeding
        self._base_url = f"http://localhost:{api_port}"

    def add_torrent(self, torrent_path: Path) -> bool:
        """Submit a .torrent file to Tribler for download + seeding.

        Parameters
        ----------
        torrent_path:
            Path to the .torrent file.

        Returns True on success, False on failure (never raises).
        """
        torrent_path = Path(torrent_path)
        if not torrent_path.exists():
            logger.error("Tribler: torrent file not found: %s", torrent_path)
            return False

        try:
            # Read torrent file and base64-encode it
            torrent_bytes = torrent_path.read_bytes()
            torrent_b64 = base64.b64encode(torrent_bytes).decode("ascii")

            url = f"{self._base_url}/downloads"
            params = {
                "uri": f"file:{torrent_path}",
                "anon_hops": str(self._anon_hops),
                "safe_seeding": str(self._safe_seeding).lower(),
                "destination": str(torrent_path.parent),
            }
            headers = {}
            if self._api_key:
                headers["X-Api-Key"] = self._api_key

            # Tribler PUT /downloads with torrent metadata
            # Some versions accept file upload, others accept URI
            resp = requests.put(
                url,
                params=params,
                headers=headers,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                logger.info(
                    "Tribler: added %s (hops=%d, safe_seeding=%s)",
                    torrent_path.name,
                    self._anon_hops,
                    self._safe_seeding,
                )
                return True

            logger.warning(
                "Tribler: add failed (status=%d): %s",
                resp.status_code,
                resp.text[:200],
            )
            return False
        except Exception as exc:
            logger.warning("Tribler: add_torrent error: %s", exc)
            return False
