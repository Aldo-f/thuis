"""Resolve show slug to correct Title Case name via VRT API or fallback.

Uses the VRT MAX GraphQL API as the primary source of truth. If the
API is unavailable, times out, or returns no data, the slug is
converted to Title Case locally as a silent fallback.

Typical usage::

    >>> resolve_show_title("thuis")
    'Thuis'
    >>> resolve_show_title("fc.de.kampioenen")
    'Fc.De.Kampioenen'
"""

from __future__ import annotations

import json
import urllib.request

from thuis.scene_namer import normalize_show_name

_VRT_GRAPHQL_URL = "https://www.vrt.be/vrtnu-api/graphql/v1"

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_TITLE_CACHE: dict[str, str] = {}
"""Module-level cache mapping show slug → resolved title.

Once a slug has been resolved (via API or fallback) the result is
stored here so repeated lookups for the same slug are instant.
"""

# ---------------------------------------------------------------------------
# GraphQL query
# ---------------------------------------------------------------------------

_GQL_QUERY = """\
query ($slug: String) {
    program(slug: $slug) {
        title
    }
}"""
"""VRT MAX GraphQL query to retrieve the official programme title."""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_show_title(show_slug: str) -> str:
    """Resolve *show_slug* to its official scene-normalised title.

    Tries the VRT MAX GraphQL API first. On any failure (timeout,
    network error, missing data, …) the slug is converted to Title Case
    as a silent fallback.

    Parameters
    ----------
    show_slug:
        Dotted slug as used in VRT MAX URLs, e.g. ``"fc.de.kampioenen"``
        or ``"thuis"``.

    Returns
    -------
    str
        Scene-normalised title such as ``"Fc.De.Kampioenen"`` or
        ``"Thuis"``.
    """
    # --- cache hit -------------------------------------------------------
    cached = _TITLE_CACHE.get(show_slug)
    if cached is not None:
        return cached

    # --- VRT GraphQL API -------------------------------------------------
    title = _query_api(show_slug)

    # --- fallback: Title Case slug ---------------------------------------
    if title is None:
        title = _title_case_slug(show_slug)

    # --- cache & return --------------------------------------------------
    _TITLE_CACHE[show_slug] = title
    return title


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _query_api(show_slug: str) -> str | None:
    """Query the VRT MAX GraphQL API for the official show title.

    Returns the scene-normalised title, or ``None`` when the API is
    unavailable, times out, returns an unexpected structure, or has no
    data for the given slug.
    """
    data = {"query": _GQL_QUERY, "variables": {"slug": show_slug}}
    data_bytes = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        _VRT_GRAPHQL_URL, data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "x-vrt-client-name": "WEB",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                return None
            result = json.loads(response.read().decode())
    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    try:
        raw_title: str | None = (result.get("data", {})
                                 .get("program", {})
                                 .get("title"))
    except AttributeError:
        return None

    if not raw_title or not isinstance(raw_title, str):
        return None

    return normalize_show_name(raw_title)


def _title_case_slug(slug: str) -> str:
    """Convert a dotted/hyphenated slug to Title Case.

    Rules
    -----
    * Split on ``.``, capitalise each segment via :meth:`str.capitalize`.
    * Within each segment, split on ``-`` and capitalise individually.
    * Rejoin segments with ``.`` (dots) or ``-`` (hyphens) as originally
      separated.

    Examples
    --------
    ``"fc.de.kampioenen"`` → ``"Fc.De.Kampioenen"``
    ``"thuis"``            → ``"Thuis"``
    ``"het-weer"``         → ``"Het-Weer"``
    """
    parts = slug.split(".")
    titled_parts: list[str] = []
    for part in parts:
        if not part:
            titled_parts.append("")
            continue
        sub = "-".join(word.capitalize() for word in part.split("-"))
        titled_parts.append(sub)
    return ".".join(titled_parts)
