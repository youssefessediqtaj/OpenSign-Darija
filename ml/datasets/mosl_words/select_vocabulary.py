from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def select_vocabulary(manifest: Path, minimum_samples: int, minimum_signers: int) -> dict[str, object]:
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_label[row.get("normalized_arabic_label", "")].append(row)
    trainable = []
    insufficient = []
    for label, label_rows in sorted(by_label.items()):
        signers = {row.get("signer_id", "") for row in label_rows if row.get("signer_id")}
        item = {"label": label, "samples": len(label_rows), "signers": len(signers)}
        if len(label_rows) >= minimum_samples and len(signers) >= minimum_signers:
            trainable.append(item)
        else:
            insufficient.append(item)
    return {"trainable": trainable, "insufficient": insufficient, "total_labels": len(by_label)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/processed/words/manifest.csv")
    parser.add_argument("--minimum-samples", type=int, default=20)
    parser.add_argument("--minimum-signers", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(select_vocabulary(Path(args.manifest), args.minimum_samples, args.minimum_signers), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
