"""Download Orchestration Module using N_m3u8DL-RE"""

import asyncio
import subprocess
import os
import shutil
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadResult:
    success: bool
    output_file: Optional[str] = None
    error: Optional[str] = None


class Downloader:
    def __init__(self, output_dir: str = "media", resolution: int = 1080):
        self.output_dir = Path(output_dir)
        self.resolution = resolution
        self.n_m3u8dl_path = self._find_n_m3u8dl()

    def _find_n_m3u8dl(self) -> Optional[str]:
        for name in ["N_m3u8DL-RE", "n_m3u8dl-re", "N_m3u8DL-RE.exe"]:
            path = shutil.which(name)
            if path:
                return path

        common_paths = [
            Path.home() / ".local" / "bin" / "N_m3u8DL-RE",
            Path("/usr/local/bin/N_m3u8DL-RE"),
            Path("/usr/bin/N_m3u8DL-RE"),
            Path("C:/Program Files/N_m3u8DL-RE/N_m3u8DL-RE.exe"),
            Path.cwd() / "tools" / "N_m3u8DL-RE",
        ]

        for path in common_paths:
            if path.exists():
                return str(path)

        return None

    def check_dependencies(self) -> bool:
        has_n_m3u8dl = self.n_m3u8dl_path is not None
        has_ffmpeg = shutil.which("ffmpeg") is not None

        if not has_n_m3u8dl:
            print("N_m3u8DL-RE not found. Please install it from:")
            print("https://github.com/nilaoda/N_m3u8DL-RE/releases")

        if not has_ffmpeg:
            print("FFmpeg not found. Please install FFmpeg.")

        return has_n_m3u8dl and has_ffmpeg

    async def download(
        self,
        mpd_url: str,
        output_filename: str,
        keys: Optional[List[str]] = None,
        license_url: Optional[str] = None,
        license_headers: Optional[dict] = None,
    ) -> DownloadResult:
        if not self.n_m3u8dl_path:
            return DownloadResult(success=False, error="N_m3u8DL-RE not found")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        output_path = self.output_dir / output_filename

        cmd = [
            self.n_m3u8dl_path,
            mpd_url,
            "--save-dir",
            str(self.output_dir),
            "--save-name",
            output_filename,
            "-M",
            "format=mp4",
        ]

        if keys:
            for key in keys:
                cmd.extend(["--key", key])

        if license_url:
            cmd.extend(["--license-url", license_url])

        if license_headers:
            for key, value in license_headers.items():
                cmd.extend(["--header", f"{key}: {value}"])

        try:
            print(f"Running: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return DownloadResult(
                    success=True, output_file=str(output_path) + ".mp4"
                )
            else:
                return DownloadResult(
                    success=False, error=stderr.decode() if stderr else "Unknown error"
                )

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    async def download_with_manual_keys(
        self, mpd_url: str, output_filename: str, kid: str, key: str
    ) -> DownloadResult:
        key_string = f"{kid}:{key}"
        return await self.download(mpd_url, output_filename, keys=[key_string])

    def generate_filename_from_url(self, url: str) -> str:
        parts = url.split("/")
        for part in reversed(parts):
            if part and not part.startswith("http"):
                name = part.split("?")[0]
                name = name.replace(".ism", "").replace(".mpd", "")
                return name or "video"
        return "video"
