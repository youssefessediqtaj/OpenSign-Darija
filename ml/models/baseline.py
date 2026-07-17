from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ml.datasets.dataset_loader import SequenceSample
from ml.preprocessing.masking import frame_mask_from_presence, masked_mean


class CentroidBaseline:
    def __init__(self) -> None:
        self.centroids: dict[str, np.ndarray] = {}

    def fit(self, samples: list[SequenceSample]) -> None:
        grouped: dict[str, list[np.ndarray]] = {}
        for sample in samples:
            grouped.setdefault(sample.label, []).append(
                masked_mean(sample.features, frame_mask_from_presence(sample.presence_mask))
            )
        self.centroids = {
            label: np.stack(values).mean(axis=0).astype(np.float32)
            for label, values in grouped.items()
        }

    def predict(self, sample: SequenceSample) -> list[tuple[str, float]]:
        vector = masked_mean(sample.features, frame_mask_from_presence(sample.presence_mask))
        distances = {
            label: float(np.linalg.norm(vector - centroid))
            for label, centroid in self.centroids.items()
        }
        ordered = sorted(distances.items(), key=lambda item: item[1])
        inv = np.asarray([1.0 / max(distance, 1e-6) for _, distance in ordered], dtype=np.float32)
        probs = inv / max(float(inv.sum()), 1e-6)
        return [(label, float(prob)) for (label, _), prob in zip(ordered, probs, strict=False)]

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps({label: value.tolist() for label, value in self.centroids.items()}, indent=2)
            + "\n",
            encoding="utf-8",
        )
