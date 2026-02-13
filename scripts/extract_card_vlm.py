#!/usr/bin/env python3
"""Analyze a single frame for embedded media using Google Gemini VLM.

Standalone script for debugging -- the main pipeline uses instarec/analyze.py instead.
"""

import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = """\
You are analyzing a short-form social video frame.
In ONE pass, determine whether the frame contains any embedded or referenced media
(e.g., music players, video players, app cards, screenshots).

If yes, extract:
- media type (music, video, article, app)
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


def analyze_frame(image_path: str, model: str = DEFAULT_MODEL) -> dict:
    """Send a single frame to the Gemini VLM and print the result.

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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_card_vlm.py <image_path> [--model MODEL]")
        sys.exit(1)

    path = sys.argv[1]
    model = DEFAULT_MODEL

    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    if not os.path.exists(path):
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_frame(path, model=model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
