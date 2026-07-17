from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.datasets.integrity import TrainingDatasetThresholds, validate_training_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a dataset before ML training.")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--feature-schema-version", default="1.0.0")
    parser.add_argument("--landmark-root", type=Path, default=Path("artifacts/landmarks"))
    parser.add_argument("--report-json", type=Path, default=Path("artifacts/ml/training-validation.json"))
    parser.add_argument("--report-text", type=Path, default=Path("artifacts/ml/training-validation.txt"))
    parser.add_argument("--min-contributors-per-sign", type=int, default=8)
    parser.add_argument("--min-repetitions-per-sign", type=int, default=80)
    parser.add_argument("--min-validation-contributors-per-sign", type=int, default=2)
    parser.add_argument("--min-test-contributors-per-sign", type=int, default=2)
    args = parser.parse_args()

    report = validate_training_dataset(
        dataset_version=args.dataset_version,
        manifest_path=args.manifest,
        feature_schema_version=args.feature_schema_version,
        landmark_root=args.landmark_root,
        thresholds=TrainingDatasetThresholds(
            min_contributors_per_sign=args.min_contributors_per_sign,
            min_repetitions_per_sign=args.min_repetitions_per_sign,
            min_validation_contributors_per_sign=args.min_validation_contributors_per_sign,
            min_test_contributors_per_sign=args.min_test_contributors_per_sign,
        ),
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"Dataset version: {report['dataset_version']}",
        f"Valid for training: {report['valid']}",
        "Errors:",
        *[f"- {item}" for item in report["errors"]],
        "Warnings:",
        *[f"- {item}" for item in report["warnings"]],
    ]
    args.report_text.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
