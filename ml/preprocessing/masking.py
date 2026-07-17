from __future__ import annotations

import numpy as np


def frame_mask_from_presence(presence_mask: np.ndarray) -> np.ndarray:
    if presence_mask.ndim != 2:
        raise ValueError("presence_mask must have shape [frames, mask_feature_count]")
    return (presence_mask.sum(axis=1) > 0).astype(np.float32)


def masked_mean(features: np.ndarray, frame_mask: np.ndarray) -> np.ndarray:
    if features.shape[0] != frame_mask.shape[0]:
        raise ValueError("features and frame_mask lengths differ")
    weights = frame_mask.astype(np.float32)[:, None]
    denominator = max(float(weights.sum()), 1.0)
    return (features * weights).sum(axis=0) / denominator
