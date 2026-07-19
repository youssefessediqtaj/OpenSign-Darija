from __future__ import annotations

from dataclasses import dataclass

import numpy as np


SCHEMA_VERSION = "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
COORDINATE_FORMAT = "shoulder_centered_v1"
POSE_LANDMARK_INDICES = tuple(range(33))
LEFT_HAND_LANDMARK_INDICES = tuple(range(21))
RIGHT_HAND_LANDMARK_INDICES = tuple(range(21))
LANDMARKS_PER_FRAME = 75
COORDINATES = 3
EXPECTED_FRAME_SHAPE = (LANDMARKS_PER_FRAME, COORDINATES)


@dataclass(frozen=True)
class NormalizedFrame:
    landmarks: np.ndarray
    presence_mask: np.ndarray


def _as_landmarks(value: object, expected: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32)
    if array.shape != (expected, COORDINATES):
        raise ValueError(f"{name} must have shape ({expected}, {COORDINATES})")
    if np.isinf(array).any():
        raise ValueError(f"{name} contains infinite values")
    return array


def _fill_missing(array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    finite = np.isfinite(array).all(axis=1)
    filled = np.where(np.isfinite(array), array, 0.0).astype(np.float32)
    return filled, finite.astype(np.float32)


def normalize_frame(
    pose_landmarks: object,
    left_hand_landmarks: object,
    right_hand_landmarks: object,
) -> NormalizedFrame:
    pose = _as_landmarks(pose_landmarks, 33, "pose_landmarks")
    left = _as_landmarks(left_hand_landmarks, 21, "left_hand_landmarks")
    right = _as_landmarks(right_hand_landmarks, 21, "right_hand_landmarks")

    pose, pose_mask = _fill_missing(pose)
    left, left_mask = _fill_missing(left)
    right, right_mask = _fill_missing(right)

    left_shoulder = pose[11]
    right_shoulder = pose[12]
    if pose_mask[11] == 0 or pose_mask[12] == 0:
        origin = np.zeros((COORDINATES,), dtype=np.float32)
        scale = 1.0
    else:
        origin = ((left_shoulder + right_shoulder) / 2.0).astype(np.float32)
        scale = float(np.linalg.norm(left_shoulder - right_shoulder))
        if not np.isfinite(scale) or scale < 1e-6:
            scale = 1.0

    stacked = np.concatenate([pose, left, right], axis=0)
    normalized = ((stacked - origin) / scale).astype(np.float32)
    mask = np.concatenate([pose_mask, left_mask, right_mask], axis=0).astype(np.float32)
    normalized[mask == 0] = 0.0
    return NormalizedFrame(landmarks=normalized, presence_mask=mask)


def pad_or_truncate_sequence(sequence: object, target_frames: int = 60) -> np.ndarray:
    array = np.asarray(sequence, dtype=np.float32)
    if array.ndim != 3 or array.shape[1:] != EXPECTED_FRAME_SHAPE:
        raise ValueError(f"sequence must have shape (frames, {LANDMARKS_PER_FRAME}, {COORDINATES})")
    if np.isnan(array).any() or np.isinf(array).any():
        raise ValueError("sequence contains NaN or infinite values")
    if target_frames <= 0:
        raise ValueError("target_frames must be positive")
    if array.shape[0] >= target_frames:
        return array[:target_frames].copy()
    padded = np.zeros((target_frames, LANDMARKS_PER_FRAME, COORDINATES), dtype=np.float32)
    padded[: array.shape[0]] = array
    return padded
