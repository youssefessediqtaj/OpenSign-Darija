"""Prepare identical local PNG frames and Python detector output for browser comparison."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def prepare(video: Path, asset: Path, output: Path, start: float, end: float) -> None:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    if output.exists() or start < 0 or end <= start:
        raise ValueError("output must be new and interval must be valid")
    output.mkdir(parents=True, mode=0o700)
    capture = cv2.VideoCapture(str(video))
    options = vision.HolisticLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(asset)),
        running_mode=vision.RunningMode.VIDEO, min_face_detection_confidence=0.5,
        min_pose_detection_confidence=0.5, min_hand_landmarks_confidence=0.5,
    )
    results = []

    def points(values: object) -> list[list[float]]:
        return [[p.x, p.y, p.z] for p in values] if values else []  # type: ignore[union-attr]

    try:
        with vision.HolisticLandmarker.create_from_options(options) as detector:
            for i in range(12):
                timestamp = start + (end - start) * i / 11
                capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ok, frame = capture.read()
                if not ok:
                    raise ValueError("unable to decode comparison frame")
                path = output / f"frame-{i:02}.png"
                if not cv2.imwrite(str(path), frame):
                    raise OSError("unable to write comparison frame")
                os.chmod(path, 0o600)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), i * 50
                )
                results.append({"pose": points(result.pose_landmarks),
                                "leftHand": points(result.left_hand_landmarks),
                                "rightHand": points(result.right_hand_landmarks),
                                "timestampMs": i * 50})
    finally:
        capture.release()
    path = output / "python.json"
    path.write_text(json.dumps(results), encoding="utf-8")
    os.chmod(path, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asset", type=Path, default=Path("ml/assets/mediapipe/holistic_landmarker.task"))
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    args = parser.parse_args()
    prepare(args.video, args.asset, args.output, args.start, args.end)
    print("Prepared 12 local PNG frames with matching synthetic detector timestamps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
