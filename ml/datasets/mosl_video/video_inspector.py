from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def is_video_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def parse_fps(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return 0.0


def inspect_video(path: Path, timeout_seconds: int = 15) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,nb_frames,r_frame_rate,avg_frame_rate,duration",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        payload = json.loads(completed.stdout)
        stream = (payload.get("streams") or [{}])[0]
        fmt = payload.get("format") or {}
        duration = float(stream.get("duration") or fmt.get("duration") or 0.0)
        fps = parse_fps(stream.get("avg_frame_rate") or stream.get("r_frame_rate"))
        frame_count_raw = stream.get("nb_frames")
        frame_count = (
            int(frame_count_raw) if str(frame_count_raw or "").isdigit() else 0
        )
        if frame_count <= 0 and duration > 0 and fps > 0:
            frame_count = int(round(duration * fps))
        width = int(stream.get("width") or 0)
        height = int(stream.get("height") or 0)
        errors: list[str] = []
        if width <= 0 or height <= 0:
            errors.append("invalid_dimensions")
        if duration <= 0:
            errors.append("invalid_duration")
        if fps <= 0:
            errors.append("invalid_fps")
        if frame_count <= 0:
            errors.append("invalid_frame_count")
        return {
            "duration_seconds": round(duration, 6),
            "fps": round(fps, 6),
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "readable": not errors,
            "validation_errors": errors,
        }
    except Exception as exc:
        return {
            "duration_seconds": 0.0,
            "fps": 0.0,
            "frame_count": 0,
            "width": 0,
            "height": 0,
            "readable": False,
            "validation_errors": [f"ffprobe_failed:{type(exc).__name__}"],
        }
