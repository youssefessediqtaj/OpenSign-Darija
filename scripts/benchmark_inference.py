from __future__ import annotations

import json
import os
import statistics
import time
import urllib.request
from datetime import UTC, datetime
from uuid import uuid4


def payload() -> dict[str, object]:
    frames = [
        {
            "index": index,
            "timestamp_ms": index * 33,
            "features": [0.0] * 63,
            "presence_mask": [1] * 21,
        }
        for index in range(30)
    ]
    return {
        "sequence_id": str(uuid4()),
        "captured_at": datetime.now(UTC).isoformat(),
        "duration_ms": 1200,
        "source_fps": 30,
        "target_frame_count": 30,
        "coordinate_format": "torso_normalized_v1",
        "feature_schema_version": "1.0.0",
        "frames": frames,
        "quality": {
            "detected_hand_ratio": 1,
            "detected_face_ratio": 1,
            "detected_pose_ratio": 1,
            "missing_frame_ratio": 0,
            "movement_score": 0.5,
        },
    }


def main() -> None:
    url = os.getenv("INFERENCE_BENCHMARK_URL", "http://localhost:8001/predict")
    latencies = []
    for _ in range(20):
        body = json.dumps(payload()).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read()
        latencies.append((time.perf_counter() - started) * 1000)
    print(
        json.dumps(
            {
                "requests": len(latencies),
                "p50_ms": statistics.median(latencies),
                "p95_ms": sorted(latencies)[int(len(latencies) * 0.95) - 1],
                "max_ms": max(latencies),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
