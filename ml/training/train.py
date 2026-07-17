from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.datasets.integrity import TrainingDatasetThresholds, validate_training_dataset
from ml.training.config import load_simple_yaml
from ml.training.reproducibility import set_global_seeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Train OpenSign Darija recognition models.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts/opensign-pilot-gru/0.1.0"))
    parser.add_argument("--resume", type=Path, default=None)
    args = parser.parse_args()

    config = load_simple_yaml(args.config)
    dataset_config = config.get("dataset", {})
    report = validate_training_dataset(
        dataset_version=args.dataset_version,
        feature_schema_version=str(dataset_config.get("feature_schema_version", "1.0.0")),
        thresholds=TrainingDatasetThresholds(
            min_contributors_per_sign=int(dataset_config.get("min_contributors_per_sign", 8)),
            min_repetitions_per_sign=int(dataset_config.get("min_repetitions_per_sign", 80)),
            min_validation_contributors_per_sign=int(
                dataset_config.get("min_validation_contributors_per_sign", 2)
            ),
            min_test_contributors_per_sign=int(dataset_config.get("min_test_contributors_per_sign", 2)),
        ),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dataset_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["valid"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("Dataset invalide: entrainement refuse.")

    metadata = set_global_seeds(int(config.get("experiment", {}).get("seed", 42)))
    (args.output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    raise SystemExit(
        "PyTorch training entrypoint is ready, but no validated dataset was available in this run."
    )


if __name__ == "__main__":
    main()
