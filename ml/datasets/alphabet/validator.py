from __future__ import annotations

import argparse
import csv
from pathlib import Path


def validate_manifest(path: Path) -> dict[str, object]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    errors = []
    if not rows:
        errors.append("alphabet manifest is empty")
    if any(row.get("license") in {"", "UNCONFIRMED"} for row in rows):
        errors.append("alphabet license is not verified; training must stay disabled")
    unreviewed = [row for row in rows if row.get("review_status") == "REQUIRES_LINGUISTIC_REVIEW"]
    return {"valid": not errors, "errors": errors, "rows": len(rows), "unreviewed_labels": len(unreviewed)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/processed/alphabet/manifest.csv")
    args = parser.parse_args()
    print(validate_manifest(Path(args.manifest)))


if __name__ == "__main__":
    main()
