from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path


def assign_splits(manifest: Path, output: Path, seed: int = 42) -> None:
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_class[row.get("class_code", "")].append(row)
    rng = random.Random(seed)
    for class_rows in by_class.values():
        rng.shuffle(class_rows)
        total = len(class_rows)
        for index, row in enumerate(class_rows):
            row["split"] = "TRAIN" if index < total * 0.7 else "VALIDATION" if index < total * 0.85 else "TEST"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["sample_id"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/processed/alphabet/manifest.csv")
    parser.add_argument("--output", default="data/processed/alphabet/manifest-with-splits.csv")
    args = parser.parse_args()
    assign_splits(Path(args.manifest), Path(args.output))


if __name__ == "__main__":
    main()
