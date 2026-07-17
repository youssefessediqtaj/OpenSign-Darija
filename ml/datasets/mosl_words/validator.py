from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def validate_manifest(path: Path) -> dict[str, object]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    labels = Counter(row.get("normalized_arabic_label", "") for row in rows)
    signer_known = sum(1 for row in rows if row.get("signer_id"))
    errors = []
    if not rows:
        errors.append("word manifest is empty")
    if any(row.get("license") != "CC-BY-4.0" for row in rows):
        errors.append("unexpected license in word manifest")
    return {
        "valid": not errors,
        "errors": errors,
        "rows": len(rows),
        "labels": len(labels),
        "known_signer_rows": signer_known,
        "signer_independent_claim_allowed": signer_known == len(rows) and bool(rows),
        "single_sample_labels": sum(1 for count in labels.values() if count == 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/processed/words/manifest.csv")
    args = parser.parse_args()
    print(validate_manifest(Path(args.manifest)))


if __name__ == "__main__":
    main()
