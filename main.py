#!/usr/bin/env python3
"""instarec - Extract media recommendations from Instagram Reels.

Pipeline: download reel -> extract unique frames -> VLM analysis -> JSON output.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

from instarec.analyze import analyze_frames
from instarec.download import download_reel
from instarec.frames import extract_unique_frames


def log(msg: str) -> None:
    """Print a status message to stderr (keeps stdout clean for JSON)."""
    print(msg, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="instarec",
        description="Extract media recommendations from an Instagram Reel",
    )
    parser.add_argument("url", help="Instagram Reel URL")
    parser.add_argument(
        "--cookies",
        default="cookies.txt",
        help="Path to yt-dlp cookies file (default: cookies.txt)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash-lite",
        help="Gemini model for frame analysis (default: gemini-2.5-flash-lite)",
    )
    parser.add_argument(
        "--scene-threshold",
        type=float,
        default=0.05,
        help="FFmpeg scene-change threshold, 0-1 (default: 0.05)",
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep downloaded video and extracted frames (default: clean up)",
    )

    args = parser.parse_args()

    if args.keep_files:
        with tempfile.TemporaryDirectory(prefix="instarec_") as tmp:
            output = _run_pipeline(args, tmp_dir=tmp, keep_files=True)
    else:
        with tempfile.TemporaryDirectory(prefix="instarec_") as tmp:
            output = _run_pipeline(args, tmp_dir=tmp, keep_files=False)

    json.dump(output, sys.stdout, indent=2)
    print(file=sys.stdout)  # trailing newline


def _run_pipeline(args: argparse.Namespace, tmp_dir: str, keep_files: bool) -> dict:
    """Execute the three pipeline stages and return the combined result."""

    # Stage 1: Download
    log("[*] Downloading reel...")
    dl = download_reel(
        url=args.url,
        output_dir=tmp_dir,
        cookies_file=args.cookies,
    )
    log(f"[+] Downloaded video to {dl['video_path']}")

    # When keeping files, create data/<reel_id>/ and move the video there
    if keep_files:
        reel_id = dl["id"]
        if not reel_id:
            raise RuntimeError("Could not determine reel ID from yt-dlp metadata")
        work_dir = os.path.join("data", reel_id)
        os.makedirs(work_dir, exist_ok=True)
        kept_video = os.path.join(work_dir, "video.mp4")
        shutil.move(dl["video_path"], kept_video)
        dl["video_path"] = kept_video
        log(f"[+] Saved video to {kept_video}")
    else:
        work_dir = tmp_dir

    # Stage 2: Extract frames
    log("[*] Extracting unique frames...")
    frames_dir = os.path.join(work_dir, "frames")
    frame_paths = extract_unique_frames(
        video_path=dl["video_path"],
        output_dir=frames_dir,
        scene_threshold=args.scene_threshold,
    )
    log(f"[+] Extracted {len(frame_paths)} unique frames")
    if keep_files:
        log(f"[+] Saved frames to {frames_dir}")

    if not frame_paths:
        log("[-] No frames extracted, nothing to analyze")
        return {
            "url": args.url,
            "caption": dl["caption"],
            "media": [],
        }

    # Stage 3: Analyze with VLM
    log(f"[*] Analyzing {len(frame_paths)} frames with {args.model}...")
    media = analyze_frames(frame_paths, model=args.model)
    log(f"[+] Found embedded media in {len(media)} frame(s)")

    return {
        "url": args.url,
        "caption": dl["caption"],
        "media": media,
    }


if __name__ == "__main__":
    main()
