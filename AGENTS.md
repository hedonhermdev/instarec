# AGENTS.md — instarec

## Project Overview

Python CLI tool that extracts media recommendations from Instagram Reels.
Pipeline: download reel (yt-dlp) -> extract unique frames (ffmpeg scene detection) -> VLM analysis (Google Gemini API) -> JSON output.

- **Language:** Python 3.12+ (see `requires-python` in `pyproject.toml`)
- **Package manager:** [uv](https://docs.astral.sh/uv/)
- **External tools required:** `ffmpeg` (invoked via subprocess in `instarec/frames.py`)

## Project Structure

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
.env                         # API keys (GEMINI_API_KEY) — NEVER commit
cookies.txt                  # yt-dlp auth cookies — NEVER commit
```

## Build & Run Commands

### Setup
```bash
uv sync                     # Install all dependencies into .venv
```

### Running the CLI
```bash
# Full pipeline: download -> extract frames -> VLM analysis -> JSON to stdout
uv run main.py <instagram_reel_url>

# Or use the installed entry point
uv run instarec <instagram_reel_url>

# Keep intermediate files in data/<reel_id>/ directory
uv run main.py <instagram_reel_url> --keep-files

# Use a different VLM model
uv run main.py <url> --model gemini-2.5-flash

# Adjust frame extraction sensitivity (default: 0.05)
uv run main.py <url> --scene-threshold 0.1
```

### Running Standalone Scripts
```bash
uv run scripts/extract_frames.py video.mp4 --output frames/
uv run scripts/extract_card.py frames/frame_0001.jpg
uv run scripts/extract_card_vlm.py frames/frame_0001.jpg
```

### Adding Dependencies
```bash
uv add <package>             # Add a runtime dependency
uv add --dev <package>       # Add a dev dependency
```

## Linting & Formatting

Ruff is used with default settings (no custom config in pyproject.toml).

```bash
uv run ruff check .          # Lint all files
uv run ruff check --fix .    # Lint and auto-fix
uv run ruff format .         # Format all files
uv run ruff format --check . # Check formatting without modifying
```

## Testing

No test framework is currently configured.

When tests are added, use pytest:
```bash
uv add --dev pytest
uv run pytest                        # Run all tests
uv run pytest tests/test_foo.py      # Run a single test file
uv run pytest tests/test_foo.py::test_bar  # Run a single test function
uv run pytest -x                     # Stop on first failure
uv run pytest -k "keyword"           # Run tests matching keyword
```

Place test files in a `tests/` directory with `test_` prefix.

## Code Style Guidelines

### Formatting
- Formatter: **ruff format** (Black-compatible defaults)
- Line length: 88 characters (ruff/Black default)
- Indentation: 4 spaces
- Quotes: double quotes for strings (`"..."`)
- Trailing commas: yes, in multi-line structures

### Imports
- Standard library first, then third-party, then local — separated by blank lines
- One import per line for `from` imports when there are multiple names
- No wildcard imports (`from x import *`)
- Example:
  ```python
  import json
  import os
  import sys
  from typing import Any

  from dotenv import load_dotenv
  from google import genai

  from instarec.download import download_reel
  ```

### Naming Conventions
- **Functions/variables:** `snake_case` (e.g., `extract_unique_frames`, `frame_paths`)
- **Module-level constants:** `UPPER_SNAKE_CASE` (e.g., `API_URL`, `DEFAULT_MODEL`, `SYSTEM_PROMPT`)
- **Private helpers:** leading underscore (e.g., `_get_client`, `_load_image_bytes`, `_run_pipeline`)
- **Files/modules:** `snake_case.py`
- **Classes:** `PascalCase` (none currently exist, follow PEP 8 if adding)

### Type Annotations
- All function signatures must have parameter and return type annotations
- Use `dict[str, Any]`, `list[str]` (lowercase generics, Python 3.12+)
- Example:
  ```python
  def download_reel(url: str, output_dir: str = ".") -> dict[str, Any]:
  ```

### Error Handling
- Library code: raise specific exceptions (`RuntimeError`, `FileNotFoundError`, `ValueError`)
- CLI code: use `sys.exit(1)` for argument validation failures
- Status/progress messages to stderr: `print("msg", file=sys.stderr)`
- Validate inputs early with guard clauses

### CLI Patterns
- `main.py` uses `argparse` and a `main()` function called via `if __name__ == "__main__": main()`
- Status messages go to stderr (via `log()`), structured output goes to stdout as JSON
- CLI output conventions: `[*]` for progress, `[+]` for success, `[-]` for failure

### Module Patterns
- Each module in `instarec/` has a single responsibility
- Public API is one or two functions per module (e.g., `download_reel`, `extract_unique_frames`, `analyze_frames`)
- Internal helpers are prefixed with underscore
- Docstrings on all public functions (Google-style with Args/Returns sections)

### Environment & Secrets
- Load API keys from `.env` using `dotenv`: `load_dotenv()` then `os.environ.get(...)`
- **NEVER** hardcode API keys or secrets
- **NEVER** commit `.env`, `cookies.txt`, or any credential files
- Check for required env vars early and raise `RuntimeError` if missing

### General Principles
- Use subprocess for external CLI tools (ffmpeg) with `check=True`
- Suppress noisy subprocess output: `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL`
- Use `tempfile.TemporaryDirectory()` for intermediate artifacts
- Use `os.makedirs(path, exist_ok=True)` when creating output directories
- Prefer `os.path` for consistency with existing code

## Security Notes

The following files contain secrets and must NEVER be committed:
- `.env` — API keys
- `cookies.txt` — authentication cookies

These are already in `.gitignore`.

## Dependencies

Key runtime dependencies (see `pyproject.toml`):
| Package | Purpose |
|---------|---------|
| `yt-dlp` | Download Instagram reels |
| `google-genai` | Google Gemini API client (for VLM frame analysis) |
| `python-dotenv` | Load `.env` files |
| `Pillow` | Image processing |
| `tqdm` | Progress bars for frame analysis |
| `opencv-python` | Computer vision / MSER card detection (standalone scripts) |
| `omniparse` | Document parsing utilities |
