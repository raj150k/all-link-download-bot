import os
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from config import config


# ── FFmpeg conversion map ──────────────────────────────────────────────

FFMPEG_CMD_TEMPLATES: dict[str, list[str]] = {
    "mp3":        ["ffmpeg", "-i", "{input}", "-vn", "-acodec", "libmp3lame", "-q:a", "2", "{output}"],
    "mp4":        ["ffmpeg", "-i", "{input}", "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "{output}"],
    "mov":        ["ffmpeg", "-i", "{input}", "-c:v", "prores_ks", "-profile:v", "3", "-c:a", "pcm_s16le", "{output}"],
    "gif":        ["ffmpeg", "-i", "{input}", "-vf", "fps=10,scale=480:-1:flags=lanczos", "-c:v", "gif", "{output}"],
    "mkv":        ["ffmpeg", "-i", "{input}", "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "{output}"],
    "webm_to_mp4":["ffmpeg", "-i", "{input}", "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "{output}"],
}


async def convert_media(input_path: str, target_format: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Convert *input_path* to *target_format*.
    Returns (output_path, error_message).
    """
    stem = Path(input_path).stem
    output_filename = f"{stem}_converted.{target_format}"
    output_path = os.path.join(config.CONVERTED_DIR, output_filename)

    # Pick the right FFmpeg template
    conversion_key = target_format
    # For conversions like mp4_to_mp3, derive key from source extension and target
    src_ext = Path(input_path).suffix.lstrip(".").lower()
    if src_ext != target_format:
        compound_key = f"{src_ext}_to_{target_format}"
        if compound_key in FFMPEG_CMD_TEMPLATES:
            conversion_key = compound_key

    cmd_template = FFMPEG_CMD_TEMPLATES.get(conversion_key)
    if cmd_template is None:
        # Fallback: try format name directly
        cmd_template = FFMPEG_CMD_TEMPLATES.get(target_format)
    if cmd_template is None:
        return None, f"❌ No conversion template for format `{target_format}`."

    # Build command
    cmd = [part.replace("{input}", input_path).replace("{output}", output_path) for part in cmd_template]

    try:
        loop = asyncio.get_event_loop()

        def _run_ffmpeg() -> bool:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "FFmpeg returned non-zero exit code.")
            return os.path.isfile(output_path)

        success = await loop.run_in_executor(None, _run_ffmpeg)
        if success:
            return output_path, None
        return None, "❌ Conversion produced no output file."
    except Exception as e:
        return None, f"❌ Conversion failed: {str(e)}"


async def get_file_size(file_path: str) -> int:
    """Return file size in bytes."""
    return os.path.getsize(file_path)


def clean_up(file_path: str):
    """Remove a converted file."""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except OSError:
        pass
