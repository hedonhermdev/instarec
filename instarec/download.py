"""Download Instagram reels via yt-dlp."""

import os
from typing import Any

from yt_dlp import YoutubeDL


def download_reel(
    url: str,
    output_dir: str = ".",
    cookies_file: str = "cookies.txt",
) -> dict[str, Any]:
    """Download an Instagram reel and return its metadata.

    Args:
        url: Instagram reel URL.
        output_dir: Directory to save the video into.
        cookies_file: Path to yt-dlp cookies file for authentication.

    Returns:
        Dict with keys ``video_path`` (str), ``caption`` (str), and ``id`` (str).
    """
    os.makedirs(output_dir, exist_ok=True)
    video_template = os.path.join(output_dir, "video.%(ext)s")

    ydl_opts: dict[str, Any] = {
        "cookies": cookies_file,
        "outtmpl": video_template,
        "format": "best",
        "postprocessors": [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if info is None:
        raise RuntimeError(f"yt-dlp returned no info for {url}")

    video_path = os.path.join(output_dir, "video.mp4")
    caption = info.get("description") or ""
    reel_id = info.get("id") or ""

    return {"video_path": video_path, "caption": caption, "id": reel_id}
