import os
import sys
import subprocess
import requests
import platform
import shutil
from .config import BASE_DIR, log



def _yt_dlp_name() -> str:
    """Return the platform‑specific yt‑dlp binary name."""
    system = platform.system().lower()
    if system.startswith("win"):
        return "yt-dlp.exe"
    return "yt-dlp"

def _yt_dlp_path() -> str:
    """Absolute path to the yt‑dlp binary inside the project.

    The binary is stored under ``BASE_DIR / 'bin'``.
    """
    return os.path.join(BASE_DIR, "bin", _yt_dlp_name())

def _download_url() -> str:
    """Construct the download URL for the latest yt‑dlp release.

    Mirrors the logic from the original ``poc.py`` script.
    """
    base = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
    return f"{base}{_yt_dlp_name()}"

# Public API

def find_yt_dlp() -> list:
    """Locate the yt‑dlp binary, downloading it if necessary.

    Returns a list containing the absolute path to the binary.
    """
    candidates = []
    path = shutil.which(_yt_dlp_name())
    if path:
        candidates.append(path)
    bundled = _yt_dlp_path()
    candidates.append(bundled)
    if hasattr(sys, 'executable'):
        venv_bin = os.path.join(os.path.dirname(sys.executable), _yt_dlp_name())
        candidates.append(venv_bin)
    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            proc = subprocess.Popen(
                [candidate, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, _ = proc.communicate(timeout=5)
            version = stdout.strip()
            if version >= "2026.06.09":
                return [candidate]
        except Exception:
            continue
    url = _download_url()
    os.makedirs(os.path.dirname(bundled), exist_ok=True)
    log.info(f"Downloading yt‑dlp from {url} to {bundled}")
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        with open(bundled, "wb") as f:
            if hasattr(resp, "iter_content"):
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            else:
                f.write(resp.content)
        if not platform.system().lower().startswith("win"):
            os.chmod(bundled, 0o755)
        return [bundled]
    except Exception as exc:
        raise RuntimeError(f"Kan yt‑dlp niet downloaden van {url}: {exc}") from exc

def download_with_yt_dlp(
    url: str,
    output_path: str = "%(title)s.%(ext)s",
    simulate: bool = False,
    quality: int | str | None = None,
    cookies: str | None = None,
    timeout: int | None = None,
) -> bool:
    """Run yt‑dlp with the supplied parameters.

    Parameters
    ----------
    url: URL of the media to download.
    output_path: yt‑dlp ``-o`` output template (default: ``%(title)s.%(ext)s``).
    simulate: If ``True``, add ``--simulate`` to perform a dry‑run.
    quality: ``int`` or ``str`` representing the desired format quality (e.g., ``22`` or ``best``). If ``None`` the default yt‑dlp format is used.
    cookies: Optional cookie header string, passed via ``--cookies``.
    timeout: Optional timeout in seconds for the yt‑dlp subprocess.

    Returns
    -------
    bool
        ``True`` on success, ``False`` on failure.
    """
    yt_dlp_path = find_yt_dlp()[0]
    cmd = [yt_dlp_path]
    cmd += ["-f", str(quality) if quality is not None else "best"]
    if simulate:
        cmd.append("--simulate")
    if cookies:
        cmd += ["--cookies", cookies]
    cmd += ["-o", output_path]
    cmd.append(url)
    log.debug(f"Executing yt‑dlp command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
        return result.returncode == 0
    except Exception as exc:
        return False
