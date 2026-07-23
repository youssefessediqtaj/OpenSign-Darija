from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import pytest
import torch

from ml.datasets.mosl_video.local_audit import build_local_audit
from ml.datasets.mosl_video.preprocess import (
    cache_valid,
    preprocess_manifest,
    resolve_mediapipe_model,
)
from ml.datasets.mosl_video.training_data import (
    LandmarkSample,
    augment_landmarks,
    balanced_sampler,
    class_weights,
    load_landmarks,
    samples_from_split_report,
)
from ml.models.mosl_v1 import ModelSpec, build_model
from ml.training.train_mosl_v1 import (
    LEXICAL_MIN5_SCOPE,
    TrainingConfig,
    calibrate_unknown,
    choose_vocabulary_scope,
    export_onnx,
    inference_latency,
    load_checkpoint,
    save_checkpoint,
    scoped_split_report,
    unknown_metrics,
    validate_model_package,
)


def write_cache(path: Path, checksum: str, value: float = 0.1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    landmarks = np.full((60, 75, 3), value, dtype=np.float32)
    presence = np.ones((60, 75), dtype=np.float32)
    np.savez_compressed(
        path,
        landmarks=landmarks,
        presence_mask=presence,
        metadata=np.array(
            json.dumps(
                {
                    "source_sha256": checksum,
                    "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                    "preprocessing_version": "mediapipe_tasks_holistic_v1",
                    "frames": 60,
                    "landmarks_per_frame": 75,
                    "coordinates": 3,
                }
            )
        ),
    )


def fixture_dataset(tmp_path: Path) -> tuple[Path, Path, Path]:
    dataset_root = tmp_path / "dataset"
    processed = dataset_root / "processed" / "landmarks"
    manifest = dataset_root / "manifests" / "videos.jsonl"
    records: list[dict[str, object]] = []

    def add(label: str, display: str, index: int, payload: bytes, mode: str = "WORD_ISOLATED") -> str:
        relative = Path("raw") / f"{label or 'invalid'}-{index}.mp4"
        path = dataset_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        checksum = hashlib.sha256(payload).hexdigest()
        write_cache(processed / f"{checksum}.npz", checksum, value=0.1 + index / 100)
        records.append(
            {
                "sha256": checksum,
                "label_key": label,
                "normalized_label_ar": display,
                "category": "Diverse",
                "mode": mode,
                "current_relative_path": relative.as_posix(),
            }
        )
        return checksum

    for label, display in (("a", "أ"), ("b", "ب")):
        for index in range(5):
            add(label, display, index, f"{label}-{index}".encode())
    for index in range(2):
        add("small", "قليل", index, f"small-{index}".encode())
    for index in range(5):
        display = "لَوَّنَ" if index < 3 else "لَوْنٌ"
        add("collision", display, index, f"collision-{index}".encode())
    add("", "ً", 0, b"invalid")
    duplicate = add("ambiguous_a", "مكرر أ", 0, b"same-binary")
    relative = Path("raw") / "ambiguous-b-0.mp4"
    (dataset_root / relative).write_bytes(b"same-binary")
    records.append(
        {
            "sha256": duplicate,
            "label_key": "ambiguous_b",
            "normalized_label_ar": "مكرر ب",
            "category": "Diverse",
            "mode": "WORD_ISOLATED",
            "current_relative_path": relative.as_posix(),
        }
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return dataset_root, manifest, processed


def test_local_audit_is_deterministic_checksum_grouped_and_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, manifest, processed = fixture_dataset(tmp_path)

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    first = build_local_audit(
        dataset_root=root,
        manifest_path=manifest,
        processed_dir=processed,
        report_dir=tmp_path / "reports-a",
        minimum_samples=5,
        unknown_samples_per_split=1,
    )
    second = build_local_audit(
        dataset_root=root,
        manifest_path=manifest,
        processed_dir=processed,
        report_dir=tmp_path / "reports-b",
        minimum_samples=5,
        unknown_samples_per_split=1,
    )
    audit, vocabulary, split = first
    assert vocabulary["supported_label_count"] == 2
    assert vocabulary["supported_sample_count"] == 10
    assert split["counts"] == {"train": 6, "validation": 2, "test": 2, "total": 10}
    assert split["label_index"] == second[2]["label_index"]
    assert split["assignments"] == second[2]["assignments"]
    assert split["checksum_split_leakage"] == {}
    assert split["unknown_label_overlap"] == []
    assert split["valid"] is True
    assert audit["ambiguous_duplicate_checksum_group_count"] == 1
    assert audit["ambiguous_label_mapping_count"] == 1
    assert audit["ambiguous_label_mappings"] == [
        {
            "label_key": "collision",
            "normalized_labels_ar": ["لَوَّنَ", "لَوْنٌ"],
            "display_variant_counts": {"لَوَّنَ": 3, "لَوْنٌ": 2},
            "video_count": 5,
            "training_decision": "EXCLUDED_FOR_QUALITY",
            "exclusion_reason": (
                "ambiguous_label_key_multiple_arabic_displays"
            ),
        }
    ]
    assert not any(
        item["sha256"] in split["ambiguous_duplicate_checksums_excluded"]
        for item in split["assignments"]
    )
    rows = {item["label_key"]: item for item in vocabulary["labels"]}
    assert rows["a"]["label_ar"] == "أ"
    assert rows[""]["supported_status"] == "INVALID"
    assert rows["ambiguous_a"]["supported_status"] == "EXCLUDED_FOR_QUALITY"
    assert rows["collision"]["supported_status"] == "EXCLUDED_FOR_QUALITY"
    assert rows["collision"]["word_model_eligible_examples"] == 0
    assert rows["collision"]["exclusion_reason"] == (
        "ambiguous_label_key_multiple_arabic_displays"
    )
    assert "collision" not in split["supported_labels"]
    assert split["ambiguous_label_keys_excluded"] == ["collision"]
    assert not any(
        item["label_key"] == "collision"
        for item in [*split["unknown_calibration"], *split["unknown_test"]]
    )

    with pytest.raises(ValueError, match="never be below three"):
        build_local_audit(
            dataset_root=root,
            manifest_path=manifest,
            processed_dir=processed,
            report_dir=tmp_path / "invalid-minimum",
            minimum_samples=2,
        )


def test_preprocessing_resolves_only_local_mediapipe_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    asset = tmp_path / "holistic_landmarker.task"
    asset.write_bytes(b"local-model-asset")
    assert resolve_mediapipe_model(asset) == asset
    with pytest.raises(FileNotFoundError, match="never downloads assets"):
        resolve_mediapipe_model(tmp_path / "missing.task")


def test_preprocessing_cache_validation_rejects_corruption(tmp_path: Path) -> None:
    checksum = "a" * 64
    valid = tmp_path / "valid.npz"
    write_cache(valid, checksum)
    assert cache_valid(valid, checksum) is True

    invalid = tmp_path / "invalid.npz"
    landmarks = np.ones((60, 75, 3), dtype=np.float32)
    landmarks[0, 0, 0] = np.nan
    np.savez_compressed(
        invalid,
        landmarks=landmarks,
        presence_mask=np.ones((60, 75), dtype=np.float32),
        metadata=np.array(
            json.dumps(
                {
                    "source_sha256": checksum,
                    "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                    "preprocessing_version": "mediapipe_tasks_holistic_v1",
                    "frames": 60,
                    "landmarks_per_frame": 75,
                    "coordinates": 3,
                }
            )
        ),
    )
    assert cache_valid(invalid, checksum) is False


def test_cached_preprocessing_and_training_step_are_fully_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, manifest, processed = fixture_dataset(tmp_path)
    asset = tmp_path / "holistic_landmarker.task"
    asset.write_bytes(b"local-model-asset")
    model = build_model(
        ModelSpec(
            "bidirectional_gru",
            class_count=2,
            hidden_size=8,
            dropout=0.0,
        )
    )
    # Constructing the optimizer primes PyTorch's optional platform inspection;
    # the actual forward/backward/update remains inside the offline guard below.
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("external process or network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)

    summary = preprocess_manifest(
        manifest,
        root,
        processed,
        tmp_path / "preprocessing-report",
        mediapipe_model_path=asset,
        progress_every=0,
    )
    assert summary["failed"] == 0
    assert summary["cache_hits"] == summary["attempted"]

    audit_report = tmp_path / "audit-report"
    build_local_audit(
        dataset_root=root,
        manifest_path=manifest,
        processed_dir=processed,
        report_dir=audit_report,
        minimum_samples=5,
        unknown_samples_per_split=1,
    )
    label_index, splits = samples_from_split_report(
        audit_report / "model-v1-split-report.json"
    )
    assert len(label_index) == 2
    batch_samples = splits["train"][:2]
    features = torch.stack(
        [torch.from_numpy(load_landmarks(sample.path)[0]) for sample in batch_samples]
    )
    targets = torch.tensor([sample.label_index for sample in batch_samples])
    optimizer.zero_grad(set_to_none=True)
    loss = torch.nn.functional.cross_entropy(model(features), targets)
    loss.backward()
    optimizer.step()
    assert torch.isfinite(loss)
    assert any(parameter.grad is not None for parameter in model.parameters())


def test_split_loader_label_index_is_deterministic(tmp_path: Path) -> None:
    root, manifest, processed = fixture_dataset(tmp_path)
    report_dir = tmp_path / "reports"
    build_local_audit(
        dataset_root=root,
        manifest_path=manifest,
        processed_dir=processed,
        report_dir=report_dir,
        minimum_samples=5,
        unknown_samples_per_split=1,
    )
    first = samples_from_split_report(report_dir / "model-v1-split-report.json")
    second = samples_from_split_report(report_dir / "model-v1-split-report.json")
    assert first[0] == {"a": 0, "b": 1}
    assert first[0] == second[0]
    assert [sample.sha256 for sample in first[1]["train"]] == [
        sample.sha256 for sample in second[1]["train"]
    ]


def test_lexical_scope_is_deterministic_disjoint_and_validation_selected() -> None:
    assignments = [
        {
            "sha256": f"{label}-{split}",
            "label_key": label,
            "split": split,
            "processed_landmark_path": f"{label}-{split}.npz",
        }
        for label in ("11", "word", "12")
        for split in ("train", "validation", "test")
    ]
    base = {
        "seed": 42,
        "supported_labels": ["11", "12", "word"],
        "assignments": assignments,
        "unknown_calibration": [
            {
                "sha256": "unknown-calibration",
                "label_key": "calibration-only",
                "processed_landmark_path": "calibration.npz",
            }
        ],
        "unknown_test": [
            {
                "sha256": "unknown-test",
                "label_key": "test-only",
                "processed_landmark_path": "test.npz",
            }
        ],
        "valid": True,
    }
    scoped = scoped_split_report(
        base,
        active_labels=["word"],
        scope=LEXICAL_MIN5_SCOPE,
    )
    assert scoped["label_index"] == {"word": 0}
    assert scoped["counts"] == {
        "train": 1,
        "validation": 1,
        "test": 1,
        "total": 3,
    }
    assert scoped["unknown_label_overlap"] == []
    assert scoped["known_unknown_checksum_overlap"] == []
    assert scoped["valid"] is True

    all_candidate = {
        "validation": {"macro_f1": 0.20, "top1_accuracy": 0.30},
        "test": {"macro_f1": 1.0, "top1_accuracy": 1.0},
    }
    lexical_candidate = {
        "validation": {"macro_f1": 0.40, "top1_accuracy": 0.40},
        "test": {"macro_f1": 0.0, "top1_accuracy": 0.0},
    }
    selected, report = choose_vocabulary_scope(all_candidate, lexical_candidate)
    assert selected == LEXICAL_MIN5_SCOPE
    assert report["test_metrics_used"] is False


def test_augmentation_is_seeded_finite_and_never_swaps_hands() -> None:
    landmarks = np.zeros((60, 75, 3), dtype=np.float32)
    landmarks[:, :33] = 0.2
    landmarks[:, 33:54] = 1.0
    landmarks[:, 54:] = -1.0
    mask = np.ones((60, 75), dtype=np.float32)
    first = augment_landmarks(landmarks, mask, seed=17)
    second = augment_landmarks(landmarks, mask, seed=17)
    assert np.array_equal(first, second)
    assert first.shape == (60, 75, 3)
    assert np.isfinite(first).all()
    assert float(first[:, 33:54].mean()) > float(first[:, 54:].mean())


def test_balanced_sampler_and_class_weighting() -> None:
    samples = [
        LandmarkSample(str(index), "a", 0, "train", Path("a")) for index in range(3)
    ] + [LandmarkSample("b", "b", 1, "train", Path("b"))]
    weights = class_weights(samples, 2)
    assert weights[1] > weights[0]
    sampler = balanced_sampler(samples, seed=42)
    assert len(list(sampler)) == len(samples)


@pytest.mark.parametrize(
    "architecture",
    ["bidirectional_gru", "temporal_conv_gru", "lightweight_transformer"],
)
def test_candidate_forward_backward_and_output_count(architecture: str) -> None:
    model = build_model(ModelSpec(architecture, class_count=3, hidden_size=16, dropout=0.0))
    features = torch.randn(2, 60, 75, 3)
    output = model(features)
    assert output.shape == (2, 3)
    torch.nn.functional.cross_entropy(output, torch.tensor([0, 2])).backward()
    assert any(parameter.grad is not None for parameter in model.parameters())
    model.eval()
    with torch.no_grad():
        empty_output = model(torch.zeros(1, 60, 75, 3))
    assert torch.isfinite(empty_output).all()


def test_candidate_rejects_invalid_shape() -> None:
    model = build_model(ModelSpec("bidirectional_gru", class_count=2, hidden_size=8))
    with pytest.raises(ValueError, match="60, 75, 3"):
        model(torch.zeros(1, 59, 75, 3))


def test_checkpoint_save_load_and_recovery(tmp_path: Path) -> None:
    model = build_model(ModelSpec("bidirectional_gru", class_count=2, hidden_size=8))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer)
    path = tmp_path / "checkpoint.pt"
    save_checkpoint(
        path,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        epoch=3,
        best_macro_f1=0.5,
        best_validation_loss=0.8,
        stale_epochs=1,
        label_index={"a": 0, "b": 1},
        architecture="bidirectional_gru",
        config=TrainingConfig(epochs=3, hidden_size=8),
        dataset_manifest_checksum="a" * 64,
    )
    original = {key: value.clone() for key, value in model.state_dict().items()}
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(10)
    checkpoint = load_checkpoint(path, model=model, optimizer=optimizer, scheduler=scheduler)
    assert checkpoint["epoch"] == 3
    assert checkpoint["label_index"] == {"a": 0, "b": 1}
    for key, value in model.state_dict().items():
        assert torch.equal(value, original[key])


def test_onnx_checker_runtime_parity_topk_and_latency(tmp_path: Path) -> None:
    checksum = "a" * 64
    sample = tmp_path / "sample.npz"
    write_cache(sample, checksum)
    model = build_model(ModelSpec("bidirectional_gru", class_count=3, hidden_size=8, dropout=0.0))
    report = export_onnx(
        model,
        output=tmp_path / "model.onnx",
        labels=["a", "b", "c"],
        validation_sample=sample,
    )
    assert report["valid"] is True
    assert report["input_shape"] == ["batch", 60, 75, 3]
    assert report["output_shape"] == ["batch", 3]
    assert report["top_k_match"] is True
    assert report["max_abs_diff"] < 1e-4
    latency = inference_latency(model, sample, repeats=2)
    assert latency["average_ms"] >= 0
    assert latency["p95_ms"] >= 0


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_dataset_loader_rejects_non_finite_values(tmp_path: Path, invalid: float) -> None:
    path = tmp_path / "bad.npz"
    landmarks = np.zeros((60, 75, 3), dtype=np.float32)
    landmarks[0, 0, 0] = invalid
    np.savez_compressed(
        path,
        landmarks=landmarks,
        presence_mask=np.ones((60, 75), dtype=np.float32),
        metadata=np.array("{}"),
    )
    with pytest.raises(ValueError, match="NaN or infinity"):
        load_landmarks(path)


def test_confidence_calibration_and_unknown_rejection() -> None:
    known_logits = np.asarray([[8.0, 0.0], [0.0, 8.0]], dtype=np.float32)
    targets = np.asarray([0, 1], dtype=np.int64)
    unknown_logits = np.asarray([[0.1, 0.1], [0.2, 0.19]], dtype=np.float32)
    calibration = calibrate_unknown(known_logits, targets, unknown_logits)
    metrics = unknown_metrics(known_logits, targets, unknown_logits, calibration)
    assert calibration["temperature"] > 0
    assert 0 <= calibration["unknown_threshold"] <= 1
    assert metrics["known_acceptance_rate"] == 1.0
    assert metrics["unknown_rejection_rate"] == 1.0
    assert calibration["pareto_frontier"]
    assert calibration["selection_policy"]["test_metrics_used"] is False


def test_confidence_calibration_uses_documented_safety_fallback() -> None:
    known_logits = np.asarray(
        [[5.0, 0.0], [0.0, 4.0], [0.405, 0.0], [0.0, 0.2], [0.0, 0.3]],
        dtype=np.float32,
    )
    targets = np.asarray([0, 1, 0, 1, 0], dtype=np.int64)
    unknown_logits = np.asarray(
        [[0.5, 0.0], [0.0, 0.55], [0.45, 0.0], [0.0, 0.5]] * 5,
        dtype=np.float32,
    )
    calibration = calibrate_unknown(known_logits, targets, unknown_logits)
    metrics = unknown_metrics(known_logits, targets, unknown_logits, calibration)
    policy = calibration["selection_policy"]
    assert policy["requested_floor_feasible"] is True
    assert policy["safety_fallback_used"] is True
    assert policy["applied_minimum_known_correct_acceptance"] == 0.4
    assert metrics["known_correct_acceptance_rate"] >= 0.4
    assert metrics["unknown_rejection_rate"] >= 0.6


def test_model_package_validator_fails_closed(tmp_path: Path) -> None:
    report = validate_model_package(tmp_path)
    assert report["valid"] is False
    assert "model.onnx" in report["missing"]
