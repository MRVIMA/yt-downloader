"""Small helpers shared by the CLI and GUI."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from yt_downloader import APP_SLUG

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_URL_RE = re.compile(r"https?://\S+")


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def has_js_runtime() -> bool:
    """yt-dlp needs a JavaScript runtime (Deno preferred) for full YouTube support."""
    return any(shutil.which(name) for name in ("deno", "node", "bun", "qjs"))


def default_download_dir() -> Path:
    xdg = _xdg_user_dir("DOWNLOAD")
    return (xdg or Path.home() / "Downloads") / "YT Downloader"


def state_dir() -> Path:
    """Where logs go: %LOCALAPPDATA% on Windows, $XDG_STATE_HOME elsewhere."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return Path(base) / "YT Downloader" / "logs"
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(base) / APP_SLUG


def use_bundled_tools() -> None:
    """Put ffmpeg/deno shipped next to a frozen (PyInstaller) build first on PATH.

    The Windows installer places them in a ``bin`` folder beside the executable.
    """
    if not getattr(sys, "frozen", False):
        return
    candidates = [Path(sys.executable).parent / "bin"]
    if meipass := getattr(sys, "_MEIPASS", None):
        candidates.append(Path(meipass) / "bin")
    for folder in candidates:
        if folder.is_dir():
            os.environ["PATH"] = f"{folder}{os.pathsep}{os.environ.get('PATH', '')}"


def _xdg_user_dir(name: str) -> Path | None:
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    try:
        text = (config / "user-dirs.dirs").read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(rf'^XDG_{name}_DIR="([^"]+)"', text, re.MULTILINE)
    if not match:
        return None
    return Path(match.group(1).replace("$HOME", str(Path.home())))


def extract_urls(text: str) -> list[str]:
    """Pull every http(s) URL out of free text, preserving order and dropping duplicates."""
    seen: dict[str, None] = {}
    for url in _URL_RE.findall(text):
        seen.setdefault(url.rstrip(".,;)]>'\""), None)
    return list(seen)


def clean_error(message: str) -> str:
    """Turn a yt-dlp error string into something readable in a UI."""
    message = _ANSI_RE.sub("", message).strip()
    message = re.sub(r"^ERROR:\s*", "", message)
    message = re.sub(r"^\[[\w:]+\]\s*[\w-]+:\s*", "", message)
    return message.splitlines()[0] if message else "Unknown error"


def format_bytes(num: float | None) -> str:
    if num is None:
        return "?"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(num) < 1024:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TiB"


def format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"
