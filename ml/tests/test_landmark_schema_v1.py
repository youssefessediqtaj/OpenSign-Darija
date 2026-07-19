import json
from pathlib import Path

import numpy as np
import pytest

from ml.preprocessing.landmark_schema_v1 import (
    COORDINATE_FORMAT,
    LANDMARKS_PER_FRAME,
    SCHEMA_VERSION,
    normalize_frame,
    pad_or_truncate_sequence,
)


FIXTURE_DIR = Path("tests/fixtures/landmarks")


def array_from_sparse(mapping: dict[str, list[float]], expected: int) -> np.ndarray:
    array = np.full((expected, 3), np.nan, dtype=np.float32)
    for index, values in mapping.items():
        array[int(index)] = values
    return array


def test_normalize_frame_outputs_75_landmarks() -> None:
    pose = np.zeros((33, 3), dtype=np.float32)
    pose[11] = [0.0, 0.0, 0.0]
    pose[12] = [2.0, 0.0, 0.0]
    left = np.ones((21, 3), dtype=np.float32)
    right = np.ones((21, 3), dtype=np.float32) * 2

    frame = normalize_frame(pose, left, right)

    assert frame.landmarks.shape == (LANDMARKS_PER_FRAME, 3)
    assert frame.presence_mask.shape == (LANDMARKS_PER_FRAME,)
    assert frame.landmarks[11].tolist() == [-0.5, 0.0, 0.0]
    assert frame.landmarks[12].tolist() == [0.5, 0.0, 0.0]


def test_normalize_frame_handles_missing_hand() -> None:
    pose = np.zeros((33, 3), dtype=np.float32)
    pose[11] = [0.0, 0.0, 0.0]
    pose[12] = [2.0, 0.0, 0.0]
    left = np.full((21, 3), np.nan, dtype=np.float32)
    right = np.ones((21, 3), dtype=np.float32)

    frame = normalize_frame(pose, left, right)

    assert frame.presence_mask[33:54].sum() == 0
    assert np.all(frame.landmarks[33:54] == 0)


def test_pad_or_truncate_sequence_rejects_nan() -> None:
    sequence = np.zeros((2, LANDMARKS_PER_FRAME, 3), dtype=np.float32)
    sequence[0, 0, 0] = np.nan

    with pytest.raises(ValueError, match="NaN"):
        pad_or_truncate_sequence(sequence)


def test_pad_or_truncate_sequence_shape() -> None:
    sequence = np.ones((2, LANDMARKS_PER_FRAME, 3), dtype=np.float32)

    padded = pad_or_truncate_sequence(sequence, target_frames=4)
    truncated = pad_or_truncate_sequence(padded, target_frames=1)

    assert padded.shape == (4, LANDMARKS_PER_FRAME, 3)
    assert truncated.shape == (1, LANDMARKS_PER_FRAME, 3)


def test_schema_v1_matches_shared_fixture() -> None:
    source = json.loads((FIXTURE_DIR / "schema-v1-input.json").read_text(encoding="utf-8"))
    expected = json.loads((FIXTURE_DIR / "schema-v1-expected.json").read_text(encoding="utf-8"))
    frame = normalize_frame(
        array_from_sparse(source["pose"], 33),
        array_from_sparse(source["left_hand"], 21),
        array_from_sparse(source["right_hand"], 21),
    )
    sequence = pad_or_truncate_sequence(frame.landmarks[None, :, :], target_frames=4)

    assert SCHEMA_VERSION == expected["schema_version"]
    assert COORDINATE_FORMAT == expected["coordinate_format"]
    assert list(frame.landmarks.shape) == expected["frame_shape"]
    assert list(sequence.shape) == expected["sequence_shape_after_padding"]
    assert int(frame.presence_mask[:33].sum()) == expected["presence_sums"]["pose"]
    assert int(frame.presence_mask[33:54].sum()) == expected["presence_sums"]["left_hand"]
    assert int(frame.presence_mask[54:].sum()) == expected["presence_sums"]["right_hand"]
    for index, values in expected["selected_landmarks"].items():
        np.testing.assert_allclose(
            frame.landmarks[int(index)],
            values,
            atol=expected["tolerance"],
        )
    for index, value in expected["selected_presence"].items():
        assert frame.presence_mask[int(index)] == value
