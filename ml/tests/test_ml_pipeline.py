from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ml.datasets.integrity import validate_training_dataset
from ml.evaluation.calibration import calibrate_temperature, softmax
from ml.evaluation.metrics import classification_metrics, top_k_accuracy
from ml.evaluation.unknown_detection import decision_from_probabilities
from ml.preprocessing.augmentation import add_landmark_noise, temporal_dropout
from ml.preprocessing.masking import frame_mask_from_presence, masked_mean
from ml.preprocessing.normalization import normalize_training_sequence
from ml.preprocessing.sampling import resample_sequence


def test_training_dataset_rejects_empty_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"version": "0.1.0", "status": "READY", "items": []}),
        encoding="utf-8",
    )
    report = validate_training_dataset(dataset_version="0.1.0", manifest_path=manifest)
    assert report["valid"] is False
    assert any("Aucun exemple" in error for error in report["errors"])


def test_training_dataset_rejects_split_contamination(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "status": "READY",
                "items": [
                    {
                        "contribution_id": "c1",
                        "recording_id": "r1",
                        "contributor_public_id": "signer_1",
                        "sign_code": "HELP",
                        "split": "TRAIN",
                        "landmark_object_key": "missing.json",
                        "checksum_landmarks": "",
                        "feature_schema_version": "1.0.0",
                    },
                    {
                        "contribution_id": "c2",
                        "recording_id": "r2",
                        "contributor_public_id": "signer_1",
                        "sign_code": "HELP",
                        "split": "TEST",
                        "landmark_object_key": "missing2.json",
                        "checksum_landmarks": "",
                        "feature_schema_version": "1.0.0",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    report = validate_training_dataset(dataset_version="0.1.0", manifest_path=manifest)
    assert any("plusieurs splits" in error for error in report["errors"])


def test_preprocessing_shapes_masks_and_nan_rejection() -> None:
    features = np.ones((10, 63), dtype=np.float32)
    mask = np.ones((10, 21), dtype=np.float32)
    normalized = normalize_training_sequence(features, mask)
    sampled = resample_sequence(normalized, 30)
    assert sampled.shape == (30, 63)
    frame_mask = frame_mask_from_presence(mask)
    assert masked_mean(features, frame_mask).shape == (63,)
    features[0, 0] = np.nan
    try:
        normalize_training_sequence(features, mask)
    except ValueError as exc:
        assert "NaN" in str(exc)
    else:
        raise AssertionError("NaN features must be rejected")


def test_augmentation_is_deterministic_and_preserves_dimensions() -> None:
    features = np.zeros((30, 63), dtype=np.float32)
    mask = np.ones((30, 21), dtype=np.float32)
    assert np.array_equal(add_landmark_noise(features, seed=7), add_landmark_noise(features, seed=7))
    dropped = temporal_dropout(mask, seed=7, probability=0.1)
    assert dropped.shape == mask.shape


def test_metrics_calibration_and_unknown_decision() -> None:
    metrics = classification_metrics(["A", "B", "B"], ["A", "A", "B"], ["A", "B"])
    assert metrics["accuracy_top1"] == 2 / 3
    assert top_k_accuracy(["A"], [["B", "A"]], 2) == 1
    logits = np.asarray([[2.0, 0.2], [0.1, 2.0]], dtype=np.float32)
    probabilities = softmax(logits)
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    calibration = calibrate_temperature(logits, np.asarray([0, 1]))
    assert calibration["temperature"] > 0
    decision, level = decision_from_probabilities(
        np.asarray([0.4, 0.35, 0.25]), unknown_threshold=0.5, margin_threshold=0.15
    )
    assert (decision, level) == ("unknown", "low")
