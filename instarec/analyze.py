"""Analyze video frames for embedded media using a Vision Language Model."""

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from tqdm import tqdm

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = """\
You are analyzing an image frame. This image may or may not contain an embedded card.
In ONE pass, determine whether the frame contains any embedded or referenced media
(e.g., music players, video players, books, etc).

If yes, extract:
- media type (music, video, article, book)
- platform (spotify, youtube, apple_music, etc.)
- title
- creator/artist/channel
- confidence (0-1)

If no, return null for the media field.

Respond ONLY as valid JSON matching this schema:
"media": {
    "type": string | null,
    "platform": string | null,
    "title": string | null,
    "creator": string | null,
    "confidence": number | null
} | null
"""


def _get_client() -> genai.Client:
    """Return a configured Gemini client or raise."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
    return genai.Client(api_key=key)


def _load_image_bytes(path: str) -> bytes:
    """Read an image file and return its raw bytes."""
    with open(path, "rb") as f:
        return f.read()


def analyze_frame(image_path: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Send a single frame to the VLM and return parsed JSON.

    Args:
        image_path: Path to a JPEG/PNG frame on disk.
        model: Gemini model identifier.

    Returns:
        Parsed JSON dict with a ``media`` key (object or null).
    """
    client = _get_client()
    image_data = _load_image_bytes(image_path)
    image_part = types.Part.from_bytes(data=image_data, mime_type="image/jpeg")

    response = client.models.generate_content(
        model=model,
        contents=[SYSTEM_PROMPT, image_part],
    )

    raw = response.text or ""

    # Strip markdown code fences if the model wraps its response
    text = raw.strip()
    if text.startswith("```"):
        # Remove opening ```json or ``` and closing ```
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return {"media": None}
        if "media" not in parsed:
            return {"media": None}
        return parsed
    except (json.JSONDecodeError, ValueError):
        return {
            "media": None,
            "_raw": raw,
            "_error": "Failed to parse VLM response as JSON",
        }


def analyze_frames(
    frame_paths: list[str], model: str = DEFAULT_MODEL
) -> list[dict[str, Any]]:
    """Analyze multiple frames and return results for those with embedded media.

    Args:
        frame_paths: List of paths to frame images.
        model: Gemini model identifier.

    Returns:
        List of result dicts (one per frame that contains embedded media).
    """
    results: list[dict[str, Any]] = []

    for path in tqdm(
        frame_paths, desc="Analyzing frames", unit="frame", file=sys.stderr
    ):
        result: dict[str, Any] = analyze_frame(path, model=model) or {"media": None}
        if result.get("media"):
            results.append(result)

    return results
