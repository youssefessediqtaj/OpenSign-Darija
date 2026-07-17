from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.datasets.dataset_loader import load_samples
from ml.datasets.integrity import validate_training_dataset
from ml.evaluation.metrics import classification_metrics, top_k_accuracy
from ml.models.baseline import CentroidBaseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the centroid baseline.")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts/opensign-pilot-baseline/0.1.0"))
    args = parser.parse_args()

    report = validate_training_dataset(dataset_version=args.dataset_version, manifest_path=args.manifest)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dataset_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["valid"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("Dataset invalide: baseline refusee.")

    train = load_samples(args.manifest, splits={"TRAIN"})
    test = load_samples(args.manifest, splits={"TEST"})
    labels = sorted({sample.label for sample in train})
    model = CentroidBaseline()
    model.fit(train)
    ranked = [[label for label, _ in model.predict(sample)] for sample in test]
    top1 = [predictions[0] for predictions in ranked]
    metrics = classification_metrics([sample.label for sample in test], top1, labels)
    metrics["accuracy_top3"] = top_k_accuracy([sample.label for sample in test], ranked, 3)
    model.save(args.output_dir / "centroids.json")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
