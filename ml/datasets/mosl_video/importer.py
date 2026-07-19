from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from ml.datasets.mosl_video.categories import CATEGORIES
from ml.datasets.mosl_video.manifest import (
    build_records,
    manifest_checksum,
    write_outputs,
)


ORIGINAL_DATASET_PREFIX = "-".join(("vedios", "dataset"))


def copy_dataset(source_root: Path, destination_raw_root: Path) -> None:
    source_root = source_root.resolve()
    destination_raw_root.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        source_folder = source_root / category.source_folder
        destination_folder = destination_raw_root / category.source_folder
        destination_folder.mkdir(parents=True, exist_ok=True)
        if not source_folder.exists():
            continue
        for source_path in sorted(source_folder.iterdir(), key=lambda item: item.name):
            if not source_path.is_file() or source_path.suffix.lower() != ".mp4":
                continue
            destination_path = destination_folder / source_path.name
            if (
                destination_path.exists()
                and destination_path.stat().st_size == source_path.stat().st_size
            ):
                continue
            shutil.copy2(source_path, destination_path)


def compare_records(
    source_records: list[dict[str, Any]], destination_records: list[dict[str, Any]]
) -> dict[str, Any]:
    source_by_original = {
        str(item["original_relative_path"]): item for item in source_records
    }
    destination_by_original = {
        str(item["original_relative_path"]): item for item in destination_records
    }
    missing = sorted(set(source_by_original) - set(destination_by_original))
    unexpected = sorted(set(destination_by_original) - set(source_by_original))
    checksum_mismatches = sorted(
        key
        for key in set(source_by_original) & set(destination_by_original)
        if source_by_original[key]["sha256"] != destination_by_original[key]["sha256"]
    )
    matching_checksums = sum(
        1
        for key in set(source_by_original) & set(destination_by_original)
        if source_by_original[key]["sha256"] == destination_by_original[key]["sha256"]
    )
    return {
        "source_video_count": len(source_records),
        "destination_video_count": len(destination_records),
        "matching_checksum_count": matching_checksums,
        "missing_file_count": len(missing),
        "unexpected_file_count": len(unexpected),
        "checksum_mismatch_count": len(checksum_mismatches),
        "missing_files": missing,
        "unexpected_files": unexpected,
        "checksum_mismatches": checksum_mismatches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import the local MoSL dataset into native layout."
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to a local MoSL source video folder or archive extraction.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset"),
    )
    args = parser.parse_args()

    raw_root = args.destination / "raw"
    manifest_dir = args.destination / "manifests"
    report_dir = args.destination / "reports"
    for folder in [
        raw_root,
        manifest_dir,
        args.destination / "processed/landmarks",
        args.destination / "processed/sequences",
        args.destination / "splits",
        report_dir,
        args.destination / "quarantine",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    source_records = build_records(
        args.source,
        current_prefix=ORIGINAL_DATASET_PREFIX,
        original_prefix=ORIGINAL_DATASET_PREFIX,
    )
    copy_dataset(args.source, raw_root)
    destination_records = build_records(
        raw_root,
        current_prefix="raw",
        original_prefix=ORIGINAL_DATASET_PREFIX,
    )
    summary = write_outputs(destination_records, manifest_dir)
    summary["manifest_sha256"] = manifest_checksum(manifest_dir / "videos.jsonl")
    (manifest_dir / "dataset-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    comparison = compare_records(source_records, destination_records)
    report = {
        **comparison,
        "total_size_before": sum(int(item["size_bytes"]) for item in source_records),
        "total_size_after": sum(
            int(item["size_bytes"]) for item in destination_records
        ),
        "corrupt_or_unreadable_video_count": summary[
            "corrupt_or_unreadable_video_count"
        ],
        "duplicate_checksum_count": summary["duplicate_checksum_count"],
        "manifest_sha256": summary["manifest_sha256"],
    }
    report_path = report_dir / "dataset-import-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme = args.destination / "README.md"
    if not readme.exists():
        readme.write_text(
            "# MoSL Video Dataset\n\n"
            "Local private copy of the Moroccan Sign Language video dataset imported "
            "from a verified local source.\n\n"
            "Raw videos are intentionally kept out of Git. Use `make ml-dataset-scan` "
            "to regenerate manifests after local changes.\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
