import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Central configuration — all values from environment variables."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "AllLinkDownloadBot")
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "raj169k")

    # Deployment mode: "polling" or "webhook"
    MODE: str = os.getenv("MODE", "polling").lower()

    # Webhook settings (used only when MODE == "webhook")
    RENDER_EXTERNAL_URL: Optional[str] = os.getenv("RENDER_EXTERNAL_URL")
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    PORT: int = int(os.getenv("PORT", "8080"))

    # Download / conversion directories
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
    CONVERTED_DIR: str = os.getenv("CONVERTED_DIR", "converted")

    # Max file size Telegram allows (50 MB — safety margin)
    MAX_FILE_SIZE: int = 45 * 1024 * 1024

    # Supported platforms for inline buttons
    PLATFORMS: dict = field(default_factory=lambda: {
        "dailymotion": {"label": "📺 Dailymotion", "emoji": "📺"},
        "vimeo":       {"label": "🎬 Vimeo",       "emoji": "🎬"},
        "vk":          {"label": "🌐 VK",           "emoji": "🌐"},
        "tiktok":      {"label": "🎵 TikTok",       "emoji": "🎵"},
        "reddit":      {"label": "👽 Reddit",       "emoji": "👽"},
        "threads":     {"label": "🧵 Threads",      "emoji": "🧵"},
        "xiaohongshu": {"label": "📕 Xiaohongshu",  "emoji": "📕"},
    })

    # Media conversion options
    CONVERSIONS: dict = field(default_factory=lambda: {
        "mp3":      {"label": "🎵 MP3 Converter",      "from": None,           "to": "mp3"},
        "mp4":      {"label": "🎥 MP4 Converter",      "from": None,           "to": "mp4"},
        "mp4_to_mp3": {"label": "🔄 MP4 → MP3",        "from": "mp4",          "to": "mp3"},
        "mov":      {"label": "🎞️ MOV",                "from": None,           "to": "mov"},
        "mov_to_mp4": {"label": "🔄 MOV → MP4",        "from": "mov",          "to": "mp4"},
        "gif":      {"label": "🎨 GIF",                "from": None,           "to": "gif"},
        "mp4_to_gif": {"label": "🔄 MP4 → GIF",        "from": "mp4",          "to": "gif"},
        "mkv":      {"label": "📦 MKV",                "from": None,           "to": "mkv"},
        "mkv_to_mp4": {"label": "🔄 MKV → MP4",        "from": "mkv",          "to": "mp4"},
        "webm_to_mp4": {"label": "🌍 WEBM → MP4",      "from": "webm",         "to": "mp4"},
    })

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required!")
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.CONVERTED_DIR, exist_ok=True)


# Global singleton
config = Config()
