"""
FFmpeg transcoding utilities for thuis.

Provides post-download transcoding to target resolution.
"""

from __future__ import annotations

import subprocess
import logging
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def get_video_resolution(path: Path) -> Optional[int]:
    """Get video height from file using ffprobe.
    
    Returns height in pixels (e.g., 1080, 720) or None on failure.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "v:0",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0:
        return None

    try:
        import json
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    streams = data.get("streams", [])
    if not streams:
        return None

    return streams[0].get("height")


def parse_target_height(target: str) -> int:
    """Parse target height from string like '720p' or '720'."""
    match = re.search(r"(\d+)", str(target))
    if match:
        return int(match.group(1))
    return 720


def should_transcode(
    path: Path,
    target_height: int,
    allow_upscale: bool = False,
) -> bool:
    """Check if file should be transcoded to target height.
    
    Returns True if:
    - Video resolution is higher than target (downscale)
    - Video resolution is lower than target AND allow_upscale is True (upscale)
    """
    height = get_video_resolution(path)
    if height is None:
        return False
    
    if height > target_height:
        return True  # Downscale
    
    if height < target_height and allow_upscale:
        return True  # Upscale
    
    return False  # Already at target or no upscale allowed


def transcode_to_target(
    input_path: Path,
    output_path: Path,
    target_height: int,
    preset: str = "fast",
    crf: int = 23,
    keep_original: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Transcode video to target height using FFmpeg."""
    if not check_ffmpeg():
        return False, "FFmpeg not found"

    if not input_path.exists():
        return False, f"Input file not found: {input_path}"

    # Ensure output has .mp4 extension
    if output_path.suffix.lower() != ".mp4":
        output_path = output_path.with_suffix(".mp4")

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", str(input_path),
        "-vf", f"scale=1280:{target_height}",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-c:a", "copy",  # Copy audio stream without re-encoding
        "-movflags", "+faststart",  # Optimize for streaming
        str(output_path),
    ]

    logger.info(f"Transcoding {input_path.name} to {target_height}p...")
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max
        )
    except subprocess.TimeoutExpired:
        return False, "Transcoding timed out"
    except OSError as e:
        return False, f"FFmpeg execution failed: {e}"

    if result.returncode != 0:
        error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
        return False, f"FFmpeg failed: {error_msg}"

    if not output_path.exists():
        return False, "Output file was not created"

    # Verify output
    out_height = get_video_resolution(output_path)
    if out_height is None or out_height != target_height:
        logger.warning(f"Output resolution unexpected: {out_height}")

    # Handle original file
    if not keep_original:
        try:
            input_path.unlink()
            logger.info(f"Removed original: {input_path.name}")
        except OSError as e:
            logger.warning(f"Could not remove original: {e}")

    logger.info(f"Transcoding complete: {output_path.name}")
    return True, None


def find_best_source_for_transcoding(
    files: List[Path],
    target_height: int,
) -> Optional[Path]:
    """Find the best source file for transcoding to target height.
    
    Prefers:
    1. File with resolution closest to but higher than target (downscale)
    2. If none higher, file with highest resolution (for upscale)
    """
    if not files:
        return None
    
    files_with_res = []
    for f in files:
        res = get_video_resolution(f)
        if res is not None:
            files_with_res.append((f, res))
    
    if not files_with_res:
        return None
    
    # Sort by distance to target (prefer higher resolutions for downscale)
    files_with_res.sort(key=lambda x: (x[1] < target_height, abs(x[1] - target_height)))
    
    # Prefer files that are higher than target (for downscale)
    higher = [(f, r) for f, r in files_with_res if r > target_height]
    if higher:
        # Return the one closest to target but still higher
        higher.sort(key=lambda x: x[1])
        return higher[0][0]
    
    # No higher resolution, return highest available (for upscale)
    files_with_res.sort(key=lambda x: x[1], reverse=True)
    return files_with_res[0][0]


def transcode_file_if_needed(
    path: Path,
    keep_original: bool = False,
    target_height: int = 720,
    allow_upscale: bool = False,
) -> Tuple[bool, Optional[Path], Optional[str]]:
    """Check and transcode a file to target height if needed."""
    if not path.exists():
        return False, None, f"File not found: {path}"

    current_height = get_video_resolution(path)
    if current_height is None:
        return False, None, "Could not determine resolution"

    # Check if transcoding is needed
    if current_height == target_height:
        logger.info(f"File already at target resolution ({target_height}p): {path.name}")
        return False, path, None
    
    if current_height > target_height:
        logger.info(f"Downscaling {current_height}p to {target_height}p: {path.name}")
    elif current_height < target_height and allow_upscale:
        logger.info(f"Upscaling {current_height}p to {target_height}p: {path.name}")
    else:
        logger.info(f"File at {current_height}p, target {target_height}p, upscale not allowed: {path.name}")
        return False, path, None

    # Generate output path
    if keep_original:
        output_path = path.with_stem(f"{path.stem}_{target_height}p")
    else:
        output_path = path

    success, error = transcode_to_target(
        input_path=path,
        output_path=output_path,
        target_height=target_height,
        keep_original=keep_original,
    )

    if success:
        return True, output_path, None
    else:
        return False, None, error


def find_related_files(directory: Path, base_name: str) -> List[Path]:
    """Find all files with the same base name (different resolutions)."""
    files = []
    for ext in ['.mp4', '.mkv', '.avi', '.mov']:
        files.extend(directory.glob(f"{base_name}*{ext}"))
    return files


def find_episode_groups(files: List[Path]) -> Dict[str, List[Path]]:
    """Group files by episode identifier (SxxExx or date)."""
    import re
    groups: Dict[str, List[Path]] = {}
    
    for f in files:
        # Try SxxExx pattern first
        match = re.search(r'(S\d{2}E\d{2})', f.name, re.IGNORECASE)
        if match:
            key = match.group(1).upper()
            groups.setdefault(key, []).append(f)
            continue
        
        # Try date pattern (e.g., d20260706)
        match = re.search(r'(d\d{8})', f.name)
        if match:
            key = match.group(1)
            groups.setdefault(key, []).append(f)
            continue
        
        # Fallback: use full stem
        key = f.stem
        groups.setdefault(key, []).append(f)
    
    return groups


def scan_directory_for_videos(
    directory: Path,
    filters: List[str],
    recursive: bool = False,
) -> List[Path]:
    """Scan directory for video files, applying filters."""
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.ts', '.webm'}
    files = []
    
    if recursive:
        all_files = directory.rglob("*")
    else:
        all_files = directory.glob("*")
    
    filters_lower = [f.lower() for f in filters] if filters else []
    
    for f in all_files:
        if not f.is_file():
            continue
        if f.suffix.lower() not in {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.ts', '.webm'}:
            continue
        
        # Apply filters (case-insensitive substring match)
        if filters_lower:
            fname_lower = f.name.lower()
            if not any(filt in fname_lower for filt in filters_lower):
                continue
        
        files.append(f)
    
    return files


def transcode_worker(
    source_path: Path,
    target_path: Path,
    target_height: int,
    preset: str,
    crf: int,
    keep_original: bool,
) -> Tuple[Path, bool, Optional[str]]:
    """Worker function for parallel transcoding."""
    success, error = transcode_to_target(
        input_path=source_path,
        output_path=target_path,
        target_height=target_height,
        preset=preset,
        crf=crf,
        keep_original=keep_original,
    )
    return (source_path, success, error)


def batch_transcode_directory(
    directory: Path,
    target_height: int,
    filters: Optional[List[str]] = None,
    recursive: bool = False,
    parallel: int = 2,
    allow_upscale: bool = False,
    keep_original: bool = True,
    preset: str = "fast",
    crf: int = 23,
    dry_run: bool = False,
) -> Dict[str, int]:
    """Batch transcode video files in a directory.
    
    Args:
        directory: Directory to scan for video files
        target_height: Target resolution height (e.g., 720)
        filters: List of filter strings (case-insensitive substring match)
        recursive: Scan subdirectories recursively
        parallel: Number of concurrent transcoding jobs
        allow_upscale: Allow upscaling lower resolutions
        keep_original: Keep original file alongside transcoded version
        preset: FFmpeg preset
        crf: FFmpeg CRF quality
        dry_run: Preview without actual transcoding
        
    Returns:
        Dictionary with stats: {total, transcoded, skipped, failed}
    """
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory not found: {directory}")
        return {"total": 0, "transcoded": 0, "skipped": 0, "failed": 0}
    
    # Scan for video files
    filters = filters or []
    logger.info(f"Scanning {directory} (recursive={recursive})...")
    video_files = scan_directory_for_videos(directory, filters, recursive)
    logger.info(f"Found {len(video_files)} video file(s)")
    
    if not video_files:
        return {"total": 0, "transcoded": 0, "skipped": 0, "failed": 0}
    
    # Group by episode
    episode_groups = find_episode_groups(video_files)
    logger.info(f"Grouped into {len(episode_groups)} episode(s)")
    
    # Plan transcoding jobs
    jobs = []
    for episode_key, group_files in episode_groups.items():
        # Check if target resolution already exists
        target_exists = False
        for f in group_files:
            current_height = get_video_resolution(f)
            if current_height == target_height:
                logger.debug(f"Target {target_height}p already exists for {episode_key}: {f.name}")
                target_exists = True
                break
        
        if target_exists:
            continue
        
        # Find best source for transcoding
        best_source = find_best_source_for_transcoding(group_files, target_height)
        if not best_source:
            logger.warning(f"No valid source for {episode_key}")
            continue
        
        # Determine output path
        source = best_source
        if keep_original:
            output_path = source.with_stem(f"{source.stem}_{target_height}p")
        else:
            output_path = source
        
        # Check if upscale is needed and allowed
        current_height = get_video_resolution(source)
        if current_height is not None:
            if current_height < target_height and not allow_upscale:
                logger.info(f"Skipping {source.name}: {current_height}p -> {target_height}p requires upscale (not allowed)")
                continue
            if current_height == target_height:
                continue
        
        jobs.append((source, target_height, keep_original))
    
    logger.info(f"Planned {len(jobs)} transcoding job(s)")
    
    if dry_run:
        for source, _, _ in jobs:
            logger.info(f"[DRY-RUN] Would transcode: {source.name}")
        return {"total": len(jobs), "transcoded": 0, "skipped": 0, "failed": 0}
    
    # Execute transcoding in parallel
    stats = {"total": len(jobs), "transcoded": 0, "skipped": 0, "failed": 0}
    
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        future_to_source = {
            executor.submit(
                transcode_worker,
                source,
                Path(str(source).replace(f".{source.suffix}", f"_{target_height}p{source.suffix}")),
                target_height,
                "fast",
                23,
                True,  # keep_original for batch
            ): source
            for source, _, _ in jobs
        }
        
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                source_path, success, error = future.result()
                if success:
                    stats["transcoded"] += 1
                    logger.info(f"Transcoded: {source_path.name}")
                else:
                    stats["failed"] += 1
                    logger.error(f"Failed {source_path.name}: {error}")
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"Exception for {source}: {e}")
    
    stats["skipped"] = stats["total"] - stats["transcoded"] - stats["failed"]
    return stats