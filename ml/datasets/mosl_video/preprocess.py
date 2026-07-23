from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from ml.preprocessing.landmark_schema_v1 import (
    SCHEMA_VERSION,
    normalize_frame,
    pad_or_truncate_sequence,
)


def load_manifest(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_cache_metadata(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"].item()))
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    return metadata


def cache_valid(path: Path, source_sha256: str) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path, allow_pickle=False) as data:
            landmarks = data["landmarks"]
            presence_mask = data["presence_mask"]
            metadata = json.loads(str(data["metadata"].item()))
        return bool(
            isinstance(metadata, dict)
            and metadata.get("source_sha256") == source_sha256
            and metadata.get("schema_version") == SCHEMA_VERSION
            and metadata.get("preprocessing_version") == PREPROCESSING_VERSION
            and metadata.get("frames") == 60
            and metadata.get("landmarks_per_frame") == 75
            and metadata.get("coordinates") == 3
            and landmarks.shape == (60, 75, 3)
            and presence_mask.shape == (60, 75)
            and np.isfinite(landmarks).all()
            and np.isfinite(presence_mask).all()
            and np.count_nonzero(landmarks) > 0
            and float(presence_mask[:, 33:].sum()) > 0.0
        )
    except Exception:
        return False


def frame_indices(frame_count: int, target_frames: int) -> set[int]:
    if frame_count <= 0:
        return set()
    if frame_count <= target_frames:
        return set(range(frame_count))
    return set(
        np.linspace(0, frame_count - 1, target_frames).round().astype(int).tolist()
    )


def landmarks_to_array(landmarks: object, expected: int) -> np.ndarray:
    if landmarks is None:
        return np.full((expected, 3), np.nan, dtype=np.float32)
    points = (
        landmarks if isinstance(landmarks, list) else getattr(landmarks, "landmark", [])
    )
    array = np.full((expected, 3), np.nan, dtype=np.float32)
    for index, point in enumerate(points[:expected]):
        array[index] = [float(point.x), float(point.y), float(point.z)]
    return array


DEFAULT_MEDIAPIPE_MODEL_PATH = Path("ml/assets/mediapipe/holistic_landmarker.task")
PREPROCESSING_VERSION = "mediapipe_tasks_holistic_v1"


def resolve_mediapipe_model(model_path: Path | None) -> Path:
    path = model_path or DEFAULT_MEDIAPIPE_MODEL_PATH
    if path.exists():
        return path
    raise FileNotFoundError(
        "MediaPipe Holistic task model is missing. Provide the local asset with "
        "`--mediapipe-model` or MEDIAPIPE_HOLISTIC_MODEL_PATH; preprocessing "
        "never downloads assets."
    )


def process_video(
    video_path: Path,
    target_frames: int,
    mediapipe_model_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    try:
        import cv2  # type: ignore[import-not-found]
        import mediapipe as mp  # type: ignore[import-not-found]
        from mediapipe.tasks import python as mp_python  # type: ignore[import-not-found]
        from mediapipe.tasks.python import vision  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "OpenCV and MediaPipe are required for MoSL preprocessing"
        ) from exc

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError("video_decode_failed")
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    wanted = frame_indices(total_frames, target_frames)
    if not wanted:
        raise RuntimeError("video_has_no_frames")

    model_path = resolve_mediapipe_model(mediapipe_model_path)
    options = vision.HolisticLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.IMAGE,
        min_pose_detection_confidence=0.35,
        min_hand_landmarks_confidence=0.35,
    )
    frames: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    body_missing = 0
    left_missing = 0
    right_missing = 0
    processed = 0
    try:
        landmarker = vision.HolisticLandmarker.create_from_options(options)
        index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if index not in wanted:
                index += 1
                continue
            rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect(image)
            pose = landmarks_to_array(getattr(result, "pose_landmarks", None), 33)
            left = landmarks_to_array(getattr(result, "left_hand_landmarks", None), 21)
            right = landmarks_to_array(
                getattr(result, "right_hand_landmarks", None), 21
            )
            normalized = normalize_frame(pose, left, right)
            frames.append(normalized.landmarks)
            masks.append(normalized.presence_mask)
            body_missing += int(normalized.presence_mask[:33].sum() == 0)
            left_missing += int(normalized.presence_mask[33:54].sum() == 0)
            right_missing += int(normalized.presence_mask[54:].sum() == 0)
            processed += 1
            index += 1
    finally:
        if "landmarker" in locals():
            landmarker.close()
        capture.release()

    if not frames:
        raise RuntimeError("no_usable_frames")
    sequence = pad_or_truncate_sequence(np.stack(frames), target_frames=target_frames)
    mask_sequence = np.zeros((target_frames, 75), dtype=np.float32)
    stacked_masks = np.stack(masks).astype(np.float32)
    mask_sequence[: min(len(masks), target_frames)] = stacked_masks[:target_frames]
    metadata = {
        "source_frames": total_frames,
        "processed_frames": processed,
        "zero_body_ratio": round(body_missing / max(processed, 1), 6),
        "missing_left_hand_ratio": round(left_missing / max(processed, 1), 6),
        "missing_right_hand_ratio": round(right_missing / max(processed, 1), 6),
    }
    return sequence, mask_sequence, metadata


def cache_quality(path: Path) -> dict[str, Any]:
    metadata = read_cache_metadata(path)
    with np.load(path, allow_pickle=False) as data:
        landmarks = data["landmarks"]
        mask = data["presence_mask"]
    return {
        "processed_frames": int(metadata.get("processed_frames", landmarks.shape[0])),
        "source_frames": int(metadata.get("source_frames", 0)),
        "zero_body_ratio": float(metadata.get("zero_body_ratio", 0.0)),
        "missing_left_hand_ratio": float(metadata.get("missing_left_hand_ratio", 0.0)),
        "missing_right_hand_ratio": float(
            metadata.get("missing_right_hand_ratio", 0.0)
        ),
        "contains_nan": bool(np.isnan(landmarks).any() or np.isnan(mask).any()),
        "contains_infinity": bool(np.isinf(landmarks).any() or np.isinf(mask).any()),
        "all_zero_sequence": bool(np.count_nonzero(landmarks) == 0),
        "output_size_bytes": path.stat().st_size,
    }


def build_summary(
    *,
    manifest: Path,
    records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    output: Path,
    target_frames: int,
    duration_seconds: float,
    mediapipe_model_path: Path | None,
) -> dict[str, Any]:
    successful = [
        item for item in statuses if item["status"] in {"processed", "cached"}
    ]
    timings = [float(item.get("processing_seconds", 0.0)) for item in statuses]
    source_frames = [
        float(item.get("source_frames", 0.0))
        for item in statuses
        if float(item.get("source_frames", 0.0)) > 0
    ]
    low_body = [
        item for item in successful if float(item.get("zero_body_ratio", 0.0)) >= 0.5
    ]
    low_left = [
        item
        for item in successful
        if float(item.get("missing_left_hand_ratio", 0.0)) >= 0.8
    ]
    low_right = [
        item
        for item in successful
        if float(item.get("missing_right_hand_ratio", 0.0)) >= 0.8
    ]
    by_category: dict[str, dict[str, int]] = {}
    by_mode: dict[str, dict[str, int]] = {}
    for item in statuses:
        category = str(item.get("category", "UNKNOWN"))
        mode = str(item.get("mode", "UNKNOWN"))
        for bucket, key in ((by_category, category), (by_mode, mode)):
            bucket.setdefault(
                key, {"total": 0, "processed": 0, "cached": 0, "failed": 0}
            )
            bucket[key]["total"] += 1
            if item["status"] in bucket[key]:
                bucket[key][item["status"]] += 1
    p95 = float(np.percentile(timings, 95)) if timings else 0.0
    asset_checksum = sha256_file(mediapipe_model_path) if mediapipe_model_path else ""
    return {
        "manifest": manifest.as_posix(),
        "target_frames": target_frames,
        "total_manifest_entries": len(records),
        "total_source_videos": len(records),
        "attempted": len(selected),
        "successfully_processed": len(successful),
        "newly_processed": sum(1 for item in statuses if item["status"] == "processed"),
        "cache_hits": sum(1 for item in statuses if item["status"] == "cached"),
        "failed": sum(1 for item in statuses if item["status"] == "failed"),
        "unreadable_videos": sum(
            1 for item in records if item.get("readable") is False
        ),
        "invalid_labels": sum(
            1
            for item in records
            if item.get("validation_errors") or not item.get("label_key")
        ),
        "sequences_containing_nan": sum(
            1 for item in successful if item.get("contains_nan")
        ),
        "sequences_containing_infinity": sum(
            1 for item in successful if item.get("contains_infinity")
        ),
        "sequences_containing_only_zeros": sum(
            1 for item in successful if item.get("all_zero_sequence")
        ),
        "low_body_detection_sequences": len(low_body),
        "low_left_hand_detection_sequences": len(low_left),
        "low_right_hand_detection_sequences": len(low_right),
        "zero_body_detection_videos": sum(
            1 for item in successful if float(item.get("zero_body_ratio", 0.0)) == 1.0
        ),
        "average_source_frames": round(
            sum(source_frames) / max(len(source_frames), 1), 3
        ),
        "average_output_frames": target_frames,
        "average_processing_time": round(sum(timings) / max(len(timings), 1), 6),
        "p95_processing_time": round(p95, 6),
        "total_output_size_bytes": sum(
            path.stat().st_size for path in output.glob("*.npz") if path.is_file()
        ),
        "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "preprocessing_version": PREPROCESSING_VERSION,
        "mediapipe_asset_checksum": asset_checksum,
        "duration_seconds": round(duration_seconds, 6),
        "average_seconds_per_video": round(duration_seconds / max(len(selected), 1), 6),
        "category_statistics": by_category,
        "mode_statistics": by_mode,
    }


def preprocess_manifest(
    manifest: Path,
    dataset_root: Path,
    output: Path,
    report_dir: Path,
    target_frames: int = 60,
    limit: int | None = None,
    mediapipe_model_path: Path | None = None,
    progress_every: int = 25,
) -> dict[str, Any]:
    records = load_manifest(manifest)
    output.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    statuses: list[dict[str, Any]] = []
    started = perf_counter()
    selected = records[:limit] if limit else records
    resolved_model_path = resolve_mediapipe_model(mediapipe_model_path)
    for record in selected:
        status = {
            "sha256": record["sha256"],
            "current_relative_path": record["current_relative_path"],
            "category": record.get("category", "UNKNOWN"),
            "label_key": record["label_key"],
            "mode": record["mode"],
            "status": "pending",
            "error": "",
            "output": "",
            "processing_seconds": 0.0,
            "source_frames": int(record.get("frame_count") or 0),
        }
        cache_path = output / f"{record['sha256']}.npz"
        if cache_valid(cache_path, str(record["sha256"])):
            status.update({"status": "cached", "output": cache_path.as_posix()})
            status.update(cache_quality(cache_path))
            statuses.append(status)
            if progress_every > 0 and len(statuses) % progress_every == 0:
                elapsed = perf_counter() - started
                avg = elapsed / max(len(statuses), 1)
                remaining = max(len(selected) - len(statuses), 0) * avg
                print(
                    json.dumps(
                        {
                            "event": "preprocess_progress",
                            "processed_count": sum(
                                1 for item in statuses if item["status"] == "processed"
                            ),
                            "cache_hit_count": sum(
                                1 for item in statuses if item["status"] == "cached"
                            ),
                            "failure_count": sum(
                                1 for item in statuses if item["status"] == "failed"
                            ),
                            "current_video": record["current_relative_path"],
                            "average_time_per_video": round(avg, 6),
                            "estimated_remaining_seconds": round(remaining, 3),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            continue
        item_started = perf_counter()
        try:
            video_path = dataset_root / str(record["current_relative_path"])
            sequence, mask, metadata = process_video(
                video_path,
                target_frames=target_frames,
                mediapipe_model_path=resolved_model_path,
            )
            metadata = {
                **metadata,
                "source_sha256": record["sha256"],
                "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                "preprocessing_version": PREPROCESSING_VERSION,
                "coordinate_format": "shoulder_centered_v1",
                "frames": target_frames,
                "landmarks_per_frame": 75,
                "coordinates": 3,
                "label_key": record["label_key"],
                "mode": record["mode"],
            }
            np.savez_compressed(
                cache_path,
                landmarks=sequence,
                presence_mask=mask,
                metadata=np.array(json.dumps(metadata, ensure_ascii=False)),
            )
            status.update({"status": "processed", "output": cache_path.as_posix()})
            status.update(
                {
                    "processed_frames": metadata["processed_frames"],
                    "source_frames": metadata["source_frames"],
                    "zero_body_ratio": metadata["zero_body_ratio"],
                    "missing_left_hand_ratio": metadata["missing_left_hand_ratio"],
                    "missing_right_hand_ratio": metadata["missing_right_hand_ratio"],
                    "contains_nan": bool(
                        np.isnan(sequence).any() or np.isnan(mask).any()
                    ),
                    "contains_infinity": bool(
                        np.isinf(sequence).any() or np.isinf(mask).any()
                    ),
                    "all_zero_sequence": bool(np.count_nonzero(sequence) == 0),
                    "output_size_bytes": cache_path.stat().st_size,
                }
            )
        except Exception as exc:
            status.update({"status": "failed", "error": str(exc)})
        status["processing_seconds"] = round(perf_counter() - item_started, 6)
        statuses.append(status)
        if progress_every > 0 and len(statuses) % progress_every == 0:
            elapsed = perf_counter() - started
            avg = elapsed / max(len(statuses), 1)
            remaining = max(len(selected) - len(statuses), 0) * avg
            print(
                json.dumps(
                    {
                        "event": "preprocess_progress",
                        "processed_count": sum(
                            1 for item in statuses if item["status"] == "processed"
                        ),
                        "cache_hit_count": sum(
                            1 for item in statuses if item["status"] == "cached"
                        ),
                        "failure_count": sum(
                            1 for item in statuses if item["status"] == "failed"
                        ),
                        "current_video": record["current_relative_path"],
                        "average_time_per_video": round(avg, 6),
                        "estimated_remaining_seconds": round(remaining, 3),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    duration_seconds = perf_counter() - started
    summary = build_summary(
        manifest=manifest,
        records=records,
        selected=selected,
        statuses=statuses,
        output=output,
        target_frames=target_frames,
        duration_seconds=duration_seconds,
        mediapipe_model_path=resolved_model_path,
    )
    (report_dir / "preprocessing-report.json").write_text(
        json.dumps(
            {"summary": summary, "items": statuses}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    with (report_dir / "preprocessing-report.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(statuses[0].keys()) if statuses else ["sha256"]
        )
        writer.writeheader()
        writer.writerows(statuses)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preprocess MoSL videos into landmark caches."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/manifests/videos.jsonl"),
    )
    parser.add_argument(
        "--dataset-root", type=Path, default=Path("ml/data/external/mosl-video-dataset")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/processed/landmarks"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/reports"),
    )
    parser.add_argument("--target-frames", type=int, default=60)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--mediapipe-model",
        type=Path,
        default=(
            Path(os.environ["MEDIAPIPE_HOLISTIC_MODEL_PATH"])
            if os.environ.get("MEDIAPIPE_HOLISTIC_MODEL_PATH")
            else None
        ),
    )
    parser.add_argument("--progress-every", type=int, default=25)
    args = parser.parse_args()
    print(
        json.dumps(
            preprocess_manifest(
                args.manifest,
                args.dataset_root,
                args.output,
                args.report_dir,
                target_frames=args.target_frames,
                limit=args.limit,
                mediapipe_model_path=args.mediapipe_model,
                progress_every=args.progress_every,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
