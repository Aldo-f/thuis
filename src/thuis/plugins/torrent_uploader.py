"""Torrent uploader plugin using python-libtorrent.

Creates valid .torrent files from local media files or directories.
Does NOT upload to any tracker — only generates the .torrent metadata.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import libtorrent as lt
except ImportError:  # pragma: no cover
    lt = None


def _build_description(
    metadata: dict[str, Any],
    tmdb: dict[str, Any] | None,
    image_url: str | None = None,
) -> str:
    """Build a human-readable description from metadata + optional TMDB data.

    Format::

        Show Name (Year)
        S01E01 - Episode Title

        Overview text here...

        [![Poster](url)](url)

        Resolution: 1080p
        Codec: H.264 / AAC
    """
    lines: list[str] = []

    series = metadata.get("series") or ""
    year = ""
    overview = ""
    if tmdb:
        year = str(tmdb.get("year") or "")
        overview = tmdb.get("overview") or ""

    if year:
        lines.append(f"{series} ({year})")
    else:
        lines.append(series)

    season = metadata.get("season")
    episode = metadata.get("episode")
    title = metadata.get("title") or ""
    if season and episode:
        try:
            s = int(season)
            e = int(episode)
            ep_line = f"S{s:02d}E{e:02d}"
            if title:
                ep_line = f"{ep_line} - {title}"
            lines.append(ep_line)
        except (ValueError, TypeError):
            pass

    if overview:
        lines.append("")
        lines.append(overview)

    if image_url:
        lines.append("")
        lines.append(f"[![Poster](https://image.tmdb.org/t/p/w92{tmdb.get('poster_path') or ''})]({image_url})")

    resolution = metadata.get("height")
    vcodec = metadata.get("vcodec_label") or metadata.get("vcodec_raw") or ""
    acodec = metadata.get("acodec_label") or metadata.get("acodec_raw") or ""
    codec_parts = [p for p in (vcodec, acodec) if p]
    if resolution or codec_parts:
        if resolution:
            lines.append(f"Resolution: {resolution}p")
        if codec_parts:
            lines.append("Codec: " + " / ".join(codec_parts))

    return "\n".join(lines)


class TorrentUploader:
    """Creates .torrent files from local media using python-libtorrent."""

    def __init__(
        self,
        trackers: list[str] | None = None,
        piece_size: int = 262144,
        comment: str = "",
        source: str = "",
    ) -> None:
        if lt is None:
            raise RuntimeError(
                "python-libtorrent is not installed. "
                "Install it with: pip install libtorrent"
            )
        self._trackers: list[str] = list(trackers or [])
        self._piece_size: int = piece_size
        self._comment: str = comment
        self._source: str = source

    # ------------------------------------------------------------------
    # Configurable properties
    # ------------------------------------------------------------------

    @property
    def announce_urls(self) -> list[str]:
        """Tracker URLs configured for this uploader."""
        return list(self._trackers)

    @announce_urls.setter
    def announce_urls(self, urls: list[str]) -> None:
        self._trackers = list(urls)

    @property
    def comment(self) -> str:
        """Comment stored in the torrent info dictionary."""
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        self._comment = value

    @property
    def source(self) -> str:
        """Creator/source string stored in the torrent."""
        return self._source

    @source.setter
    def source(self, value: str) -> None:
        self._source = value

    @property
    def piece_size(self) -> int:
        """Piece size in bytes used when creating the torrent."""
        return self._piece_size

    @piece_size.setter
    def piece_size(self, value: int) -> None:
        if value <= 0:
            raise ValueError(f"piece_size must be positive, got {value}")
        self._piece_size = value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_torrent(
        self,
        filepath: Path,
        trackers: list[str] | None = None,
        piece_size: int | None = None,
    ) -> Path:
        """Create a .torrent file and return its path.

        Parameters
        ----------
        filepath:
            Path to the source file or directory.
        trackers:
            Optional tracker URLs (overrides instance default).
        piece_size:
            Optional piece size in bytes (overrides instance default).

        Returns
        -------
        Path to the generated .torrent file. For a single file ``foo.mp4``
        the output is ``foo.torrent``; for a directory ``Show.S01`` the
        output is ``Show.S01.torrent``.

        Raises
        ------
        FileNotFoundError:
            If *filepath* does not exist.
        RuntimeError:
            If libtorrent fails to create the torrent.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Source not found: {path}")

        effective_trackers = trackers if trackers is not None else self._trackers
        effective_piece_size = piece_size if piece_size is not None else self._piece_size

        try:
            return self._create(
                path=path,
                trackers=effective_trackers,
                piece_size=effective_piece_size,
            )
        except FileNotFoundError:
            raise
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Failed to create torrent: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create(
        self,
        *,
        path: Path,
        trackers: list[str],
        piece_size: int,
    ) -> Path:
        """Core torrent creation logic."""
        fs = lt.file_storage()

        if path.is_dir():
            lt.add_files(fs, str(path))
            # add_files includes the directory basename in every path
            # (e.g. "Show.S01/ep1.mp4"). set_piece_hashes must therefore
            # be called on the PARENT directory so it resolves to
            # <parent>/<dirname>/<file>.
            hash_root = str(path.parent)
            output_name = path.name
        else:
            lt.add_files(fs, str(path))
            # Single file: path in torrent is just the filename.
            hash_root = str(path.parent)
            output_name = path.stem

        if fs.num_files() == 0:
            raise RuntimeError(f"No files found in: {path}")

        tor = lt.create_torrent(fs, piece_size=piece_size)
        tor.set_comment(self._comment)
        tor.set_creator(self._source)

        for url in trackers:
            tor.add_tracker(url)

        logger.debug(
            "Hashing %d file(s) from %r with piece_size=%d",
            fs.num_files(),
            hash_root,
            piece_size,
        )
        lt.set_piece_hashes(tor, hash_root)

        torrent_data = lt.bencode(tor.generate())

        out_path = path.parent / f"{output_name}.torrent"
        out_path.write_bytes(torrent_data)
        logger.info(
            "Created .torrent: %s (%d bytes, %d file(s))",
            out_path,
            len(torrent_data),
            fs.num_files(),
        )
        return out_path


# ---------------------------------------------------------------------------
# postprocess — main entry point called by the plugin host
# ---------------------------------------------------------------------------

def postprocess(ctx: PostprocessContext) -> bool:  # type: ignore[name-defined]  # noqa: F821
    """Create a .torrent file for the downloaded media.

    Reads tracker and piece_size configuration from
    ``ctx._plugin_config`` (populated by the plugin host).
    Looks up TMDB metadata when available and embeds a
    formatted description in the torrent comment.

    Returns
    -------
    True on success, False on any failure (never raises).
    """
    filepath = Path(ctx.filepath)
    if not filepath.exists():
        logger.warning("Torrent upload skipped — file not found: %s", filepath)
        return False

    try:
        plugin_config = getattr(ctx, "_plugin_config", {}) or {}
        trackers = plugin_config.get("trackers")
        piece_size = plugin_config.get("piece_size") or 262144
        source = plugin_config.get("source", "thuis")
        tmdb_key = plugin_config.get("tmdb_key")

        tmdb_data: dict[str, Any] | None = None
        if tmdb_key:
            from .metadata_enricher import TMDBClient
            client = TMDBClient(api_key=tmdb_key)
            series = ctx.metadata.get("series")
            season = ctx.metadata.get("season")
            episode = ctx.metadata.get("episode")
            if series:
                try:
                    s = int(season) if season else 1
                    e = int(episode) if episode else None
                except (ValueError, TypeError):
                    s, e = 1, None
                tmdb_data = client.lookup_show(series, season=s, episode=e)
                if tmdb_data:
                    logger.debug("TMDB enrichment for %s (S%ds%d)", series, s, e or 0)
                else:
                    logger.debug("No TMDB data for %s", series)

        image_url: str | None = None
        imgbb_key = plugin_config.get("imgbb_api_key")
        if imgbb_key and tmdb_data and tmdb_data.get("poster_path"):
            from .metadata_enricher import ImgBBUploader
            poster_bytes = client.fetch_poster_image(tmdb_data["poster_path"], width=500)
            if poster_bytes:
                image_url = ImgBBUploader(imgbb_key).upload(
                    poster_bytes,
                    name=f"{series}_s{season}e{episode}",
                )
                if image_url:
                    logger.info("Uploaded poster to %s", image_url)
                else:
                    logger.warning("Failed to upload poster to ImgBB")

        description = _build_description(ctx.metadata, tmdb_data, image_url)
        comment = plugin_config.get("comment", "")
        if comment:
            description = comment + "\n\n" + description

        uploader = TorrentUploader(
            trackers=trackers,
            piece_size=piece_size,
            comment=description,
            source=source,
        )

        if ctx.dry_run:
            logger.info("[dry-run] Would create .torrent for: %s", filepath)
            return True

        out_torrent = uploader.create_torrent(filepath)
        logger.info("Created .torrent: %s", out_torrent)

        # --- Season completion check + upload ---
        season = ctx.metadata.get("season")
        series = ctx.metadata.get("series")
        if season and series and not ctx.dry_run:
            try:
                from thuis.plugins.season_detector import SeasonDetector
                detector = SeasonDetector(
                    download_dir=Path(ctx.filepath).parent,
                    show_name=series,
                    season=int(season),
                    tmdb_key=plugin_config.get("tmdb_key", ""),
                )
                is_complete, missing, expected = detector.check()
                if is_complete and expected > 0:
                    logger.info(
                        "Season %s complete (%d episodes) — creating season torrent",
                        season, expected,
                    )
                    # Collect all episode files
                    episode_files = detector.collect_files()
                    # Create season torrent from all files
                    season_out = uploader.create_torrent(
                        Path(ctx.filepath).parent,
                        trackers=trackers,
                    )
                    logger.info("Created season .torrent: %s", season_out)

                    # Upload to ext.to
                    ext_to_cfg = plugin_config.get("ext_to", {})
                    if ext_to_cfg.get("username") and ext_to_cfg.get("password"):
                        from thuis.plugins.ext_to_client import ExtToClient
                        ext_client = ExtToClient(
                            username=ext_to_cfg["username"],
                            password=ext_to_cfg["password"],
                        )
                        if ext_client.login():
                            season_title = f"{series}.S{int(season):02d}.1080p.WEB-DL.AAC.x264"
                            ext_client.upload_torrent(
                                torrent_path=season_out,
                                title=season_title,
                                category="TV",
                                description=description,
                            )
                        else:
                            logger.warning("ext.to login failed — season torrent not uploaded")

                    # Submit to Tribler for anonymous seeding
                    tribler_cfg = plugin_config.get("tribler", {})
                    if tribler_cfg.get("enabled", False):
                        from thuis.plugins.tribler_client import TriblerClient
                        tribler = TriblerClient(
                            api_port=tribler_cfg.get("api_port", 8085),
                            api_key=tribler_cfg.get("api_key", ""),
                            anon_hops=tribler_cfg.get("anon_hops", 3),
                            safe_seeding=tribler_cfg.get("safe_seeding", True),
                        )
                        tribler.add_torrent(season_out)
                else:
                    logger.info(
                        "Season %s not complete (%d missing) — skipping season upload",
                        season, len(missing),
                    )
            except Exception as exc:
                logger.warning("Season upload check failed: %s", exc)

        return True

    except Exception as exc:
        logger.error("Torrent uploader failed: %s", exc)
        return False
