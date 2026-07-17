from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ml.datasets.manifest import ManifestItem, load_manifest, manifest_items
from ml.preprocessing.feature_selection import FEATURE_COUNT, MASK_FEATURE_COUNT, TARGET_FRAMES
from ml.preprocessing.normalization import normalize_training_sequence
from ml.preprocessing.sampling import resample_sequence


@dataclass(frozen=True)
class SequenceSample:
    recording_id: str
    label: str
    contributor_public_id: str
    split: str
    features: np.ndarray
    presence_mask: np.ndarray


def _load_landmarks(path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    frames = payload.get("frames", [])
    features = np.asarray([frame["features"] for frame in frames], dtype=np.float32)
    mask = np.asarray([frame["presence_mask"] for frame in frames], dtype=np.float32)
    if features.ndim != 2 or features.shape[1] != FEATURE_COUNT:
        raise ValueError(f"features must have shape [frames, {FEATURE_COUNT}]")
    if mask.ndim != 2 or mask.shape[1] != MASK_FEATURE_COUNT:
        raise ValueError(f"presence_mask must have shape [frames, {MASK_FEATURE_COUNT}]")
    return features, mask


def load_samples(
    manifest_path: Path = Path("artifacts/datasets/manifest.json"),
    landmark_root: Path = Path("artifacts/landmarks"),
    splits: set[str] | None = None,
) -> list[SequenceSample]:
    samples: list[SequenceSample] = []
    for item in manifest_items(load_manifest(manifest_path)):
        if splits and item.split not in splits:
            continue
        features, mask = _load_landmarks(landmark_root / item.landmark_object_key)
        features = resample_sequence(normalize_training_sequence(features, mask), TARGET_FRAMES)
        mask = resample_sequence(mask, TARGET_FRAMES)
        samples.append(
            SequenceSample(
                recording_id=item.recording_id,
                label=item.sign_code,
                contributor_public_id=item.contributor_public_id,
                split=item.split,
                features=features,
                presence_mask=mask,
            )
        )
    return samples


def labels_from_items(items: list[ManifestItem]) -> list[str]:
    return sorted({item.sign_code for item in items})
