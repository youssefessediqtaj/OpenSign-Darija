from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
RECOGNITION_MODE = "WORD_ISOLATED"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_assignments(split_dir: Path) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for split in ("train", "validation", "test"):
        path = split_dir / f"word-isolated-{split}.json"
        if not path.exists():
            continue
        for item in load_json(path):
            assignments[str(item["sha256"])] = split
    return assignments


def inspect_cache(path: Path, source_sha256: str) -> tuple[str, str, int]:
    if not path.exists():
        return "missing_cache", "processed cache missing", 0
    try:
        with np.load(path, allow_pickle=False) as data:
            landmarks = data["landmarks"]
            mask = data["presence_mask"]
            metadata = json.loads(str(data["metadata"].item()))
        if landmarks.ndim != 3 or landmarks.shape[1:] != (75, 3):
            return "invalid_cache", "landmarks shape is not frames x 75 x 3", 0
        if mask.shape != (landmarks.shape[0], 75):
            return "invalid_cache", "presence mask shape does not match landmarks", 0
        if metadata.get("source_sha256") != source_sha256:
            return "invalid_cache", "source checksum mismatch", 0
        if metadata.get("schema_version") != SCHEMA_VERSION:
            return "invalid_cache", "schema version mismatch", 0
        return "processed", "", int(landmarks.shape[0])
    except Exception as exc:
        return "invalid_cache", f"cache read failed: {exc}", 0


def evaluate_label_eligibility(
    processed_by_label: dict[str, list[dict[str, Any]]],
    *,
    min_samples_per_class: int,
    require_train_sample: bool,
    require_validation_sample: bool,
    require_test_sample: bool,
) -> tuple[list[str], dict[str, str]]:
    eligible_labels: list[str] = []
    label_reasons: dict[str, str] = {}
    for label, label_samples in sorted(processed_by_label.items()):
        split_counts = Counter(str(sample["split"]) for sample in label_samples)
        reason = ""
        if len(label_samples) < min_samples_per_class:
            reason = "insufficient_processed_samples"
        elif require_train_sample and split_counts["train"] < 1:
            reason = "missing_train_sample"
        elif require_validation_sample and split_counts["validation"] < 1:
            reason = "missing_validation_sample"
        elif require_test_sample and split_counts["test"] < 1:
            reason = "missing_test_sample"
        if reason:
            label_reasons[label] = reason
        else:
            eligible_labels.append(label)
    return eligible_labels, label_reasons


def prepare_training_manifest(
    source: Path,
    splits: Path,
    processed_dir: Path,
    output: Path,
    report_json: Path,
    report_csv: Path,
    *,
    min_samples_per_class: int = 3,
    require_train_sample: bool = True,
    require_validation_sample: bool = True,
    require_test_sample: bool = False,
    smoke_max_classes: int = 5,
    smoke_max_samples_per_class: int = 3,
) -> dict[str, Any]:
    records = [
        item for item in load_jsonl(source) if item.get("mode") == RECOGNITION_MODE
    ]
    split_by_sha = split_assignments(splits)
    manifest_checksum = sha256_file(source)
    samples: list[dict[str, Any]] = []
    counts = Counter(str(item.get("label_key", "")) for item in records)

    for item in records:
        sha = str(item["sha256"])
        label_key = str(item.get("label_key", ""))
        cache_path = processed_dir / f"{sha}.npz"
        processing_status, exclusion_reason, sequence_length = inspect_cache(
            cache_path, sha
        )
        split = split_by_sha.get(sha)
        if not label_key:
            exclusion_reason = "invalid_or_empty_label_key"
        elif split is None:
            exclusion_reason = "missing_split_assignment"
        elif processing_status != "processed":
            pass
        else:
            exclusion_reason = ""
        samples.append(
            {
                "source_sha256": sha,
                "source_path": item["current_relative_path"],
                "normalized_label_ar": item.get("normalized_label_ar", ""),
                "label_key": label_key,
                "split": split,
                "processed_landmark_path": cache_path.as_posix(),
                "sequence_length": sequence_length,
                "processing_status": processing_status,
                "exclusion_reason": exclusion_reason,
                "dataset_manifest_checksum": manifest_checksum,
                "eligible": False,
            }
        )

    processed_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        if (
            sample["processing_status"] == "processed"
            and sample["exclusion_reason"] == ""
        ):
            processed_by_label[str(sample["label_key"])].append(sample)

    eligible_labels, label_reasons = evaluate_label_eligibility(
        processed_by_label,
        min_samples_per_class=min_samples_per_class,
        require_train_sample=require_train_sample,
        require_validation_sample=require_validation_sample,
        require_test_sample=require_test_sample,
    )

    for sample in samples:
        label = str(sample["label_key"])
        if (
            label in eligible_labels
            and sample["processing_status"] == "processed"
            and sample["exclusion_reason"] == ""
        ):
            sample["eligible"] = True
        elif sample["exclusion_reason"] == "":
            sample["exclusion_reason"] = label_reasons.get(label, "class_not_eligible")

    smoke_labels = sorted(
        eligible_labels,
        key=lambda label: (-len(processed_by_label[label]), label),
    )[:smoke_max_classes]
    smoke_subset: dict[str, list[str]] = {}
    for label in smoke_labels:
        ordered = sorted(
            processed_by_label[label], key=lambda sample: str(sample["source_sha256"])
        )
        smoke_subset[label] = [
            str(sample["source_sha256"])
            for sample in ordered[:smoke_max_samples_per_class]
        ]

    label_index = {label: index for index, label in enumerate(sorted(eligible_labels))}
    processing_status_counts = Counter(
        str(sample["processing_status"]) for sample in samples
    )
    sample_exclusion_reason_counts = Counter(
        str(sample["exclusion_reason"]) or "eligible" for sample in samples
    )
    policy_reports: dict[str, dict[str, Any]] = {}
    for policy_min_samples in (2, 3, 5):
        policy_labels, policy_reasons = evaluate_label_eligibility(
            processed_by_label,
            min_samples_per_class=policy_min_samples,
            require_train_sample=require_train_sample,
            require_validation_sample=require_validation_sample,
            require_test_sample=require_test_sample,
        )
        policy_reports[str(policy_min_samples)] = {
            "minimum_samples_per_class": policy_min_samples,
            "eligible_label_count": len(policy_labels),
            "eligible_sample_count": sum(
                len(processed_by_label[label]) for label in policy_labels
            ),
            "eligible_labels": policy_labels,
            "excluded_label_count": max(
                len(processed_by_label) - len(policy_labels), 0
            ),
            "label_exclusion_reason_counts": dict(
                sorted(Counter(policy_reasons.values()).items())
            ),
        }
    report = {
        "total_videos": len(records),
        "processed_videos": processing_status_counts["processed"],
        "unprocessed_videos": len(records) - processing_status_counts["processed"],
        "total_normalized_labels": len(counts),
        "processed_normalized_labels": len(processed_by_label),
        "eligible_labels": len(eligible_labels),
        "eligible_label_keys": eligible_labels,
        "eligible_samples": len([sample for sample in samples if sample["eligible"]]),
        "excluded_labels": len(counts) - len(eligible_labels),
        "singleton_labels": sum(1 for count in counts.values() if count == 1),
        "two_sample_labels": sum(1 for count in counts.values() if count == 2),
        "processing_status_counts": dict(sorted(processing_status_counts.items())),
        "sample_exclusion_reason_counts": dict(
            sorted(sample_exclusion_reason_counts.items())
        ),
        "label_exclusion_reason_counts": dict(
            sorted(Counter(label_reasons.values()).items())
        ),
        "eligibility_by_min_samples": policy_reports,
        "samples_per_eligible_label": {
            label: len(processed_by_label[label]) for label in eligible_labels
        },
        "smoke_subset_labels": smoke_labels,
        "smoke_subset_sample_counts": {
            label: len(values) for label, values in smoke_subset.items()
        },
        "policy": {
            "minimum_samples_per_class": min_samples_per_class,
            "require_train_sample": require_train_sample,
            "require_validation_sample": require_validation_sample,
            "require_test_sample": require_test_sample,
        },
    }
    manifest = {
        "dataset_version": "mosl-word-isolated-v1",
        "source_dataset_version": "source-import-v1",
        "recognition_mode": RECOGNITION_MODE,
        "landmark_schema_version": SCHEMA_VERSION,
        "dataset_manifest_checksum": manifest_checksum,
        "label_index": label_index,
        "eligible_samples": [
            sample["source_sha256"] for sample in samples if sample["eligible"]
        ],
        "smoke_subset": smoke_subset,
        "samples": samples,
        "eligibility_report": report,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with report_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "label_key",
                "source_samples",
                "processed_samples",
                "eligible",
                "exclusion_reason",
            ],
        )
        writer.writeheader()
        for label in sorted(counts):
            reason = (
                ""
                if label in eligible_labels
                else label_reasons.get(label, "class_not_eligible")
            )
            writer.writerow(
                {
                    "label_key": label,
                    "source_samples": counts[label],
                    "processed_samples": len(processed_by_label.get(label, [])),
                    "eligible": label in eligible_labels,
                    "exclusion_reason": reason,
                }
            )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a MoSL word training manifest."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/manifests/videos.jsonl"),
    )
    parser.add_argument(
        "--splits",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/splits"),
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/processed/landmarks"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/datasets/mosl-word-isolated-v1/manifest.json"),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("artifacts/reports/mosl-class-eligibility.json"),
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        default=Path("artifacts/reports/mosl-class-eligibility.csv"),
    )
    parser.add_argument("--min-samples-per-class", type=int, default=3)
    parser.add_argument("--smoke-max-classes", type=int, default=5)
    parser.add_argument("--smoke-max-samples-per-class", type=int, default=3)
    args = parser.parse_args()
    manifest = prepare_training_manifest(
        args.source,
        args.splits,
        args.processed_dir,
        args.output,
        args.report_json,
        args.report_csv,
        min_samples_per_class=args.min_samples_per_class,
        smoke_max_classes=args.smoke_max_classes,
        smoke_max_samples_per_class=args.smoke_max_samples_per_class,
    )
    print(
        json.dumps(
            {
                "output": args.output.as_posix(),
                "eligible_labels": len(manifest["label_index"]),
                "eligible_samples": len(manifest["eligible_samples"]),
                "smoke_subset_labels": list(manifest["smoke_subset"].keys()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
