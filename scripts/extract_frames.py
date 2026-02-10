#!/usr/bin/env python3

import argparse
import subprocess
import tempfile
import shutil
import os
from PIL import Image
import imagehash


def extract_scene_frames(video_path, out_dir, scene_threshold):
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        f"select='gt(scene,{scene_threshold})'",
        "-vsync",
        "vfr",
        os.path.join(out_dir, "frame_%04d.jpg"),
    ]
    subprocess.run(
        cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def dedupe_frames(in_dir, out_dir, hash_threshold):
    os.makedirs(out_dir, exist_ok=True)

    hashes = []
    kept = 0

    for fname in sorted(os.listdir(in_dir)):
        path = os.path.join(in_dir, fname)
        img = Image.open(path).convert("RGB")
        h = imagehash.phash(img)

        if all(abs(h - prev) > hash_threshold for prev in hashes):
            shutil.copy(path, os.path.join(out_dir, fname))
            hashes.append(h)
            kept += 1

    return kept


def main():
    parser = argparse.ArgumentParser(
        description="Extract unique frames from an MP4 using scene detection + perceptual hashing"
    )
    parser.add_argument("video", help="Path to MP4 file")
    parser.add_argument(
        "--scene-threshold",
        type=float,
        default=0.3,
        help="FFmpeg scene change threshold (default: 0.3)",
    )
    parser.add_argument(
        "--hash-threshold",
        type=int,
        default=10,
        help="Perceptual hash distance threshold (default: 10)",
    )
    parser.add_argument(
        "--output", default="frames", help="Output directory (default: unique_frames)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.video):
        raise FileNotFoundError(args.video)

    with tempfile.TemporaryDirectory() as tmp:
        print("[*] Extracting scene-change frames…")
        extract_scene_frames(args.video, tmp, args.scene_threshold)

        print("[*] Deduplicating frames…")
        kept = dedupe_frames(tmp, args.output, args.hash_threshold)

    print(f"[✓] Done. Saved {kept} unique frames to '{args.output}/'")


if __name__ == "__main__":
    main()
