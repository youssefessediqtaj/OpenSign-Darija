from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ml.datasets.mosl_video.importer import compare_records
from ml.datasets.mosl_video.manifest import build_records


ORIGINAL_DATASET_PREFIX = "-".join(("vedios", "dataset"))


def build_verification(source_root: Path, destination_root: Path) -> dict[str, Any]:
    source_records = build_records(
        source_root,
        current_prefix=ORIGINAL_DATASET_PREFIX,
        original_prefix=ORIGINAL_DATASET_PREFIX,
    )
    destination_records = build_records(
        destination_root / "raw",
        current_prefix="raw",
        original_prefix=ORIGINAL_DATASET_PREFIX,
    )
    source_by_original = {
        str(item["original_relative_path"]): item for item in source_records
    }
    destination_by_original = {
        str(item["original_relative_path"]): item for item in destination_records
    }
    rows: list[dict[str, Any]] = []
    for key in sorted(set(source_by_original) | set(destination_by_original)):
        source = source_by_original.get(key)
        destination = destination_by_original.get(key)
        if source is None:
            status = "unexpected"
        elif destination is None:
            status = "missing"
        elif source["sha256"] != destination["sha256"]:
            status = "checksum_mismatch"
        else:
            status = "matched"
        rows.append(
            {
                "status": status,
                "original_relative_path": key,
                "source_current_path": source.get("current_relative_path", "")
                if source
                else "",
                "destination_current_path": destination.get("current_relative_path", "")
                if destination
                else "",
                "source_sha256": source.get("sha256", "") if source else "",
                "destination_sha256": destination.get("sha256", "")
                if destination
                else "",
                "source_size_bytes": source.get("size_bytes", "") if source else "",
                "destination_size_bytes": destination.get("size_bytes", "")
                if destination
                else "",
                "category": (destination or source or {}).get("category", ""),
                "mode": (destination or source or {}).get("mode", ""),
                "label_key": (destination or source or {}).get("label_key", ""),
                "original_filename": (destination or source or {}).get(
                    "original_filename", ""
                ),
            }
        )
    comparison = compare_records(source_records, destination_records)
    comparison["matched_row_count"] = sum(
        1 for row in rows if row["status"] == "matched"
    )
    comparison["total_source_size_bytes"] = sum(
        int(item["size_bytes"]) for item in source_records
    )
    comparison["total_destination_size_bytes"] = sum(
        int(item["size_bytes"]) for item in destination_records
    )
    return {
        "summary": {
            **comparison,
            "valid": (
                comparison["source_video_count"] == 2216
                and comparison["destination_video_count"] == 2216
                and comparison["matching_checksum_count"] == 2216
                and comparison["missing_file_count"] == 0
                and comparison["unexpected_file_count"] == 0
                and comparison["checksum_mismatch_count"] == 0
            ),
        },
        "items": rows,
    }


def write_outputs(report: dict[str, Any], json_output: Path, csv_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fieldnames = list(report["items"][0].keys()) if report["items"] else ["status"]
    with csv_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report["items"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify source-to-native MoSL video migration."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Path to the source video folder used for checksum comparison.",
    )
    parser.add_argument(
        "--destination-root",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "ml/data/external/mosl-video-dataset/reports/migration-verification.json"
        ),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path(
            "ml/data/external/mosl-video-dataset/reports/migration-verification.csv"
        ),
    )
    args = parser.parse_args()
    report = build_verification(args.source_root, args.destination_root)
    write_outputs(report, args.json_output, args.csv_output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    if not report["summary"]["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
