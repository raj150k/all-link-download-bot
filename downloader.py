import os
import asyncio
import re
from pathlib import Path
from typing import Optional, Tuple

import yt_dlp
from yt_dlp.utils import DownloadError

from config import config


# ── Platform detection ──────────────────────────────────────────────────

PLATFORM_PATTERNS: dict[str, re.Pattern] = {
    "dailymotion": re.compile(r"(?:www\.)?dailymotion\.com/video/", re.I),
    "vimeo":       re.compile(r"(?:www\.)?vimeo\.com/\d+", re.I),
    "vk":          re.compile(r"(?:www\.)?vk\.com/video", re.I),
    "tiktok":      re.compile(r"(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)/", re.I),
    "reddit":      re.compile(r"(?:www\.)?reddit\.com/r/", re.I),
    "threads":     re.compile(r"(?:www\.)?threads\.net/", re.I),
    "xiaohongshu": re.compile(r"(?:www\.)?xhslink\.com|xiaohongshu\.com", re.I),
}


def detect_platform(url: str) -> Optional[str]:
    """Return platform key if URL matches a known pattern."""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return platform
    return None


# ── yt-dlp helpers ─────────────────────────────────────────────────────

def _progress_hook(d: dict):
    """Optional: log download progress (can be extended for Telegram updates)."""
    if d["status"] == "finished":
        print(f"✅ Download finished: {d['filename']}")


def _build_ydl_opts(format_spec: str = "bestvideo+bestaudio/best") -> dict:
    return {
        "format": format_spec,
        "outtmpl": os.path.join(config.DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
        "merge_output_format": "mp4",
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }


async def download_media(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download media from *url*.
    Returns (file_path, error_message).
    On success error_message is None; on failure file_path is None.
    """
    loop = asyncio.get_event_loop()
    opts = _build_ydl_opts()

    def _sync_dl() -> Optional[str]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                # yt-dlp's outtmpl with post-processing may change extension
                # We glob for the file id
                file_id = info.get("id")
                ext = info.get("ext", "mp4")
                # Try common extensions
                for candidate_ext in (ext, "mp4", "webm", "mkv", "mov"):
                    candidate = os.path.join(config.DOWNLOAD_DIR, f"{file_id}.{candidate_ext}")
                    if os.path.isfile(candidate):
                        return candidate
                # Fallback: walk the download dir
                for f in Path(config.DOWNLOAD_DIR).iterdir():
                    if f.is_file() and file_id in f.name:
                        return str(f)
                return None
            except DownloadError as e:
                raise e

    try:
        file_path = await loop.run_in_executor(None, _sync_dl)
        if file_path and os.path.isfile(file_path):
            return file_path, None
        return None, "❌ Could not locate the downloaded file."
    except DownloadError as e:
        return None, f"❌ Download failed: {e.msg}"
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"


async def get_file_size(file_path: str) -> int:
    """Return file size in bytes."""
    return os.path.getsize(file_path)


def clean_up(file_path: str):
    """Remove a downloaded / converted file."""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except OSError:
        pass
