"""Normalize video filenames to canonical scene naming format.

Scans a directory for media files, parses existing filenames, resolves
show titles via API, detects codecs, and renames files to a consistent
scene-style format.
"""

from __future__ import annotations

import time
from pathlib import Path

from thuis.codec_detector import detect_codecs
from thuis.filename_parser import ParsedFilename, parse_filename
from thuis.scene_namer import build_tv_filename
from thuis.show_resolver import resolve_show_title


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_normalize(
    directory: Path,
    dry_run: bool = False,
    cleanup: bool = False,
) -> None:
    """Rename video files in *directory* to canonical scene naming format.

    Pipeline
    --------
    1. Scan directory for ``*.mp4``, ``*.mp4.part`` and ``*.part`` files.
    2. Parse each filename with :func:`~thuis.filename_parser.parse_filename`.
    3. Group by show slug and resolve official show titles (one API call
       per unique slug).
    4. For each regular (non-part, non-duplicate) file, detect audio/video
       codecs via :func:`~thuis.codec_detector.detect_codecs`.
    5. Build a new scene-style filename with
       :func:`~thuis.scene_namer.build_tv_filename`.
    6. Rename the file if the new name differs from the old one.
    7. If *cleanup* is ``True``: remove ``_1`` duplicates (whose non-dup
       original was processed) and delete ``.part`` files older than 24 h.

    Parameters
    ----------
    directory:
        Path to the directory containing media files.
    dry_run:
        If ``True``, only print what would happen without modifying any
        files.
    cleanup:
        If ``True``, also remove ``_1`` duplicate files and stale
        ``.part`` files.
    """
    # ------------------------------------------------------------------
    # 1. Scan
    # ------------------------------------------------------------------
    files = sorted(
        {
            f
            for pattern in ("*.mp4", "*.mp4.part", "*.part")
            for f in directory.glob(pattern)
        }
    )

    if not files:
        print("Geen media-bestanden gevonden.")
        return

    # ------------------------------------------------------------------
    # 2. Parse
    # ------------------------------------------------------------------
    parsed_map: dict[Path, ParsedFilename] = {}
    for f in files:
        result = parse_filename(f)
        if result is not None:
            parsed_map[f] = result

    # ------------------------------------------------------------------
    # 3. Group by slug & resolve titles (one API call per slug)
    # ------------------------------------------------------------------
    slugs: set[str] = set()
    for pf in parsed_map.values():
        if not pf.is_part and pf.show_slug:
            slugs.add(pf.show_slug)

    titles: dict[str, str] = {}
    for slug in slugs:
        titles[slug] = resolve_show_title(slug)

    # ------------------------------------------------------------------
    # 4. Categorise files
    # ------------------------------------------------------------------
    part_entries: list[tuple[Path, ParsedFilename]] = []
    dup_entries: list[tuple[Path, ParsedFilename]] = []
    normal_entries: list[tuple[Path, ParsedFilename]] = []

    for path, pf in parsed_map.items():
        if pf.is_part:
            part_entries.append((path, pf))
        elif pf.is_duplicate:
            dup_entries.append((path, pf))
        else:
            normal_entries.append((path, pf))

    # ------------------------------------------------------------------
    # 5-6. Rename pass
    # ------------------------------------------------------------------
    renamed = 0
    processed_ids: set[tuple[str, int, int]] = set()
    claimed: set[str] = set()

    for path, pf in normal_entries:
        show_name = titles.get(pf.show_slug, pf.show_slug)
        audio_codec, video_codec = detect_codecs(path)
        new_name = build_tv_filename(
            show_name,
            pf.season,
            pf.episode,
            pf.resolution,
            audio_codec,
            video_codec,
        )
        new_path = directory / new_name

        # Already has the correct name → nothing to do
        if new_path == path:
            processed_ids.add((pf.show_slug, pf.season, pf.episode))
            continue

        # Collision with an already-existing file on disk
        if new_path.exists():
            print(
                f"WAARSCHUWING: '{new_name}' bestaat al — "
                f"overslaan van '{path.name}'"
            )
            continue

        # Collision with another file that was renamed earlier in this run
        if new_name in claimed:
            print(
                f"WAARSCHUWING: '{new_name}' wordt ook door een ander "
                f"bestand gebruikt — overslaan van '{path.name}'"
            )
            continue

        if dry_run:
            print(f"[DRY RUN] Hernoem: '{path.name}' → '{new_name}'")
        else:
            path.rename(new_path)
            print(f"Hernoemd: '{path.name}' → '{new_name}'")

        renamed += 1
        processed_ids.add((pf.show_slug, pf.season, pf.episode))
        claimed.add(new_name)

    # ------------------------------------------------------------------
    # 7. Cleanup pass
    # ------------------------------------------------------------------
    duplicates_removed = 0
    part_removed = 0

    if cleanup:
        # -- 7a. Remove _1 duplicates whose original was processed ----------
        for path, pf in dup_entries:
            identity = (pf.show_slug, pf.season, pf.episode)
            if identity not in processed_ids:
                print(
                    f"Duplicate behouden (geen origineel verwerkt): "
                    f"'{path.name}'"
                )
                continue

            if dry_run:
                print(
                    f"[DRY RUN] Verwijder duplicate: '{path.name}'"
                )
            else:
                path.unlink()
                print(f"Duplicate verwijderd: '{path.name}'")
            duplicates_removed += 1

        # -- 7b. Remove .part files older than 24 hours ---------------------
        now = time.time()
        for path, _pf in part_entries:
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue

            age_hours = (now - mtime) / 3600
            if age_hours < 24:
                continue

            if dry_run:
                print(
                    f"[DRY RUN] Verwijder part file: '{path.name}' "
                    f"({age_hours:.1f}u oud)"
                )
            else:
                path.unlink()
                print(
                    f"Part file verwijderd: '{path.name}' "
                    f"({age_hours:.1f}u oud)"
                )
            part_removed += 1

    # ------------------------------------------------------------------
    # 8. Report
    # ------------------------------------------------------------------
    print(
        f"{renamed} bestanden hernoemd, "
        f"{duplicates_removed} duplicates verwijderd, "
        f"{part_removed} part files opgeruimd"
    )
