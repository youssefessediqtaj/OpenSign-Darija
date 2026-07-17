from __future__ import annotations

import numpy as np


def add_landmark_noise(features: np.ndarray, *, seed: int, std: float = 0.005) -> np.ndarray:
    if std <= 0:
        return features.astype(np.float32, copy=True)
    rng = np.random.default_rng(seed)
    return (features + rng.normal(0.0, std, size=features.shape)).astype(np.float32)


def temporal_dropout(mask: np.ndarray, *, seed: int, probability: float = 0.05) -> np.ndarray:
    if not 0 <= probability <= 0.25:
        raise ValueError("temporal dropout probability must be between 0 and 0.25")
    rng = np.random.default_rng(seed)
    keep = rng.random(mask.shape[0]) >= probability
    output = mask.copy()
    output[~keep] = 0
    return output
