from __future__ import annotations

from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def discover_videos(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS)


def inspect_video(path: Path) -> dict[str, object]:
    try:
        import cv2

        capture = cv2.VideoCapture(path.as_posix())
        if not capture.isOpened():
            return {"valid": False, "error": "OPEN_FAILED"}
        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        capture.release()
        return {
            "valid": True,
            "fps": fps,
            "duration_ms": int((frame_count / fps) * 1000) if fps else None,
            "width": width,
            "height": height,
            "frame_count": int(frame_count),
        }
    except Exception as exc:
        return {"valid": False, "error": exc.__class__.__name__}
