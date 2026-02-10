# instarec

CLI tool that extracts media recommendations from Instagram Reels.

Given a reel URL, it downloads the video, extracts unique frames via scene detection and perceptual hashing, then sends each frame to a Vision Language Model to identify embedded media (Spotify tracks, YouTube videos, etc.). Results are output as JSON.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- `ffmpeg` installed and on PATH
- An [OpenRouter](https://openrouter.ai/) API key

## Setup

```bash
uv sync
```

Create a `.env` file with your API key:

```
OPENROUTER_API_KEY=sk-or-...
```

For Instagram authentication, place a Netscape-format `cookies.txt` in the project root (see [yt-dlp docs](https://github.com/yt-dlp/yt-dlp#filesystem-options) on cookie extraction).

## Usage

```bash
# Run the full pipeline (outputs JSON to stdout)
uv run main.py https://www.instagram.com/reel/XXXX/

# Keep downloaded video and extracted frames in the current directory
uv run main.py https://www.instagram.com/reel/XXXX/ --keep-files

# Use a different VLM
uv run main.py https://www.instagram.com/reel/XXXX/ --model google/gemini-2.0-flash-001

# Pipe results through jq
uv run main.py https://www.instagram.com/reel/XXXX/ | jq '.media[].media.title'
```

Status messages go to stderr, JSON goes to stdout, so output is always pipeable.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--cookies` | `cookies.txt` | Path to yt-dlp cookies file |
| `--model` | `meta-llama/llama-4-maverick` | OpenRouter model for frame analysis |
| `--scene-threshold` | `0.3` | FFmpeg scene-change sensitivity (0-1, lower = more frames) |
| `--hash-threshold` | `10` | Perceptual hash distance for dedup |
| `--keep-files` | off | Keep downloaded video and extracted frames |

### Output format

```json
{
  "url": "https://www.instagram.com/reel/XXXX/",
  "caption": "Check out this song!",
  "media": [
    {
      "has_embedded_media": true,
      "media": {
        "type": "music",
        "platform": "spotify",
        "title": "Song Name",
        "creator": "Artist Name",
        "confidence": 0.95
      },
      "intent": "recommendation",
      "frame": "frames/frame_0003.jpg"
    }
  ]
}
```

## Pipeline

1. **Download** (`instarec/download.py`) -- downloads the reel via yt-dlp, remuxes to MP4, extracts the caption
2. **Extract frames** (`instarec/frames.py`) -- runs ffmpeg scene-change detection, then deduplicates with perceptual hashing (pHash)
3. **Analyze** (`instarec/analyze.py`) -- sends each unique frame to a VLM via OpenRouter, parses the structured JSON response

## Standalone scripts

The `scripts/` directory contains the original standalone versions of each pipeline stage, useful for debugging individual steps:

```bash
# Extract frames from an existing video
uv run scripts/extract_frames.py video.mp4 --output frames/

# Detect embedded cards via OpenCV (no API needed)
uv run scripts/extract_card.py frames/frame_0001.jpg

# Analyze a single frame via VLM
uv run scripts/extract_card_vlm.py frames/frame_0001.jpg
```

## Project structure

```
main.py                      # CLI entry point: runs the full pipeline
instarec/
  __init__.py
  download.py                # Stage 1: download reel via yt-dlp
  frames.py                  # Stage 2: scene detection + perceptual hash dedup
  analyze.py                 # Stage 3: VLM frame analysis via OpenRouter
scripts/
  extract_frames.py          # Standalone frame extraction
  extract_card.py            # Standalone CV-based card detection (OpenCV MSER)
  extract_card_vlm.py        # Standalone VLM-based card extraction
```
