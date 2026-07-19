from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from ml.datasets.mosl_video.preprocess import PREPROCESSING_VERSION, load_manifest
from ml.preprocessing.landmark_schema_v1 import COORDINATE_FORMAT, SCHEMA_VERSION


def validate_artifact(
    record: dict[str, Any],
    processed_dir: Path,
    checksum_counts: Counter[str],
) -> dict[str, Any]:
    sha256 = str(record["sha256"])
    path = processed_dir / f"{sha256}.npz"
    item = {
        "sha256": sha256,
        "path": path.as_posix(),
        "status": "valid",
        "errors": [],
        "warnings": [],
    }
    errors: list[str] = item["errors"]
    warnings: list[str] = item["warnings"]
    if path.name != f"{sha256}.npz":
        errors.append("cache_filename_does_not_match_sha256")
    if not path.exists():
        errors.append("missing_artifact")
        item["status"] = "invalid"
        return item
    try:
        with np.load(path, allow_pickle=False) as data:
            if "landmarks" not in data.files:
                errors.append("missing_landmarks_array")
                landmarks = None
            else:
                landmarks = data["landmarks"]
            if "presence_mask" not in data.files:
                errors.append("missing_presence_mask_array")
                mask = None
            else:
                mask = data["presence_mask"]
            if "metadata" not in data.files:
                errors.append("missing_metadata")
                metadata = {}
            else:
                metadata = json.loads(str(data["metadata"].item()))
    except Exception as exc:
        errors.append(f"artifact_open_failed:{exc}")
        item["status"] = "invalid"
        return item

    if metadata.get("source_sha256") != sha256:
        errors.append("source_checksum_mismatch")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if metadata.get("preprocessing_version") != PREPROCESSING_VERSION:
        errors.append("preprocessing_version_mismatch")
    is_duplicate_checksum = checksum_counts[sha256] > 1
    if metadata.get("label_key") != record.get("label_key") and is_duplicate_checksum:
        warnings.append("duplicate_checksum_label_metadata_differs")
    elif metadata.get("label_key") != record.get("label_key"):
        errors.append("label_key_mismatch")
    if metadata.get("mode") != record.get("mode"):
        errors.append("recognition_mode_mismatch")
    if metadata.get("coordinate_format") not in {None, COORDINATE_FORMAT}:
        errors.append("coordinate_format_mismatch")

    if landmarks is not None:
        if landmarks.shape != (60, 75, 3):
            errors.append(f"invalid_landmarks_shape:{landmarks.shape}")
        if landmarks.dtype != np.float32:
            errors.append(f"invalid_landmarks_dtype:{landmarks.dtype}")
        if np.isnan(landmarks).any():
            errors.append("landmarks_contains_nan")
        if np.isinf(landmarks).any():
            errors.append("landmarks_contains_infinity")
        if np.count_nonzero(landmarks) == 0:
            warnings.append("all_zero_sequence")
        if float(np.max(np.abs(landmarks))) > 20:
            warnings.append("normalized_values_outside_documented_bounds")

    if mask is not None:
        if mask.shape != (60, 75):
            errors.append(f"invalid_presence_mask_shape:{mask.shape}")
        if not (
            np.issubdtype(mask.dtype, np.floating)
            or np.issubdtype(mask.dtype, np.integer)
            or np.issubdtype(mask.dtype, np.bool_)
        ):
            errors.append(f"invalid_presence_mask_dtype:{mask.dtype}")
        if np.isnan(mask).any():
            errors.append("presence_mask_contains_nan")
        if np.isinf(mask).any():
            errors.append("presence_mask_contains_infinity")
        if not np.isin(mask, [0, 1]).all():
            errors.append("presence_mask_non_binary")

    if float(metadata.get("zero_body_ratio", 0.0)) >= 0.5:
        warnings.append("low_body_detection")
    if float(metadata.get("missing_left_hand_ratio", 0.0)) >= 0.8:
        warnings.append("low_left_hand_detection")
    if float(metadata.get("missing_right_hand_ratio", 0.0)) >= 0.8:
        warnings.append("low_right_hand_detection")
    item["status"] = "invalid" if errors else "valid"
    return item


def validate_manifest(
    manifest: Path, processed_dir: Path, output: Path
) -> dict[str, Any]:
    records = load_manifest(manifest)
    checksum_counts = Counter(str(record["sha256"]) for record in records)
    items = [
        validate_artifact(record, processed_dir, checksum_counts) for record in records
    ]
    invalid = [item for item in items if item["status"] == "invalid"]
    report = {
        "valid": not invalid,
        "manifest": manifest.as_posix(),
        "processed_dir": processed_dir.as_posix(),
        "total_manifest_entries": len(records),
        "valid_artifacts": sum(1 for item in items if item["status"] == "valid"),
        "invalid_artifacts": len(invalid),
        "warning_count": sum(len(item["warnings"]) for item in items),
        "duplicate_checksum_count": sum(
            value - 1 for value in checksum_counts.values()
        ),
        "schema_version": SCHEMA_VERSION,
        "preprocessing_version": PREPROCESSING_VERSION,
        "items": items,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate MoSL processed landmark artifacts."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/manifests/videos.jsonl"),
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/processed/landmarks"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "ml/data/external/mosl-video-dataset/reports/processed-artifact-validation.json"
        ),
    )
    args = parser.parse_args()
    report = validate_manifest(args.manifest, args.processed_dir, args.output)
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "items"}, indent=2
        )
    )
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
