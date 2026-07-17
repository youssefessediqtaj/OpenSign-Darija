from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ml.datasets.alphabet.inspector import discover_images, inspect_image
from ml.datasets.alphabet.label_parser import parse_label
from ml.datasets.manifest import sha256_file


def build_manifest(root: Path, output: Path, source_id: str = "kaggle_moroccan_lsm_alphabet") -> list[dict[str, object]]:
    rows = []
    for index, path in enumerate(discover_images(root), start=1):
        label = parse_label(path, root)
        info = inspect_image(path)
        rows.append(
            {
                "sample_id": f"{source_id}_{index:08d}",
                "source_id": source_id,
                "relative_path": path.relative_to(root).as_posix(),
                "class_code": label.class_code,
                "original_label": label.original_label,
                "normalized_label": label.normalized_label,
                "image_width": info["width"],
                "image_height": info["height"],
                "image_format": info["format"],
                "checksum": sha256_file(path),
                "split": "",
                "license": "UNCONFIRMED",
                "review_status": label.review_status,
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["sample_id"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/raw/external/kaggle-lsm-alphabet/extracted")
    parser.add_argument("--output", default="data/processed/alphabet/manifest.csv")
    args = parser.parse_args()
    rows = build_manifest(Path(args.root), Path(args.output))
    print(f"alphabet manifest rows: {len(rows)}")


if __name__ == "__main__":
    main()
