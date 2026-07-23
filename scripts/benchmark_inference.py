from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPLIT_REPORT = ROOT / "artifacts/reports/model-v1-split-report.json"
OUTPUT_REPORT = ROOT / "artifacts/reports/api-runtime-benchmark.json"
MODEL_DIR = ROOT / "artifacts/models/mosl-isolated-sign-v1"


def select_fixture(split_path: Path, requested: Path | None) -> tuple[Path, str]:
    if requested is not None:
        return requested, "UNCONFIRMED"
    report = json.loads(split_path.read_text(encoding="utf-8"))
    assignments = report.get("assignments", [])
    supported_labels = set(report.get("supported_labels", []))
    candidates = [item for item in assignments if item.get("label_key") in supported_labels]

    # Prefer a held-out supported example that the calibrated package actually accepts
    # correctly. This is an integration-latency fixture, not an added evaluation sample.
    import onnxruntime as ort  # type: ignore[import-untyped]

    labels = json.loads((MODEL_DIR / "labels.json").read_text(encoding="utf-8"))
    calibration = json.loads(
        (MODEL_DIR / "confidence-calibration.json").read_text(encoding="utf-8")
    )
    session = ort.InferenceSession(
        str(MODEL_DIR / "model.onnx"), providers=["CPUExecutionProvider"]
    )
    for preferred_split in ("test", "validation", "train"):
        for item in candidates:
            if item.get("split") != preferred_split:
                continue
            path = ROOT / str(item["processed_landmark_path"])
            if not path.is_file():
                continue
            with np.load(path, allow_pickle=False) as data:
                sequence = np.asarray(data["landmarks"], dtype=np.float32)[None, ...]
            logits = session.run(None, {"landmarks": sequence})[0][0]
            logits = logits / float(calibration["temperature"])
            logits -= logits.max()
            probabilities = np.exp(logits) / np.exp(logits).sum()
            order = np.argsort(probabilities)[::-1]
            top = float(probabilities[order[0]])
            margin = float(probabilities[order[0]] - probabilities[order[1]])
            predicted = str(labels[int(order[0])])
            accepted = (
                top >= float(calibration["unknown_threshold"])
                and margin >= float(calibration["margin_threshold"])
            )
            if accepted and predicted == str(item.get("label_key")):
                return path, predicted
    raise RuntimeError("No local processed landmark fixture exists in the split report")


def load_payload(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as data:
        landmarks = np.asarray(data["landmarks"], dtype=np.float32)
        masks = np.asarray(data["presence_mask"], dtype=np.float32)
    if landmarks.shape != (60, 75, 3) or masks.shape != (60, 75):
        raise RuntimeError(f"Invalid benchmark fixture shape: {landmarks.shape}, {masks.shape}")
    if not np.isfinite(landmarks).all():
        raise RuntimeError("Benchmark fixture contains NaN or Infinity")

    binary_masks = (masks > 0.5).astype(np.int8)
    hand_frames = np.any(binary_masks[:, 33:] == 1, axis=1)
    pose_frames = np.any(binary_masks[:, :33] == 1, axis=1)
    visible_frames = np.any(binary_masks == 1, axis=1)
    duration_ms = 59 * 33
    return {
        "sequence_id": str(uuid4()),
        "captured_at": datetime.now(UTC).isoformat(),
        "recognition_mode": "WORD_ISOLATED",
        "duration_ms": duration_ms,
        "source_fps": 30.0,
        "target_frame_count": 60,
        "landmark_count": 75,
        "coordinate_count": 3,
        "coordinate_format": "shoulder_centered_v1",
        "feature_schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "frames": [
            {
                "index": index,
                "timestamp_ms": index * 33,
                "landmarks": landmarks[index].tolist(),
                "presence_mask": binary_masks[index].tolist(),
            }
            for index in range(60)
        ],
        "quality": {
            "detected_hand_ratio": float(hand_frames.mean()),
            "detected_face_ratio": 0.0,
            "detected_pose_ratio": float(pose_frames.mean()),
            "missing_frame_ratio": float(1.0 - visible_frames.mean()),
            # This benchmark measures transport/inference, not browser boundary tuning.
            "movement_score": 0.5,
        },
        "segmentation_kind": "dynamic",
        "segmentation_reliable": True,
        "usable_frame_count": int(hand_frames.sum()),
    }


def percentile_95(values: list[float]) -> float:
    return sorted(values)[max(0, int(len(values) * 0.95) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the real landmark-only public API.")
    parser.add_argument(
        "--url",
        default=os.getenv(
            "API_BENCHMARK_URL", "http://localhost:8081/api/v1/recognitions/word"
        ),
    )
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--split-report", type=Path, default=SPLIT_REPORT)
    parser.add_argument("--output", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 25:
        raise SystemExit("--requests must be between 1 and 25 (below the public rate limit)")

    fixture, expected_label = select_fixture(args.split_report, args.fixture)
    payload = load_payload(fixture)
    round_trip_ms: list[float] = []
    api_latency_ms: list[float] = []
    statuses: list[str] = []
    returned_labels: list[str | None] = []
    for _ in range(args.requests):
        payload["sequence_id"] = str(uuid4())
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        request = urllib.request.Request(
            args.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise SystemExit(f"Real Docker API is unavailable at {args.url}: {exc}") from exc
        round_trip_ms.append((time.perf_counter() - started) * 1000)
        api_latency_ms.append(float(result["latency_ms"]))
        statuses.append(str(result["status"]))
        returned_labels.append(result.get("label_key"))

    report = {
        "schema_version": "OPEN_SIGNE_RUNTIME_BENCHMARK_V1",
        "measured_at": datetime.now(UTC).isoformat(),
        "url": args.url,
        "requests": args.requests,
        "fixture": fixture.relative_to(ROOT).as_posix()
        if fixture.is_relative_to(ROOT)
        else fixture.as_posix(),
        "fixture_expected_label": expected_label,
        "payload_shape": [60, 75, 3],
        "api_round_trip_ms": {
            "average": round(statistics.mean(round_trip_ms), 3),
            "p50": round(statistics.median(round_trip_ms), 3),
            "p95": round(percentile_95(round_trip_ms), 3),
            "maximum": round(max(round_trip_ms), 3),
        },
        "server_reported_latency_ms": {
            "average": round(statistics.mean(api_latency_ms), 3),
            "p95": round(percentile_95(api_latency_ms), 3),
        },
        "recognized_count": statuses.count("recognized"),
        "unknown_count": statuses.count("unknown"),
        "returned_labels": sorted({label for label in returned_labels if label is not None}),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
