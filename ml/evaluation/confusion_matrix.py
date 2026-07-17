from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def write_confusion_matrix(matrix: np.ndarray, labels: list[str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "confusion_matrix.json").write_text(
        json.dumps({"labels": labels, "matrix": matrix.tolist()}, indent=2) + "\n"
    )
    with (output_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true/pred", *labels])
        for label, row in zip(labels, matrix.tolist(), strict=False):
            writer.writerow([label, *row])
