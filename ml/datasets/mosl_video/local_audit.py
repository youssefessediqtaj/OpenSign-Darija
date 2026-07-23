from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import unicodedata

import numpy as np

from ml.datasets.mosl_video.preprocess import PREPROCESSING_VERSION
from ml.preprocessing.landmark_schema_v1 import SCHEMA_VERSION


DATASET_ROOT = Path("ml/data/external/mosl-video-dataset")
MANIFEST_PATH = DATASET_ROOT / "manifests/videos.jsonl"
PROCESSED_DIR = DATASET_ROOT / "processed/landmarks"
REPORT_DIR = Path("artifacts/reports")
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
SUPPORTED = "SUPPORTED_FOR_TRAINING"
INSUFFICIENT = "INSUFFICIENT_SAMPLES"
INVALID = "INVALID"
EXCLUDED_QUALITY = "EXCLUDED_FOR_QUALITY"
AMBIGUOUS_LABEL_MAPPING_REASON = "ambiguous_label_key_multiple_arabic_displays"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_order(values: list[str], *, seed: int, namespace: str) -> list[str]:
    return sorted(
        values,
        key=lambda value: hashlib.sha256(
            f"{seed}:{namespace}:{value}".encode()
        ).hexdigest(),
    )


def inspect_cache(path: Path, source_sha256: str) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    metadata: dict[str, Any] = {}
    if not path.exists():
        return False, ["missing_processed_artifact"], metadata
    try:
        with np.load(path, allow_pickle=False) as data:
            landmarks = data["landmarks"]
            presence_mask = data["presence_mask"]
            metadata_value = json.loads(str(data["metadata"].item()))
    except Exception as exc:
        return False, [f"unreadable_processed_artifact:{exc}"], metadata
    if isinstance(metadata_value, dict):
        metadata = metadata_value
    else:
        errors.append("invalid_metadata")
    if landmarks.shape != (60, 75, 3):
        errors.append("invalid_landmark_shape")
    if presence_mask.shape != (60, 75):
        errors.append("invalid_presence_mask_shape")
    elif bool(((presence_mask < 0.0) | (presence_mask > 1.0)).any()):
        errors.append("invalid_presence_mask_values")
    if not np.isfinite(landmarks).all() or not np.isfinite(presence_mask).all():
        errors.append("non_finite_values")
    if np.count_nonzero(landmarks) == 0:
        errors.append("all_zero_sequence")
    if presence_mask.shape == (60, 75) and float(presence_mask[:, 33:].sum()) == 0.0:
        errors.append("hands_missing_throughout")
    if metadata.get("source_sha256") != source_sha256:
        errors.append("processed_source_checksum_mismatch")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("obsolete_or_invalid_schema_version")
    if metadata.get("preprocessing_version") != PREPROCESSING_VERSION:
        errors.append("obsolete_preprocessing_version")
    if (
        metadata.get("frames"),
        metadata.get("landmarks_per_frame"),
        metadata.get("coordinates"),
    ) != (60, 75, 3):
        errors.append("incompatible_preprocessing_dimensions")
    return not errors, errors, metadata


def _representative_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(records, key=lambda item: str(item["current_relative_path"]))[0]


def _split_supported_samples(
    samples_by_label: dict[str, list[dict[str, Any]]],
    *,
    seed: int,
    minimum_samples: int,
) -> tuple[dict[str, str], list[str]]:
    assignments: dict[str, str] = {}
    supported_labels: list[str] = []
    for label, samples in sorted(samples_by_label.items()):
        unique = {str(item["sha256"]): item for item in samples}
        if len(unique) < minimum_samples:
            continue
        ordered = stable_order(list(unique), seed=seed, namespace=f"supported:{label}")
        validation_count = max(1, round(len(ordered) * 0.2))
        test_count = max(1, round(len(ordered) * 0.2))
        train_count = len(ordered) - validation_count - test_count
        if train_count < 1:
            continue
        supported_labels.append(label)
        for checksum in ordered[:train_count]:
            assignments[checksum] = "train"
        for checksum in ordered[train_count : train_count + validation_count]:
            assignments[checksum] = "validation"
        for checksum in ordered[train_count + validation_count :]:
            assignments[checksum] = "test"
    return assignments, supported_labels


def _unknown_pools(
    samples_by_label: dict[str, list[dict[str, Any]]],
    supported_labels: set[str],
    *,
    seed: int,
    per_split: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = stable_order(
        [label for label in samples_by_label if label not in supported_labels],
        seed=seed,
        namespace="unknown-labels",
    )
    calibration_labels = labels[:per_split]
    test_labels = labels[per_split : per_split * 2]

    def select(selected_labels: list[str], namespace: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for label in selected_labels:
            unique = {str(item["sha256"]): item for item in samples_by_label[label]}
            ordered = stable_order(list(unique), seed=seed, namespace=f"{namespace}:{label}")
            if ordered:
                record = unique[ordered[0]]
                output.append(
                    {
                        "sha256": ordered[0],
                        "label_key": label,
                        "processed_landmark_path": record["processed_landmark_path"],
                    }
                )
        return output

    return select(calibration_labels, "unknown-calibration"), select(
        test_labels, "unknown-test"
    )


def build_local_audit(
    *,
    dataset_root: Path = DATASET_ROOT,
    manifest_path: Path = MANIFEST_PATH,
    processed_dir: Path = PROCESSED_DIR,
    report_dir: Path = REPORT_DIR,
    minimum_samples: int = 5,
    seed: int = 42,
    unknown_samples_per_split: int = 64,
    verify_raw_checksums: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if minimum_samples < 3:
        raise ValueError("minimum_samples must never be below three")
    records = load_records(manifest_path)
    manifest_checksum = sha256_file(manifest_path)
    by_checksum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_checksum[str(record["sha256"])].append(record)
    duplicate_groups = {
        checksum: items for checksum, items in by_checksum.items() if len(items) > 1
    }
    ambiguous_checksums = {
        checksum
        for checksum, items in duplicate_groups.items()
        if len({str(item.get("label_key", "")) for item in items}) > 1
    }
    display_counts_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        label = str(record.get("label_key", ""))
        display = unicodedata.normalize(
            "NFC", str(record.get("normalized_label_ar", "")).strip()
        )
        if label and display:
            display_counts_by_label[label][display] += 1
    ambiguous_label_mappings = {
        label: sorted(display_counts)
        for label, display_counts in display_counts_by_label.items()
        if len(display_counts) > 1
    }

    cache_results: dict[str, tuple[bool, list[str], dict[str, Any]]] = {}
    raw_errors: dict[str, list[str]] = defaultdict(list)
    for checksum, items in by_checksum.items():
        cache_results[checksum] = inspect_cache(processed_dir / f"{checksum}.npz", checksum)
        if verify_raw_checksums:
            for item in items:
                path = dataset_root / str(item["current_relative_path"])
                if not path.exists():
                    raw_errors[checksum].append("missing_raw_video")
                elif sha256_file(path) != checksum:
                    raw_errors[checksum].append("raw_checksum_mismatch")

    valid_samples_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    samples_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    quality_reasons_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    for checksum, items in sorted(by_checksum.items()):
        cache_valid, cache_errors, _ = cache_results[checksum]
        for item in items:
            label = str(item.get("label_key", ""))
            reasons = [*cache_errors, *raw_errors.get(checksum, [])]
            if checksum in ambiguous_checksums:
                reasons.append("ambiguous_duplicate_checksum_labels")
            if label in ambiguous_label_mappings:
                reasons.append(AMBIGUOUS_LABEL_MAPPING_REASON)
            if reasons:
                quality_reasons_by_label[label].update(set(reasons))
                continue
            if not label:
                continue
            sample = dict(item)
            sample["processed_landmark_path"] = (
                processed_dir / f"{checksum}.npz"
            ).as_posix()
            valid_samples_by_label[label].append(sample)
            if item.get("mode") == "WORD_ISOLATED":
                samples_by_label[label].append(sample)

    split_by_checksum, supported_labels = _split_supported_samples(
        samples_by_label,
        seed=seed,
        minimum_samples=minimum_samples,
    )
    supported_set = set(supported_labels)
    unknown_calibration, unknown_test = _unknown_pools(
        samples_by_label,
        supported_set,
        seed=seed,
        per_split=unknown_samples_per_split,
    )

    records_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        records_by_label[str(record.get("label_key", ""))].append(record)
    label_rows: list[dict[str, Any]] = []
    for label, label_records in sorted(records_by_label.items()):
        analyzed_usable = {
            str(item["sha256"]): item
            for item in valid_samples_by_label.get(label, [])
        }
        usable = {str(item["sha256"]): item for item in samples_by_label.get(label, [])}
        split_counts = Counter(split_by_checksum.get(checksum) for checksum in usable)
        representative = _representative_record(label_records)
        displays = Counter(str(item.get("normalized_label_ar", "")) for item in label_records)
        display = displays.most_common(1)[0][0] if displays else ""
        categories = sorted({str(item.get("category", "")) for item in label_records})
        quality_reasons = quality_reasons_by_label.get(label, Counter())
        if not label:
            status = INVALID
            exclusion_reason = "invalid_or_empty_normalized_label"
        elif label in supported_set:
            status = SUPPORTED
            exclusion_reason = ""
        elif not usable and quality_reasons:
            status = EXCLUDED_QUALITY
            exclusion_reason = ";".join(sorted(quality_reasons))
        else:
            status = INSUFFICIENT
            exclusion_reason = (
                "separate_ALPHABET_STATIC_task_not_in_word_model"
                if representative.get("mode") != "WORD_ISOLATED"
                else f"fewer_than_{minimum_samples}_independent_usable_examples"
            )
        label_rows.append(
            {
                "label_key": label,
                "label_ar": display if label else "",
                "category": ",".join(categories),
                "mode": str(representative.get("mode", "")),
                "source_rows": len(label_records),
                "examples": len(analyzed_usable),
                "word_model_eligible_examples": len(usable),
                "training_count": split_counts["train"],
                "validation_count": split_counts["validation"],
                "test_count": split_counts["test"],
                "supported_status": status,
                "exclusion_reason": exclusion_reason,
                "quality_excluded_examples": len(
                    {
                        str(item["sha256"])
                        for item in label_records
                        if str(item["sha256"]) not in analyzed_usable
                    }
                ),
            }
        )

    assignments: list[dict[str, Any]] = []
    for label in supported_labels:
        unique = {str(item["sha256"]): item for item in samples_by_label[label]}
        for checksum, item in sorted(unique.items()):
            assignments.append(
                {
                    "sha256": checksum,
                    "label_key": label,
                    "label_ar": str(item.get("normalized_label_ar", "")),
                    "category": str(item.get("category", "")),
                    "split": split_by_checksum[checksum],
                    "processed_landmark_path": item["processed_landmark_path"],
                    "source_path": str(item["current_relative_path"]),
                }
            )
    assignment_counts = Counter(item["split"] for item in assignments)
    assigned_checksum_splits: dict[str, set[str]] = defaultdict(set)
    for item in assignments:
        assigned_checksum_splits[item["sha256"]].add(item["split"])
    leakage = {
        checksum: sorted(splits)
        for checksum, splits in assigned_checksum_splits.items()
        if len(splits) > 1
    }

    raw_files = [
        path
        for path in (dataset_root / "raw").rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    ]
    status_counts = Counter(row["supported_status"] for row in label_rows)
    invalid_artifacts = [
        {
            "sha256": checksum,
            "errors": result[1],
        }
        for checksum, result in sorted(cache_results.items())
        if not result[0]
    ]
    audit = {
        "schema_version": "OPEN_SIGNE_LOCAL_MOSL_AUDIT_V1",
        "dataset_root": dataset_root.as_posix(),
        "dataset_manifest": manifest_path.as_posix(),
        "dataset_manifest_checksum_sha256": manifest_checksum,
        "video_count": len(raw_files),
        "manifest_video_count": len(records),
        "total_video_size_bytes": sum(path.stat().st_size for path in raw_files),
        "category_counts": dict(sorted(Counter(str(r["category"]) for r in records).items())),
        "mode_counts": dict(sorted(Counter(str(r["mode"]) for r in records).items())),
        "unique_normalized_label_count_including_empty": len(records_by_label),
        "valid_nonempty_normalized_label_count": len(records_by_label) - int("" in records_by_label),
        "invalid_label_video_count": sum(1 for item in records if not item.get("label_key")),
        "duplicate_checksum_group_count": len(duplicate_groups),
        "duplicate_checksum_extra_count": sum(len(items) - 1 for items in duplicate_groups.values()),
        "ambiguous_duplicate_checksum_group_count": len(ambiguous_checksums),
        "ambiguous_label_mapping_count": len(ambiguous_label_mappings),
        "ambiguous_label_mappings": [
            {
                "label_key": label,
                "normalized_labels_ar": displays,
                "display_variant_counts": {
                    display: display_counts_by_label[label][display]
                    for display in displays
                },
                "video_count": sum(display_counts_by_label[label].values()),
                "training_decision": "EXCLUDED_FOR_QUALITY",
                "exclusion_reason": AMBIGUOUS_LABEL_MAPPING_REASON,
            }
            for label, displays in sorted(ambiguous_label_mappings.items())
        ],
        "unique_video_checksum_count": len(by_checksum),
        "processed_landmark_file_count": len(list(processed_dir.glob("*.npz"))),
        "processed_manifest_entry_count": sum(
            len(by_checksum[checksum]) for checksum, result in cache_results.items() if result[0]
        ),
        "missing_or_invalid_processed_artifact_count": len(invalid_artifacts),
        "missing_or_invalid_processed_artifacts": invalid_artifacts,
        "raw_checksum_error_count": sum(len(errors) for errors in raw_errors.values()),
        "label_classification_counts": dict(sorted(status_counts.items())),
        "minimum_supported_examples": minimum_samples,
        "supported_label_count": len(supported_labels),
        "supported_sample_count": len(assignments),
        "eligible_minimum_sample_split_counts": {
            "train": assignment_counts["train"],
            "validation": assignment_counts["validation"],
            "test": assignment_counts["test"],
            "total": len(assignments),
        },
        "eligible_split_checksum_leakage": leakage,
        "duplicate_groups": [
            {
                "sha256": checksum,
                "row_count": len(items),
                "label_keys": sorted({str(item.get("label_key", "")) for item in items}),
                "paths": sorted(str(item["current_relative_path"]) for item in items),
                "training_decision": "EXCLUDED_FOR_QUALITY"
                if checksum in ambiguous_checksums
                else "GROUPED_AS_ONE_SAMPLE",
            }
            for checksum, items in sorted(duplicate_groups.items())
        ],
        "labels": label_rows,
    }
    vocabulary = {
        "schema_version": "OPEN_SIGNE_SUPPORTED_VOCABULARY_V1",
        "dataset_manifest_checksum_sha256": manifest_checksum,
        "policy": {
            "minimum_independent_examples": minimum_samples,
            "requires_train_validation_test": True,
            "ambiguous_cross_label_duplicate_checksums_excluded": True,
            "ambiguous_label_to_arabic_mappings_excluded": True,
            "one_missing_hand_is_not_automatically_excluded": True,
        },
        "supported_label_count": len(supported_labels),
        "supported_sample_count": len(assignments),
        "labels": label_rows,
    }
    split_report = {
        "schema_version": "OPEN_SIGNE_MOSL_SPLIT_V1",
        "seed": seed,
        "dataset_manifest_checksum_sha256": manifest_checksum,
        "grouping_key": "binary_sha256",
        "stratified_by": "label_key",
        "signer_independent": False,
        "signer_limitation": (
            "Signer identity is unavailable in the local dataset manifest and filenames; "
            "the split is checksum-grouped and label-stratified but not signer-independent."
        ),
        "minimum_supported_examples": minimum_samples,
        "label_index": {label: index for index, label in enumerate(sorted(supported_labels))},
        "supported_labels": sorted(supported_labels),
        "counts": {
            "train": assignment_counts["train"],
            "validation": assignment_counts["validation"],
            "test": assignment_counts["test"],
            "total": len(assignments),
        },
        "assignments": sorted(assignments, key=lambda item: (item["split"], item["label_key"], item["sha256"])),
        "unknown_calibration": unknown_calibration,
        "unknown_test": unknown_test,
        "unknown_label_overlap": sorted(
            {item["label_key"] for item in unknown_calibration}
            & {item["label_key"] for item in unknown_test}
        ),
        "checksum_split_leakage": leakage,
        "ambiguous_duplicate_checksums_excluded": sorted(ambiguous_checksums),
        "ambiguous_label_keys_excluded": sorted(ambiguous_label_mappings),
        "valid": not leakage
        and not (set(supported_labels) & set(ambiguous_label_mappings))
        and not ({item["label_key"] for item in unknown_calibration} & {item["label_key"] for item in unknown_test}),
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "local-mosl-dataset-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (report_dir / "supported-sign-vocabulary-v1.json").write_text(
        json.dumps(vocabulary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (report_dir / "model-v1-split-report.json").write_text(
        json.dumps(split_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    csv_fields = list(label_rows[0]) if label_rows else ["label_key"]
    for name in ("local-mosl-dataset-audit.csv", "supported-sign-vocabulary-v1.csv"):
        with (report_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=csv_fields)
            writer.writeheader()
            writer.writerows(label_rows)
    return audit, vocabulary, split_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and split the local native MoSL dataset.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--minimum-samples", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-raw-checksums", action="store_true")
    args = parser.parse_args()
    audit, vocabulary, split = build_local_audit(
        dataset_root=args.dataset_root,
        manifest_path=args.manifest,
        processed_dir=args.processed_dir,
        report_dir=args.report_dir,
        minimum_samples=args.minimum_samples,
        seed=args.seed,
        verify_raw_checksums=not args.skip_raw_checksums,
    )
    print(
        json.dumps(
            {
                "video_count": audit["video_count"],
                "supported_labels": vocabulary["supported_label_count"],
                "supported_samples": vocabulary["supported_sample_count"],
                "split_counts": split["counts"],
                "valid": split["valid"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
