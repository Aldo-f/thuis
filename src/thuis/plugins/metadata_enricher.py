"""TMDB metadata enrichment plugin.

Provides :class:`TMDBClient` for querying The Movie Database (TMDB) API v3.
Used as a postprocess plugin to enrich downloaded files with metadata
(titles, overviews, poster paths, and season/episode information).
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class TMDBClient:
    """Thin wrapper around the TMDB API v3."""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.params = {"api_key": api_key}
        self._session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Perform a GET request to *endpoint* and return the parsed JSON body.

        Returns ``None`` on any error (network failure, HTTP error, or
        malformed JSON).
        """
        try:
            resp = self._session.get(f"{self.BASE_URL}/{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup_show(
        self,
        series: str,
        season: int = 1,
        episode: int | None = None,
    ) -> dict[str, Any] | None:
        """Search for a TV series and return enriched metadata.

        Parameters
        ----------
        series:
            Show name to search for.
        season:
            Season number to look up (default ``1``).
        episode:
            Optional episode number. When provided, the result dict
            will also contain an ``episodes`` key with the matching
            episode detail(s).

        Returns
        -------
        dict or None
            Keys: ``title``, ``year``, ``overview``, ``poster_path``,
            ``seasons``. Also ``episodes`` when *episode* is given.
            Returns ``None`` on any error or when the show is not found.
        """
        try:
            search_data = self._get_json("search/tv", params={"query": series})
            if search_data is None:
                return None

            results = search_data.get("results", [])
            if not results:
                return None

            show_id = results[0].get("id")
            if show_id is None:
                return None

            tv_data = self._get_json(f"tv/{show_id}")
            if tv_data is None:
                return None

            year = self._parse_year(tv_data.get("first_air_date"))
            overview = tv_data.get("overview") or ""
            poster_path = tv_data.get("poster_path")
            seasons_list = tv_data.get("seasons") or []
            total_seasons = len(seasons_list)

            result: dict[str, Any] = {
                "title": tv_data.get("name"),
                "year": year,
                "overview": overview,
                "poster_path": poster_path,
                "seasons": total_seasons,
            }

            if episode is not None:
                ep_data = self._get_json(
                    f"tv/{show_id}/season/{season}/episode/{episode}"
                )
                if ep_data is not None:
                    result["episodes"] = [ep_data]
                else:
                    # Fallback: fetch entire season and filter by episode number.
                    season_data = self._get_json(f"tv/{show_id}/season/{season}")
                    if season_data is not None:
                        filtered = [
                            e for e in season_data.get("episodes", [])
                            if e.get("episode_number") == episode
                        ]
                        if filtered:
                            result["episodes"] = filtered

            return result

        except Exception:
            return None

    def lookup_movie(
        self,
        title: str,
        year: int | None = None,
    ) -> dict[str, Any] | None:
        """Search for a movie and return enriched metadata.

        Parameters
        ----------
        title:
            Movie title to search for.
        year:
            Optional release year for filtering.

        Returns
        -------
        dict or None
            Keys: ``title``, ``year``, ``overview``, ``poster_path``,
            ``seasons`` (always ``0`` for movies).
            Returns ``None`` on any error or when the movie is not found.
        """
        try:
            params: dict[str, Any] = {"query": title}
            if year is not None:
                params["year"] = year

            search_data = self._get_json("search/movie", params=params)
            if search_data is None:
                return None

            results = search_data.get("results", [])
            if not results:
                return None

            movie_id = results[0].get("id")
            if movie_id is None:
                return None

            movie_data = self._get_json(f"movie/{movie_id}")
            if movie_data is None:
                return None

            return {
                "title": movie_data.get("title"),
                "year": self._parse_year(movie_data.get("release_date")),
                "overview": movie_data.get("overview") or "",
                "poster_path": movie_data.get("poster_path"),
                "seasons": 0,
            }

        except Exception:
            return None

    def fetch_poster_image(
        self,
        poster_path: str,
        width: int = 500,
    ) -> bytes | None:
        """Fetch a poster image from the TMDB CDN.

        Parameters
        ----------
        poster_path:
            The ``poster_path`` value returned by a lookup call
            (e.g. ``"/abc123.jpg"``).
        width:
            Target width in pixels (default ``500``).

        Returns
        -------
        bytes or None
            Raw image bytes, or ``None`` on any error.
        """
        if not poster_path:
            return None

        url = f"{self.IMAGE_BASE}/w{width}{poster_path}"
        try:
            resp = self._session.get(url)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_year(date_str: str | None) -> int | None:
        """Extract a 4-digit year from an ISO date string."""
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            return int(date_str[:4])
        except (ValueError, IndexError):
            return None
