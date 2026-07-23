from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset, WeightedRandomSampler


EXPECTED_LANDMARK_SHAPE = (60, 75, 3)
EXPECTED_MASK_SHAPE = (60, 75)


@dataclass(frozen=True)
class LandmarkSample:
    sha256: str
    label_key: str
    label_index: int
    split: str
    path: Path


def _seed_for(seed: int, epoch: int, checksum: str) -> int:
    digest = hashlib.sha256(f"{seed}:{epoch}:{checksum}".encode()).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def load_landmarks(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        landmarks = data["landmarks"].astype(np.float32)
        presence_mask = data["presence_mask"].astype(np.float32)
    if landmarks.shape != EXPECTED_LANDMARK_SHAPE:
        raise ValueError(f"{path} landmarks must have shape 60 x 75 x 3")
    if presence_mask.shape != EXPECTED_MASK_SHAPE:
        raise ValueError(f"{path} presence_mask must have shape 60 x 75")
    if not np.isfinite(landmarks).all() or not np.isfinite(presence_mask).all():
        raise ValueError(f"{path} contains NaN or infinity")
    return landmarks, presence_mask


def temporal_resample(sequence: np.ndarray, target_frames: int = 60) -> np.ndarray:
    if sequence.ndim != 3 or sequence.shape[1:] != (75, 3):
        raise ValueError("sequence must have shape [frames, 75, 3]")
    if sequence.shape[0] < 2:
        raise ValueError("sequence must contain at least two frames")
    source = np.linspace(0.0, 1.0, sequence.shape[0])
    target = np.linspace(0.0, 1.0, target_frames)
    flat = sequence.reshape(sequence.shape[0], -1)
    result = np.stack(
        [np.interp(target, source, flat[:, column]) for column in range(flat.shape[1])],
        axis=1,
    )
    return result.reshape(target_frames, 75, 3).astype(np.float32)


def augment_landmarks(
    landmarks: np.ndarray,
    presence_mask: np.ndarray,
    *,
    seed: int,
) -> np.ndarray:
    if landmarks.shape != EXPECTED_LANDMARK_SHAPE or presence_mask.shape != EXPECTED_MASK_SHAPE:
        raise ValueError("augmentation expects 60 x 75 x 3 landmarks and 60 x 75 mask")
    rng = np.random.default_rng(seed)
    output = landmarks.astype(np.float32, copy=True)

    stretch = float(rng.uniform(0.9, 1.1))
    intermediate_frames = max(48, min(72, int(round(60 * stretch))))
    output = temporal_resample(output, target_frames=intermediate_frames)
    output = temporal_resample(output, target_frames=60)

    drop_count = int(rng.integers(0, 5))
    if drop_count:
        dropped = sorted(rng.choice(np.arange(1, 59), size=drop_count, replace=False).tolist())
        for frame in dropped:
            output[frame] = (output[frame - 1] + output[frame + 1]) / 2.0

    scale = float(rng.uniform(0.96, 1.04))
    translation = rng.uniform(-0.02, 0.02, size=(1, 1, 3)).astype(np.float32)
    noise = rng.normal(0.0, 0.003, size=output.shape).astype(np.float32)
    output = output * scale + translation + noise
    output[presence_mask == 0] = 0.0
    return output.astype(np.float32)


class MoslLandmarkDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(
        self,
        samples: list[LandmarkSample],
        *,
        augment: bool = False,
        seed: int = 42,
    ) -> None:
        self.samples = samples
        self.augment = augment
        self.seed = seed
        self.epoch = 0

    def __len__(self) -> int:
        return len(self.samples)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[index]
        landmarks, mask = load_landmarks(sample.path)
        if self.augment:
            landmarks = augment_landmarks(
                landmarks,
                mask,
                seed=_seed_for(self.seed, self.epoch, sample.sha256),
            )
        return torch.from_numpy(landmarks), torch.tensor(sample.label_index, dtype=torch.long)


def samples_from_split_report(
    path: Path,
) -> tuple[dict[str, int], dict[str, list[LandmarkSample]]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    label_index = {str(key): int(value) for key, value in report["label_index"].items()}
    output: dict[str, list[LandmarkSample]] = {
        "train": [],
        "validation": [],
        "test": [],
        "unknown_calibration": [],
        "unknown_test": [],
    }
    for item in report["assignments"]:
        split = str(item["split"])
        output[split].append(
            LandmarkSample(
                sha256=str(item["sha256"]),
                label_key=str(item["label_key"]),
                label_index=label_index[str(item["label_key"])],
                split=split,
                path=Path(item["processed_landmark_path"]),
            )
        )
    for key in ("unknown_calibration", "unknown_test"):
        for item in report[key]:
            output[key].append(
                LandmarkSample(
                    sha256=str(item["sha256"]),
                    label_key=str(item["label_key"]),
                    label_index=-1,
                    split=key,
                    path=Path(item["processed_landmark_path"]),
                )
            )
    for values in output.values():
        values.sort(key=lambda sample: (sample.label_key, sample.sha256))
    return label_index, output


def class_weights(samples: list[LandmarkSample], class_count: int) -> torch.Tensor:
    counts = np.bincount([sample.label_index for sample in samples], minlength=class_count)
    if (counts == 0).any():
        raise ValueError("every class must have a training sample")
    weights = len(samples) / (class_count * counts.astype(np.float64))
    return torch.tensor(weights, dtype=torch.float32)


def balanced_sampler(samples: list[LandmarkSample], *, seed: int) -> WeightedRandomSampler:
    counts: dict[int, int] = {}
    for sample in samples:
        counts[sample.label_index] = counts.get(sample.label_index, 0) + 1
    sample_weights = [1.0 / counts[sample.label_index] for sample in samples]
    generator = torch.Generator().manual_seed(seed)
    return WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(samples),
        replacement=True,
        generator=generator,
    )


def split_report_summary(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return {
        "valid": report["valid"],
        "seed": report["seed"],
        "counts": report["counts"],
        "supported_labels": report["supported_labels"],
        "signer_independent": report["signer_independent"],
        "dataset_manifest_checksum_sha256": report["dataset_manifest_checksum_sha256"],
    }
