from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ml.datasets.mosl_video.categories import (
    CATEGORY_BY_FOLDER,
    CATEGORIES,
    DATASET_SOURCE,
    DATASET_VERSION,
)
from ml.datasets.mosl_video.label_parser import parse_mosl_label
from ml.datasets.mosl_video.video_inspector import inspect_video, is_video_path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {path}") from exc


def discover_videos(root: Path) -> list[Path]:
    paths: list[Path] = []
    for category in CATEGORIES:
        folder = root / category.source_folder
        if not folder.exists():
            continue
        paths.extend(path for path in folder.iterdir() if is_video_path(path))
    return sorted(paths, key=lambda item: item.relative_to(root).as_posix())


def build_records(
    root: Path, current_prefix: str = "", original_prefix: str = ""
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in discover_videos(root):
        relative = safe_relative(path, root)
        category = CATEGORY_BY_FOLDER[relative.parts[0]]
        parsed = parse_mosl_label(path.name)
        info = inspect_video(path)
        checksum = sha256_file(path)
        current_relative_path = (
            f"{current_prefix.rstrip('/')}/{relative.as_posix()}".lstrip("/")
        )
        original_relative_path = (
            f"{original_prefix.rstrip('/')}/{relative.as_posix()}".lstrip("/")
        )
        errors = list(info["validation_errors"])
        if not parsed.label_key:
            errors.append("label_parse_empty")
        records.append(
            {
                "dataset_source": DATASET_SOURCE,
                "dataset_version": DATASET_VERSION,
                "mode": category.mode,
                "category": category.display_name,
                "original_relative_path": original_relative_path,
                "current_relative_path": current_relative_path,
                "original_filename": path.name,
                "raw_label": parsed.raw_label,
                "normalized_label_ar": parsed.normalized_label_ar,
                "label_key": parsed.label_key,
                "variant_index": parsed.variant_index,
                "extension": path.suffix.lower(),
                "sha256": checksum,
                "size_bytes": path.stat().st_size,
                "duration_seconds": info["duration_seconds"],
                "fps": info["fps"],
                "frame_count": info["frame_count"],
                "width": info["width"],
                "height": info["height"],
                "readable": info["readable"],
                "validation_errors": errors,
                "split": None,
            }
        )
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(str(item["category"]) for item in records)
    mode_counts = Counter(str(item["mode"]) for item in records)
    label_counts = Counter(str(item["label_key"]) for item in records)
    checksum_counts = Counter(str(item["sha256"]) for item in records)
    duplicate_checksums = {
        key: value for key, value in checksum_counts.items() if value > 1
    }
    errors_by_reason: dict[str, int] = defaultdict(int)
    for record in records:
        for error in record["validation_errors"]:
            errors_by_reason[str(error)] += 1
    return {
        "dataset_source": DATASET_SOURCE,
        "dataset_version": DATASET_VERSION,
        "video_count": len(records),
        "total_size_bytes": sum(int(item["size_bytes"]) for item in records),
        "readable_video_count": sum(1 for item in records if item["readable"]),
        "corrupt_or_unreadable_video_count": sum(
            1 for item in records if not item["readable"]
        ),
        "invalid_label_count": sum(
            1 for item in records if "label_parse_empty" in item["validation_errors"]
        ),
        "duplicate_checksum_count": sum(
            value - 1 for value in duplicate_checksums.values()
        ),
        "unique_checksum_count": len(checksum_counts),
        "unique_normalized_label_count": len(label_counts),
        "singleton_class_count": sum(
            1 for value in label_counts.values() if value == 1
        ),
        "category_counts": dict(sorted(category_counts.items())),
        "mode_counts": dict(sorted(mode_counts.items())),
        "duplicate_checksums": duplicate_checksums,
        "validation_errors": dict(sorted(errors_by_reason.items())),
    }


def write_outputs(records: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(records)
    jsonl_path = output_dir / "videos.jsonl"
    csv_path = output_dir / "videos.csv"
    labels_path = output_dir / "labels.json"
    categories_path = output_dir / "categories.json"
    summary_path = output_dir / "dataset-summary.json"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    fieldnames = list(records[0].keys()) if records else ["dataset_source"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["validation_errors"] = "|".join(
                str(item) for item in record["validation_errors"]
            )
            writer.writerow(row)

    labels: dict[str, dict[str, Any]] = {}
    for record in records:
        label_key = str(record["label_key"])
        item = labels.setdefault(
            label_key,
            {
                "label_key": label_key,
                "display_labels": sorted({str(record["normalized_label_ar"])}),
                "raw_labels": sorted({str(record["raw_label"])}),
                "modes": sorted({str(record["mode"])}),
                "categories": sorted({str(record["category"])}),
                "sample_count": 0,
            },
        )
        item["sample_count"] += 1
        item["display_labels"] = sorted(
            set(item["display_labels"]) | {str(record["normalized_label_ar"])}
        )
        item["raw_labels"] = sorted(
            set(item["raw_labels"]) | {str(record["raw_label"])}
        )
        item["modes"] = sorted(set(item["modes"]) | {str(record["mode"])})
        item["categories"] = sorted(set(item["categories"]) | {str(record["category"])})

    labels_path.write_text(
        json.dumps(list(labels.values()), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    categories_path.write_text(
        json.dumps([asdict(item) for item in CATEGORIES], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def manifest_checksum(path: Path) -> str:
    return sha256_file(path)
