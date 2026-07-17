from __future__ import annotations

import numpy as np


def resample_sequence(features: np.ndarray, target_frames: int) -> np.ndarray:
    if features.ndim != 2:
        raise ValueError("features must have shape [frames, feature_count]")
    if features.shape[0] == 0:
        raise ValueError("sequence is empty")
    if features.shape[0] == target_frames:
        return features.astype(np.float32, copy=False)
    source_positions = np.linspace(0, features.shape[0] - 1, num=features.shape[0])
    target_positions = np.linspace(0, features.shape[0] - 1, num=target_frames)
    columns = [
        np.interp(target_positions, source_positions, features[:, index])
        for index in range(features.shape[1])
    ]
    return np.stack(columns, axis=1).astype(np.float32)
