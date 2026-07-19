from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def split_mode_records(
    records: list[dict[str, Any]], seed: int = 42
) -> tuple[list[list[dict[str, Any]]], dict[str, Any]]:
    rng = random.Random(seed)
    eligible = [item for item in records if item["readable"]]
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in eligible:
        by_label[str(record["label_key"])].append(record)

    train: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    excluded: list[str] = []
    singleton: list[str] = []
    two_sample: list[str] = []

    for label, items in sorted(by_label.items()):
        unique_by_checksum = {str(item["sha256"]): item for item in items}
        samples = list(unique_by_checksum.values())
        rng.shuffle(samples)
        if len(samples) < 2:
            excluded.append(label)
            singleton.append(label)
            continue
        if len(samples) == 2:
            two_sample.append(label)
            train.append(samples[0])
            validation.append(samples[1])
            continue
        test_count = max(1, round(len(samples) * 0.15))
        validation_count = max(1, round(len(samples) * 0.15))
        train_count = len(samples) - validation_count - test_count
        if train_count <= 0:
            train_count = 1
            validation_count = max(1, len(samples) - train_count - test_count)
        train.extend(samples[:train_count])
        validation.extend(samples[train_count : train_count + validation_count])
        test.extend(samples[train_count + validation_count :])

    report = {
        "seed": seed,
        "readable_samples": len(eligible),
        "classes": len(by_label),
        "classes_excluded_from_training": excluded,
        "singleton_classes": singleton,
        "two_sample_classes": two_sample,
        "train_count": len(train),
        "validation_count": len(validation),
        "test_count": len(test),
        "samples_per_class": dict(
            sorted(Counter(str(item["label_key"]) for item in eligible).items())
        ),
        "split_limitation": (
            "Signer identity is unavailable in local filenames; split is class-aware "
            "but not signer-independent."
        ),
    }
    return [train, validation, test], report


def write_split(path: Path, records: list[dict[str, Any]], split_name: str) -> None:
    payload = [
        {
            "sha256": item["sha256"],
            "current_relative_path": item["current_relative_path"],
            "label_key": item["label_key"],
            "normalized_label_ar": item["normalized_label_ar"],
            "mode": item["mode"],
            "split": split_name,
        }
        for item in records
    ]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def build_splits(manifest: Path, output_dir: Path, seed: int = 42) -> dict[str, Any]:
    records = load_records(manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}
    for mode, prefix in [
        ("WORD_ISOLATED", "word-isolated"),
        ("ALPHABET_STATIC", "alphabet-static"),
    ]:
        mode_records = [item for item in records if item["mode"] == mode]
        splits, mode_report = split_mode_records(mode_records, seed=seed)
        train, validation, test = splits
        write_split(output_dir / f"{prefix}-train.json", train, "train")
        write_split(output_dir / f"{prefix}-validation.json", validation, "validation")
        write_split(output_dir / f"{prefix}-test.json", test, "test")
        report[mode] = mode_report
    (output_dir / "split-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build leakage-aware MoSL dataset splits."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/manifests/videos.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/splits"),
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(
        json.dumps(
            build_splits(args.manifest, args.output, args.seed),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
