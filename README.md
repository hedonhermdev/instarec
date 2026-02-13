# instarec

CLI tool that extracts media recommendations from Instagram Reels.

Given a reel URL, it downloads the video, extracts unique frames via FFmpeg scene-change detection, then sends each frame to a Vision Language Model to identify embedded media (Spotify tracks, YouTube videos, etc.). Results are output as JSON.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- `ffmpeg` installed and on PATH
- A [Google Gemini](https://ai.google.dev/) API key

## Setup

```bash
uv sync
```

Create a `.env` file with your API key:

```
GEMINI_API_KEY=your-api-key
```

For Instagram authentication, place a Netscape-format `cookies.txt` in the project root (see [yt-dlp docs](https://github.com/yt-dlp/yt-dlp#filesystem-options) on cookie extraction).

## Usage

```bash
# Run the full pipeline (outputs JSON to stdout)
uv run main.py https://www.instagram.com/reel/XXXX/

# Or use the installed entry point
uv run instarec https://www.instagram.com/reel/XXXX/

# Keep downloaded video and extracted frames in data/<reel_id>/
uv run main.py https://www.instagram.com/reel/XXXX/ --keep-files

# Use a different VLM model
uv run main.py https://www.instagram.com/reel/XXXX/ --model gemini-2.5-flash

# Pipe results through jq
uv run main.py https://www.instagram.com/reel/XXXX/ | jq '.media[].media.title'
```

Status messages go to stderr, JSON goes to stdout, so output is always pipeable.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--cookies` | `cookies.txt` | Path to yt-dlp cookies file |
| `--model` | `gemini-2.5-flash-lite` | Gemini model for frame analysis |
| `--scene-threshold` | `0.05` | FFmpeg scene-change sensitivity (0-1, lower = more frames) |
| `--keep-files` | off | Keep downloaded video and extracted frames in `data/<reel_id>/` |

### Output format

```json
{
  "url": "https://www.instagram.com/reel/XXXX/",
  "caption": "Check out this song!",
  "media": [
    {
      "media": {
        "type": "music",
        "platform": "spotify",
        "title": "Song Name",
        "creator": "Artist Name",
        "confidence": 0.95
      }
    }
  ]
}
```

## Pipeline

1. **Download** (`instarec/download.py`) -- downloads the reel via yt-dlp, remuxes to MP4, extracts the caption
2. **Extract frames** (`instarec/frames.py`) -- runs FFmpeg scene-change detection to extract unique frames
3. **Analyze** (`instarec/analyze.py`) -- sends each unique frame to a VLM via Google Gemini, parses the structured JSON response

## Standalone scripts

The `scripts/` directory contains the original standalone versions of each pipeline stage, useful for debugging individual steps:

```bash
# Extract frames from an existing video
uv run scripts/extract_frames.py video.mp4 --output frames/

# Detect embedded cards via OpenCV (no API needed)
uv run scripts/extract_card.py frames/frame_0001.jpg

# Analyze a single frame via VLM (requires GEMINI_API_KEY in .env)
uv run scripts/extract_card_vlm.py frames/frame_0001.jpg
```

## Project structure

```
main.py                      # CLI entry point: runs the full pipeline
instarec/                    # Library package
  __init__.py
  download.py                # Stage 1: download reel via yt-dlp
  frames.py                  # Stage 2: scene-change frame extraction
  analyze.py                 # Stage 3: VLM frame analysis via Google Gemini
scripts/                     # Standalone scripts (for debugging individual stages)
  extract_frames.py          # Scene detection + perceptual hash dedup
  extract_card.py            # CV-based card detection (OpenCV MSER)
  extract_card_vlm.py        # VLM-based card extraction
skills/                      # AI agent skill definitions
  instarec/SKILL.md
pyproject.toml               # Project metadata & dependencies
```
