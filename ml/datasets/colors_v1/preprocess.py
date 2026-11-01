"""Local video-mode COLORS_V1 feature extraction; outputs remain experimental/private."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from ml.datasets.colors_v1.review import validate_review
from ml.datasets.colors_v1.validate import _contained_file, sha256
from ml.preprocessing.landmark_schema_v1 import normalize_frame

FEATURE_VERSION = "COLORS_V1_VIDEO_V1_EXPERIMENTAL"


def sample_indices(count: int, target: int = 60) -> np.ndarray:
    """Match JavaScript Math.round on nonnegative uniformly spaced indices."""
    if count <= 0 or target <= 0:
        raise ValueError("nonempty source and positive target required")
    if target == 1:
        return np.array([0], dtype=np.int64)
    return np.floor(np.arange(target, dtype=np.float64) * (count - 1) / (target - 1) + 0.5).astype(np.int64)


def frame_timestamps(path: Path) -> list[float]:
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                             "frame=best_effort_timestamp_time", "-of", "json", str(path)],
                            capture_output=True, text=True, check=True, timeout=60)
    frames = json.loads(result.stdout)["frames"]
    times = [float(frame["best_effort_timestamp_time"]) for frame in frames]
    if not times or any(not math.isfinite(t) for t in times):
        raise ValueError("video has missing or invalid frame timestamps")
    if any(b < a for a, b in zip(times, times[1:])):
        raise ValueError("video timestamps are not monotonic")
    return times


def points(value: Any, count: int) -> np.ndarray:
    result = np.full((count, 3), np.nan, dtype=np.float32)
    for i, point in enumerate((value or [])[:count]):
        result[i] = [point.x, point.y, point.z]
    return result


def extract(video: Path, asset: Path, *, start: float = 0, end: float | None = None) -> dict[str, Any]:
    """Detect sequentially in VIDEO mode; interval selection remains unreviewed unless supplied."""
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    timestamps = frame_timestamps(video)
    if not math.isfinite(start) or start < 0 or (end is not None and (not math.isfinite(end) or end <= start)):
        raise ValueError("invalid time interval")
    duration = timestamps[-1] - timestamps[0]
    if start >= duration or (end is not None and end > duration + 0.1):
        raise ValueError("time interval is outside the video")
    options = vision.HolisticLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(asset)),
        running_mode=vision.RunningMode.VIDEO,
        min_face_detection_confidence=0.5, min_pose_detection_confidence=0.5,
        min_hand_landmarks_confidence=0.5,
    )
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError("video could not be decoded")
    frames, masks, detected_times = [], [], []
    selected = decoded = 0
    last_selected = -float("inf")
    last_timestamp = -1
    hand_count = pose_count = 0
    begin = time.perf_counter()
    try:
        with vision.HolisticLandmarker.create_from_options(options) as landmarker:
            for timestamp in timestamps:
                ok, image = capture.read()
                if not ok:
                    raise RuntimeError("decoder ended before timestamp list")
                decoded += 1
                relative = timestamp - timestamps[0]
                if relative < start or (end is not None and relative > end):
                    continue
                if relative - last_selected < 1 / 24:
                    continue
                last_selected = relative
                selected += 1
                frame_ms = max(last_timestamp + 1, round(relative * 1000))
                last_timestamp = frame_ms
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                result = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), frame_ms)
                pose = points(result.pose_landmarks, 33)
                left = points(result.left_hand_landmarks, 21)
                right = points(result.right_hand_landmarks, 21)
                pose_ok = np.isfinite(pose[[11, 12]]).all()
                hand_ok = np.isfinite(left).all(axis=1).any() or np.isfinite(right).all(axis=1).any()
                pose_count += int(pose_ok)
                hand_count += int(hand_ok)
                if not pose_ok or not hand_ok:
                    continue
                normalized = normalize_frame(pose, left, right)
                frames.append(np.round(normalized.landmarks, 6))
                masks.append(normalized.presence_mask)
                detected_times.append(relative)
    finally:
        capture.release()
    if len(frames) < 2:
        raise ValueError("fewer than two frames with shoulders and a hand")
    indices = sample_indices(len(frames))
    return {"landmarks": np.stack(frames)[indices], "presence_mask": np.stack(masks)[indices],
            "sampled_source_times_seconds": np.asarray(detected_times)[indices],
            "decoded_frames": decoded, "detector_frames": selected, "valid_frames": len(frames),
            "pose_detected_frames": pose_count, "hand_detected_frames": hand_count,
            "source_start_seconds": start, "source_end_seconds": end,
            "first_hand_seconds": min(detected_times), "last_hand_seconds": max(detected_times),
            "elapsed_seconds": round(time.perf_counter() - begin, 3)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--video-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--asset", type=Path, default=Path("ml/assets/mediapipe/holistic_landmarker.task"))
    parser.add_argument("--video-id", help="optionally process one source")
    parser.add_argument("--review", type=Path, help="optional source-hash-bound review JSON")
    args = parser.parse_args()
    root = args.video_root.resolve()
    legacy = (Path(__file__).resolve().parents[2] / "data/external/mosl-video-dataset").resolve()
    if root == legacy or root.is_relative_to(legacy) or legacy.is_relative_to(root):
        parser.error("video root must be isolated from legacy data")
    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    review_rows = json.loads(args.review.read_text(encoding="utf-8")) if args.review else []
    reviews = {row["video_id"]: row for row in review_rows}
    if len(reviews) != len(review_rows):
        raise ValueError("duplicate review video_id")
    destination = args.output_dir.resolve()
    if destination == legacy or destination.is_relative_to(legacy) or legacy.is_relative_to(destination):
        parser.error("output must be isolated from legacy data")
    if destination == root or destination.is_relative_to(root):
        parser.error("output must be separate from source video directory")
    args.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    found = False
    for item in records:
        if args.video_id and item["video_id"] != args.video_id:
            continue
        found = True
        if not isinstance(item.get("video_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]+", item["video_id"]):
            raise ValueError("video_id must be a safe identifier")
        path = _contained_file(root, item["file_path"])
        if sha256(path) != item["file_hash"]:
            raise ValueError("source missing, outside video root, or checksum changed")
        if item.get("local_experimental_training_permission") not in {"owner_confirmed", "owner_confirmed_2026-11-01"}:
            raise ValueError("local experimental use permission is not confirmed")
        output = args.output_dir / (item["video_id"] + ".npz")
        if output.exists():
            raise FileExistsError(f"refusing to overwrite {output}")
        review = reviews.get(item["video_id"])
        if review is not None:
            validate_review(review, item)
        approved = review is not None and review["technical_review_status"] == "APPROVED"
        start = float(review["sign_start_time"]) if approved else 0.0
        end = float(review["sign_end_time"]) if approved else None
        data = extract(path, args.asset, start=start, end=end)
        arrays = {k: data.pop(k) for k in ("landmarks", "presence_mask", "sampled_source_times_seconds")}
        metadata = {**data, "dataset_id": "colors_v1", "video_id": item["video_id"],
                    "semantic_label": item["semantic_label"], "sign_variant_id": item["sign_variant_id"],
                    "source_sha256": item["file_hash"], "asset_sha256": sha256(args.asset),
                    "feature_version": FEATURE_VERSION,
                    "segmentation_method": review["segmentation_method"] if approved else "full_clip_unreviewed",
                    "technical_review_status": review["technical_review_status"] if review else "PENDING",
                    "linguistic_review_status": review["linguistic_review_status"] if review else "PENDING"}
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            np.savez_compressed(stream, **arrays, metadata=json.dumps(metadata))
        print(json.dumps(metadata), flush=True)
    if not found:
        raise ValueError("requested video_id not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
