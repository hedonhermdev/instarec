"""Extract unique frames from a video using scene detection."""

import os
import shutil
import subprocess
import tempfile


def extract_scene_frames(video_path: str, out_dir: str, scene_threshold: float) -> None:
    """Run ffmpeg scene-change detection and write raw frames to *out_dir*."""
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


def extract_unique_frames(
    video_path: str,
    output_dir: str = "frames",
    scene_threshold: float = 0.05,
) -> list[str]:
    """Extract scene-change frames from a video.

    Args:
        video_path: Path to MP4 file.
        output_dir: Directory to write frames into.
        scene_threshold: FFmpeg scene-change sensitivity (0-1, lower = more frames).

    Returns:
        Sorted list of paths to the extracted frames.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    with tempfile.TemporaryDirectory() as tmp:
        extract_scene_frames(video_path, tmp, scene_threshold)

        os.makedirs(output_dir, exist_ok=True)
        kept: list[str] = []
        for fname in sorted(os.listdir(tmp)):
            src = os.path.join(tmp, fname)
            dest = os.path.join(output_dir, fname)
            shutil.copy(src, dest)
            kept.append(dest)

    return kept
