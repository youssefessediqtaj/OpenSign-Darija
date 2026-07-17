from __future__ import annotations

import numpy as np


def validate_finite(features: np.ndarray) -> None:
    if not np.isfinite(features).all():
        raise ValueError("features contain NaN or infinite values")


def to_float32(features: np.ndarray) -> np.ndarray:
    output = features.astype(np.float32, copy=False)
    validate_finite(output)
    return output


def normalize_training_sequence(features: np.ndarray, presence_mask: np.ndarray) -> np.ndarray:
    output = to_float32(features)
    if presence_mask.shape[0] != output.shape[0]:
        raise ValueError("presence_mask and features frame counts differ")
    output = output.copy()
    missing = presence_mask.repeat(3, axis=1) == 0
    if missing.shape == output.shape:
        output[missing] = 0.0
    return output
