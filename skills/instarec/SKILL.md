---
name: instarec
description: Extract media recommendations (music, videos, books, articles) from Instagram Reels. Use this skill when the user asks to extract, identify, or find media recommendations from an Instagram Reel. This includes requests like "what song is in this reel", "extract recommendations from this reel", "what media is shown in this Instagram post", or any task involving analyzing Instagram Reel content for embedded media references.
---

# Skill: instarec

Extract media recommendations (music, videos, books, articles) from Instagram Reels.

## Prerequisites

The tool requires the following to be set up before use:

| Requirement | How to verify | How to fix |
|-------------|---------------|------------|
| Python 3.12+ | `python3 --version` | Install via `pyenv` or system package manager |
| `uv` package manager | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ffmpeg` | `ffmpeg -version` | `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux) |
| Dependencies installed | `uv sync` in project root | Run `uv sync` |
| `GEMINI_API_KEY` in `.env` | Check `.env` file exists with key | Create `.env` with `GEMINI_API_KEY=<key>` |
| `cookies.txt` | File exists in project root | Export Instagram cookies using a browser extension (Netscape format) |

## Usage

### Basic command

```bash
uv run main.py <instagram_reel_url>
```

### All options

```bash
uv run main.py <url> [--cookies <path>] [--model <model>] [--scene-threshold <float>] [--keep-files]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `url` | positional, required | -- | Instagram Reel URL (e.g. `https://www.instagram.com/reel/ABC123/`) |
| `--cookies` | string | `cookies.txt` | Path to yt-dlp Netscape-format cookies file for Instagram authentication |
| `--model` | string | `gemini-2.5-flash-lite` | Google Gemini model to use for frame analysis |
| `--scene-threshold` | float | `0.05` | FFmpeg scene-change sensitivity (0-1). Lower = more frames extracted. Raise to 0.2-0.4 if too many duplicate frames are returned |
| `--keep-files` | flag | off | Retain downloaded video and extracted frames in `data/<reel_id>/` instead of cleaning up |

### Working directory

All commands MUST be run from the project root: `/Users/tirthjain/src/instarec`

## Output format

The CLI writes structured JSON to **stdout** and status/progress messages to **stderr**.

### JSON schema

```json
{
  "url": "https://www.instagram.com/reel/...",
  "caption": "Original reel caption text",
  "media": [
    {
      "media": {
        "type": "music | video | article | book",
        "platform": "spotify | youtube | apple_music | ...",
        "title": "Song or media title",
        "creator": "Artist, author, or channel name",
        "confidence": 0.95
      }
    }
  ]
}
```

### Field details

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | The input Instagram Reel URL |
| `caption` | string | The reel's caption/description text (may be empty) |
| `media` | array | List of detected media items. Empty array `[]` if nothing found |
| `media[].media.type` | string | One of: `music`, `video`, `article`, `book` |
| `media[].media.platform` | string or null | Platform identifier (e.g. `spotify`, `youtube`, `apple_music`) |
| `media[].media.title` | string or null | Title of the media |
| `media[].media.creator` | string or null | Artist, author, or channel name |
| `media[].media.confidence` | number or null | Model confidence score from 0 to 1 |

### Capturing output

Since JSON goes to stdout and status messages go to stderr, capture the JSON like this:

```bash
# Save JSON to file
uv run main.py <url> > output.json

# Parse with jq
uv run main.py <url> 2>/dev/null | jq '.media'

# Store in a variable
result=$(uv run main.py <url> 2>/dev/null)
```

## Pipeline stages

The CLI runs a three-stage pipeline:

1. **Download** -- Downloads the Instagram Reel video via `yt-dlp` (requires valid `cookies.txt` for authentication). Output: MP4 video file.
2. **Frame extraction** -- Uses `ffmpeg` scene-change detection to extract visually distinct keyframes. Output: JPEG frames.
3. **VLM analysis** -- Sends each frame to Google Gemini to detect embedded media cards (Spotify players, YouTube embeds, book covers, etc.). Output: structured JSON per frame.

## Examples

### Extract recommendations from a reel

```bash
uv run main.py "https://www.instagram.com/reel/DUacLRYktcd/"
```

### Keep intermediate files for inspection

```bash
uv run main.py "https://www.instagram.com/reel/DUacLRYktcd/" --keep-files
# Video saved to: data/DUacLRYktcd/video.mp4
# Frames saved to: data/DUacLRYktcd/frames/
```

### Use a more capable model for difficult reels

```bash
uv run main.py "https://www.instagram.com/reel/DUacLRYktcd/" --model gemini-2.5-flash-preview-05-20
```

### Reduce frame count for long reels

```bash
uv run main.py "https://www.instagram.com/reel/DUacLRYktcd/" --scene-threshold 0.3
```

### Process multiple reels

```bash
for url in \
  "https://www.instagram.com/reel/ABC123/" \
  "https://www.instagram.com/reel/DEF456/"; do
  uv run main.py "$url" 2>/dev/null
done
```

## Error handling

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `RuntimeError: GEMINI_API_KEY not set` | Missing API key | Add `GEMINI_API_KEY=...` to `.env` |
| `RuntimeError: yt-dlp returned no info` | Invalid URL or expired cookies | Verify URL is a valid Instagram Reel; re-export `cookies.txt` |
| `ffmpeg` errors / no frames extracted | `ffmpeg` not installed or corrupt video | Install ffmpeg; try a different reel |
| Empty `media` array | No embedded media detected in reel | Reel may not contain media cards; try lowering `--scene-threshold` or using a stronger `--model` |
| HTTP 401/403 from Instagram | Expired or invalid cookies | Re-export cookies from a logged-in browser session |

## Limitations

- Only works with Instagram Reels (not Stories, Posts, or other platforms)
- Requires valid Instagram session cookies (`cookies.txt`) for downloading
- Frame analysis is per-frame and sequential -- long reels with many scene changes will be slower
- VLM analysis depends on visual clarity; blurry or partially visible media cards may not be detected
- The `confidence` score is the model's self-reported confidence, not a calibrated probability
