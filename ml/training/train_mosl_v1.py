from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from copy import deepcopy
import json
import math
import os
import random
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from ml.datasets.mosl_video.local_audit import (
    REPORT_DIR,
    build_local_audit,
    sha256_file,
    stable_order,
)
from ml.datasets.mosl_video.training_data import (
    MoslLandmarkDataset,
    balanced_sampler,
    class_weights,
    load_landmarks,
    samples_from_split_report,
)
from ml.evaluation.calibration import calibrate_temperature, softmax
from ml.models.mosl_v1 import ModelSpec, build_model, parameter_count


MODEL_NAME = "mosl-isolated-sign-v1"
MODEL_VERSION = "1.0.0"
MODEL_DIR = Path("artifacts/models/mosl-isolated-sign-v1")
SPLIT_REPORT = REPORT_DIR / "model-v1-split-report.json"
VOCABULARY_REPORT = REPORT_DIR / "supported-sign-vocabulary-v1.json"
ARCHITECTURES = (
    "bidirectional_gru",
    "temporal_conv_gru",
    "lightweight_transformer",
)
ALL_MIN5_SCOPE = "all_min5"
LEXICAL_MIN5_SCOPE = "lexical_min5"
LEXICAL_SCOPE_MINIMUM_MACRO_F1_GAIN = 0.10


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 42
    epochs: int = 40
    batch_size: int = 8
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    hidden_size: int = 64
    dropout: float = 0.15
    gradient_clip_norm: float = 1.0
    early_stopping_patience: int = 8
    scheduler_patience: int = 3
    scheduler_factor: float = 0.5
    minimum_learning_rate: float = 0.00001


def set_reproducible_seed(seed: int) -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    try:
        torch.use_deterministic_algorithms(True)
    except RuntimeError:
        pass


def scoped_split_report(
    base: dict[str, Any],
    *,
    active_labels: list[str],
    scope: str,
) -> dict[str, Any]:
    report = deepcopy(base)
    active = set(active_labels)
    eligible = set(str(label) for label in base["supported_labels"])
    if not active or not active <= eligible:
        raise ValueError("active vocabulary must be a non-empty subset of eligible labels")
    assignments = [
        item for item in base["assignments"] if str(item["label_key"]) in active
    ]
    deferred = stable_order(
        sorted(eligible - active),
        seed=int(base["seed"]),
        namespace=f"{scope}:deferred-unknown-labels",
    )
    calibration_deferred = set(deferred[: (len(deferred) + 1) // 2])
    test_deferred = set(deferred[(len(deferred) + 1) // 2 :])

    def deferred_unknown(labels: set[str], split: str) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []
        for label in sorted(labels):
            candidates = [
                item
                for item in base["assignments"]
                if str(item["label_key"]) == label and item["split"] == split
            ]
            if not candidates:
                raise ValueError(f"deferred label {label!r} has no {split} sample")
            item = sorted(candidates, key=lambda value: str(value["sha256"]))[0]
            output.append(
                {
                    "sha256": str(item["sha256"]),
                    "label_key": label,
                    "processed_landmark_path": str(item["processed_landmark_path"]),
                }
            )
        return output

    unknown_calibration = [*base["unknown_calibration"]]
    unknown_calibration.extend(
        deferred_unknown(calibration_deferred, "validation")
    )
    unknown_test = [*base["unknown_test"]]
    unknown_test.extend(deferred_unknown(test_deferred, "test"))
    known_checksums = {str(item["sha256"]) for item in assignments}
    unknown_checksums = {
        str(item["sha256"]) for item in [*unknown_calibration, *unknown_test]
    }
    unknown_calibration_labels = {
        str(item["label_key"]) for item in unknown_calibration
    }
    unknown_test_labels = {str(item["label_key"]) for item in unknown_test}
    counts = {
        split: sum(1 for item in assignments if item["split"] == split)
        for split in ("train", "validation", "test")
    }
    counts["total"] = len(assignments)
    report.update(
        {
            "active_vocabulary_scope": scope,
            "eligible_supported_labels": sorted(eligible),
            "deferred_eligible_labels": sorted(eligible - active),
            "label_index": {
                label: index for index, label in enumerate(sorted(active))
            },
            "supported_labels": sorted(active),
            "counts": counts,
            "assignments": sorted(
                assignments,
                key=lambda item: (
                    str(item["split"]),
                    str(item["label_key"]),
                    str(item["sha256"]),
                ),
            ),
            "unknown_calibration": sorted(
                unknown_calibration,
                key=lambda item: (str(item["label_key"]), str(item["sha256"])),
            ),
            "unknown_test": sorted(
                unknown_test,
                key=lambda item: (str(item["label_key"]), str(item["sha256"])),
            ),
            "unknown_label_overlap": sorted(
                unknown_calibration_labels & unknown_test_labels
            ),
            "known_unknown_checksum_overlap": sorted(
                known_checksums & unknown_checksums
            ),
        }
    )
    report["valid"] = bool(
        base["valid"]
        and not report["unknown_label_overlap"]
        and not report["known_unknown_checksum_overlap"]
    )
    return report


def choose_vocabulary_scope(
    all_min5: dict[str, Any], lexical_min5: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    all_validation = all_min5["validation"]
    lexical_validation = lexical_min5["validation"]
    macro_f1_gain = float(lexical_validation["macro_f1"]) - float(
        all_validation["macro_f1"]
    )
    top1_gain = float(lexical_validation["top1_accuracy"]) - float(
        all_validation["top1_accuracy"]
    )
    lexical_is_materially_stronger = bool(
        macro_f1_gain >= LEXICAL_SCOPE_MINIMUM_MACRO_F1_GAIN and top1_gain >= 0.0
    )
    scope = LEXICAL_MIN5_SCOPE if lexical_is_materially_stronger else ALL_MIN5_SCOPE
    return scope, {
        "selection_split": "validation",
        "test_metrics_used": False,
        "rule": (
            "Use lexical_min5 only when validation macro F1 improves by at least "
            f"{LEXICAL_SCOPE_MINIMUM_MACRO_F1_GAIN:.2f} without reducing validation top-1."
        ),
        "all_min5_validation_macro_f1": float(all_validation["macro_f1"]),
        "lexical_min5_validation_macro_f1": float(
            lexical_validation["macro_f1"]
        ),
        "macro_f1_gain": macro_f1_gain,
        "all_min5_validation_top1": float(all_validation["top1_accuracy"]),
        "lexical_min5_validation_top1": float(
            lexical_validation["top1_accuracy"]
        ),
        "top1_gain": top1_gain,
        "lexical_is_materially_stronger": lexical_is_materially_stronger,
        "selected_scope": scope,
    }


def atomic_torch_save(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def save_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    epoch: int,
    best_macro_f1: float,
    best_validation_loss: float,
    stale_epochs: int,
    label_index: dict[str, int],
    architecture: str,
    config: TrainingConfig,
    dataset_manifest_checksum: str,
) -> None:
    atomic_torch_save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "epoch": epoch,
            "best_macro_f1": best_macro_f1,
            "best_validation_loss": best_validation_loss,
            "stale_epochs": stale_epochs,
            "label_index": label_index,
            "architecture": architecture,
            "config": asdict(config),
            "dataset_manifest_checksum": dataset_manifest_checksum,
            "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        },
        path,
    )


def load_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any | None = None,
) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    if optimizer is not None:
        optimizer.load_state_dict(checkpoint["optimizer_state"])
    if scheduler is not None:
        scheduler.load_state_dict(checkpoint["scheduler_state"])
    return checkpoint


def _predict(
    model: nn.Module,
    samples: list[Any],
    *,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    dataset = MoslLandmarkDataset(samples, augment=False)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    logits: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for features, labels in loader:
            output = model(features)
            logits.append(output.detach().cpu().numpy())
            targets.append(labels.detach().cpu().numpy())
    class_count = int(model.classifier[-1].out_features)  # type: ignore[index]
    return (
        np.concatenate(logits) if logits else np.zeros((0, class_count), dtype=np.float32),
        np.concatenate(targets) if targets else np.zeros((0,), dtype=np.int64),
    )


def classification_metrics(
    logits: np.ndarray,
    targets: np.ndarray,
    labels: list[str],
    *,
    temperature: float = 1.0,
) -> dict[str, Any]:
    probabilities = softmax(logits, temperature) if len(logits) else logits
    predictions = probabilities.argmax(axis=1) if len(probabilities) else np.zeros(0, dtype=int)
    class_count = len(labels)
    matrix = np.zeros((class_count, class_count), dtype=np.int64)
    for truth, prediction in zip(targets, predictions, strict=True):
        matrix[int(truth), int(prediction)] += 1
    per_class: list[dict[str, Any]] = []
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    supports: list[int] = []
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        false_positive = int(matrix[:, index].sum() - true_positive)
        false_negative = int(matrix[index, :].sum() - true_positive)
        support = int(matrix[index, :].sum())
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)
        per_class.append(
            {
                "label_key": label,
                "precision": round(precision, 8),
                "recall": round(recall, 8),
                "f1": round(f1, 8),
                "support": support,
            }
        )
    top1 = float((predictions == targets).mean()) if len(targets) else 0.0
    top3 = (
        float(
            np.mean(
                [
                    int(int(truth) in np.argsort(row)[::-1][: min(3, class_count)])
                    for truth, row in zip(targets, probabilities, strict=True)
                ]
            )
        )
        if len(targets)
        else 0.0
    )
    return {
        "sample_count": int(len(targets)),
        "top1_accuracy": round(top1, 8),
        "top3_accuracy": round(top3, 8),
        "macro_precision": round(float(np.mean(precisions)), 8),
        "macro_recall": round(float(np.mean(recalls)), 8),
        "macro_f1": round(float(np.mean(f1s)), 8),
        "balanced_accuracy": round(float(np.mean(recalls)), 8),
        "weighted_f1": round(
            float(np.average(f1s, weights=supports)) if sum(supports) else 0.0,
            8,
        ),
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def calibrate_unknown(
    known_logits: np.ndarray,
    known_targets: np.ndarray,
    unknown_logits: np.ndarray,
) -> dict[str, Any]:
    temperature_report = calibrate_temperature(known_logits, known_targets)
    temperature = float(temperature_report["temperature"])
    known_probabilities = softmax(known_logits, temperature)
    unknown_probabilities = softmax(unknown_logits, temperature)

    def scores(probabilities: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ordered = np.sort(probabilities, axis=1)[:, ::-1]
        return ordered[:, 0], ordered[:, 0] - ordered[:, 1]

    known_confidence, known_margin = scores(known_probabilities)
    unknown_confidence, unknown_margin = scores(unknown_probabilities)
    known_correct = known_probabilities.argmax(axis=1) == known_targets
    requested_known_correct_floor = 0.60
    safety_fallback_known_correct_floor = 0.40
    minimum_validation_unknown_rejection = 0.60
    unknown_rejection_weight = 0.65
    known_correct_weight = 1.0 - unknown_rejection_weight
    confidence_values = np.concatenate((known_confidence, unknown_confidence))
    margin_values = np.concatenate((known_margin, unknown_margin))
    thresholds = np.unique(
        np.concatenate(
            (
                [0.0],
                np.linspace(0.05, 0.95, 37),
                confidence_values,
                np.nextafter(confidence_values, 1.0),
            )
        )
    )
    margin_thresholds = np.unique(
        np.concatenate(
            (
                [0.0],
                np.linspace(0.0, 0.5, 21),
                margin_values,
                np.nextafter(margin_values, 1.0),
            )
        )
    )
    operating_points: dict[tuple[int, int, int], dict[str, float]] = {}
    for threshold in thresholds:
        for margin_threshold in margin_thresholds:
            known_accept = (known_confidence >= threshold) & (
                known_margin >= margin_threshold
            )
            known_correct_accept = known_accept & known_correct
            unknown_reject = (unknown_confidence < threshold) | (
                unknown_margin < margin_threshold
            )
            known_rate = float(known_accept.mean())
            known_correct_rate = float(known_correct_accept.mean())
            unknown_rate = float(unknown_reject.mean())
            balanced = (known_rate + unknown_rate) / 2.0
            safe_accuracy = (known_correct_rate + unknown_rate) / 2.0
            safety_score = (
                unknown_rejection_weight * unknown_rate
                + known_correct_weight * known_correct_rate
            )
            counts = (
                int(known_accept.sum()),
                int(known_correct_accept.sum()),
                int(unknown_reject.sum()),
            )
            point = {
                "unknown_threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
                "known_acceptance_rate": known_rate,
                "known_correct_acceptance_rate": known_correct_rate,
                "unknown_rejection_rate": unknown_rate,
                "balanced_unknown_accuracy": balanced,
                "safe_operating_accuracy": safe_accuracy,
                "safety_weighted_score": safety_score,
            }
            previous = operating_points.get(counts)
            if previous is None or (
                point["unknown_threshold"], point["margin_threshold"]
            ) < (previous["unknown_threshold"], previous["margin_threshold"]):
                operating_points[counts] = point

    points = list(operating_points.values())
    maximum_known_correct = max(
        point["known_correct_acceptance_rate"] for point in points
    )
    floor_is_feasible = maximum_known_correct >= requested_known_correct_floor
    primary_known_correct_floor = (
        requested_known_correct_floor if floor_is_feasible else maximum_known_correct
    )
    primary_eligible = [
        point
        for point in points
        if point["known_correct_acceptance_rate"] + 1e-12
        >= primary_known_correct_floor
    ]
    def selection_key(point: dict[str, float]) -> tuple[float, ...]:
        return (
            point["safety_weighted_score"],
            point["unknown_rejection_rate"],
            point["safe_operating_accuracy"],
            point["known_correct_acceptance_rate"],
            point["known_acceptance_rate"],
            -point["unknown_threshold"],
            -point["margin_threshold"],
        )
    primary_selected = max(primary_eligible, key=selection_key)
    safety_fallback_eligible = [
        point
        for point in points
        if point["known_correct_acceptance_rate"] + 1e-12
        >= min(safety_fallback_known_correct_floor, maximum_known_correct)
        and point["unknown_rejection_rate"] + 1e-12
        >= minimum_validation_unknown_rejection
    ]
    safety_fallback_used = bool(
        primary_selected["unknown_rejection_rate"]
        < minimum_validation_unknown_rejection
        and safety_fallback_eligible
    )
    selected = (
        max(safety_fallback_eligible, key=selection_key)
        if safety_fallback_used
        else primary_selected
    )
    applied_known_correct_floor = (
        min(safety_fallback_known_correct_floor, maximum_known_correct)
        if safety_fallback_used
        else primary_known_correct_floor
    )
    pareto_frontier = [
        point
        for point in points
        if not any(
            (
                other["known_correct_acceptance_rate"]
                >= point["known_correct_acceptance_rate"]
                and other["unknown_rejection_rate"]
                >= point["unknown_rejection_rate"]
                and other["known_acceptance_rate"]
                >= point["known_acceptance_rate"]
                and (
                    other["known_correct_acceptance_rate"]
                    > point["known_correct_acceptance_rate"]
                    or other["unknown_rejection_rate"]
                    > point["unknown_rejection_rate"]
                    or other["known_acceptance_rate"]
                    > point["known_acceptance_rate"]
                )
            )
            for other in points
        )
    ]
    pareto_frontier.sort(
        key=lambda point: (
            point["known_correct_acceptance_rate"],
            -point["unknown_rejection_rate"],
        )
    )
    return {
        "schema_version": "OPEN_SIGNE_CONFIDENCE_CALIBRATION_V1",
        "method": "temperature_scaling_max_probability_and_margin",
        "temperature": temperature,
        "unknown_threshold": selected["unknown_threshold"],
        "margin_threshold": selected["margin_threshold"],
        "known_validation_samples": int(len(known_targets)),
        "unknown_validation_samples": int(len(unknown_logits)),
        "temperature_nll": float(temperature_report["nll"]),
        "expected_calibration_error": float(temperature_report["ece"]),
        "selection_policy": {
            "selection_split": "validation",
            "test_metrics_used": False,
            "objective": "safety_weighted_known_correct_acceptance_and_oov_rejection",
            "unknown_rejection_weight": unknown_rejection_weight,
            "known_correct_acceptance_weight": known_correct_weight,
            "requested_minimum_known_correct_acceptance": requested_known_correct_floor,
            "safety_fallback_minimum_known_correct_acceptance": (
                safety_fallback_known_correct_floor
            ),
            "minimum_validation_unknown_rejection_target": (
                minimum_validation_unknown_rejection
            ),
            "applied_minimum_known_correct_acceptance": applied_known_correct_floor,
            "requested_floor_feasible": floor_is_feasible,
            "maximum_known_correct_acceptance": maximum_known_correct,
            "primary_operating_point": primary_selected,
            "safety_fallback_used": safety_fallback_used,
            "safety_fallback_reason": (
                "primary_floor_could_not_meet_validation_unknown_rejection_target"
                if safety_fallback_used
                else "not_needed"
            ),
        },
        "selected_operating_point": selected,
        "pareto_frontier": pareto_frontier,
        "validation": selected,
    }


def unknown_metrics(
    known_logits: np.ndarray,
    known_targets: np.ndarray,
    unknown_logits: np.ndarray,
    calibration: dict[str, Any],
) -> dict[str, float | int]:
    temperature = float(calibration["temperature"])
    threshold = float(calibration["unknown_threshold"])
    margin_threshold = float(calibration["margin_threshold"])

    def accepted(probabilities: np.ndarray) -> np.ndarray:
        ordered = np.sort(probabilities, axis=1)[:, ::-1]
        return (ordered[:, 0] >= threshold) & (
            ordered[:, 0] - ordered[:, 1] >= margin_threshold
        )

    known_probabilities = softmax(known_logits, temperature)
    unknown_probabilities = softmax(unknown_logits, temperature)
    known_accepted = accepted(known_probabilities)
    known_correct = known_probabilities.argmax(axis=1) == known_targets
    known_correct_accepted = known_accepted & known_correct
    unknown_rejected = ~accepted(unknown_probabilities)
    known_rate = float(known_accepted.mean())
    known_correct_rate = float(known_correct_accepted.mean())
    known_classification_accuracy = float(known_correct.mean())
    unknown_rate = float(unknown_rejected.mean())
    return {
        "known_samples": int(len(known_targets)),
        "unknown_samples": int(len(unknown_logits)),
        "known_acceptance_rate": known_rate,
        "known_correct_acceptance_rate": known_correct_rate,
        "known_classification_accuracy": known_classification_accuracy,
        "unknown_rejection_rate": unknown_rate,
        "unknown_false_acceptance_rate": 1.0 - unknown_rate,
        "balanced_unknown_accuracy": (known_rate + unknown_rate) / 2.0,
        "safe_operating_accuracy": (known_correct_rate + unknown_rate) / 2.0,
        "safety_weighted_score": 0.65 * unknown_rate + 0.35 * known_correct_rate,
    }


def inference_latency(model: nn.Module, sample_path: Path, repeats: int = 40) -> dict[str, float]:
    landmarks, _ = load_landmarks(sample_path)
    tensor = torch.from_numpy(landmarks[None, :, :, :])
    model.eval()
    with torch.no_grad():
        for _ in range(5):
            model(tensor)
        latencies: list[float] = []
        for _ in range(repeats):
            started = perf_counter()
            model(tensor)
            latencies.append((perf_counter() - started) * 1000.0)
    return {
        "average_ms": float(np.mean(latencies)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "repeats": float(repeats),
    }


def fit_candidate(
    architecture: str,
    *,
    label_index: dict[str, int],
    splits: dict[str, list[Any]],
    config: TrainingConfig,
    output_dir: Path,
    dataset_manifest_checksum: str,
    resume: bool = False,
) -> tuple[nn.Module, dict[str, Any]]:
    set_reproducible_seed(config.seed)
    labels = [label for label, _ in sorted(label_index.items(), key=lambda item: item[1])]
    model = build_model(
        ModelSpec(
            architecture,
            len(labels),
            hidden_size=config.hidden_size,
            dropout=config.dropout,
        )
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=config.scheduler_factor,
        patience=config.scheduler_patience,
        min_lr=config.minimum_learning_rate,
    )
    loss_function = nn.CrossEntropyLoss(
        weight=class_weights(splits["train"], len(labels))
    )
    train_dataset = MoslLandmarkDataset(
        splits["train"], augment=True, seed=config.seed
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        sampler=balanced_sampler(splits["train"], seed=config.seed),
        num_workers=0,
    )
    last_checkpoint = output_dir / "last-checkpoint.pt"
    best_checkpoint = output_dir / "best-checkpoint.pt"
    start_epoch = 1
    best_macro_f1 = -1.0
    best_validation_loss = math.inf
    stale_epochs = 0
    history: list[dict[str, Any]] = []
    if resume and last_checkpoint.exists():
        checkpoint = load_checkpoint(
            last_checkpoint, model=model, optimizer=optimizer, scheduler=scheduler
        )
        if checkpoint["label_index"] != label_index or checkpoint["architecture"] != architecture:
            raise ValueError("checkpoint label index or architecture is incompatible")
        start_epoch = int(checkpoint["epoch"]) + 1
        best_macro_f1 = float(checkpoint["best_macro_f1"])
        best_validation_loss = float(checkpoint["best_validation_loss"])
        stale_epochs = int(checkpoint["stale_epochs"])

    started = perf_counter()
    for epoch in range(start_epoch, config.epochs + 1):
        train_dataset.set_epoch(epoch)
        model.train()
        losses: list[float] = []
        for features, targets in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(features)
            loss = loss_function(logits, targets)
            if not torch.isfinite(loss):
                raise RuntimeError("training loss became NaN or infinity")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)
            optimizer.step()
            losses.append(float(loss.detach()))
        validation_logits, validation_targets = _predict(
            model, splits["validation"], batch_size=config.batch_size
        )
        with torch.no_grad():
            validation_loss = float(
                loss_function(
                    torch.from_numpy(validation_logits),
                    torch.from_numpy(validation_targets),
                )
            )
        validation_metrics = classification_metrics(
            validation_logits, validation_targets, labels
        )
        macro_f1 = float(validation_metrics["macro_f1"])
        scheduler.step(macro_f1)
        improved = macro_f1 > best_macro_f1 or (
            math.isclose(macro_f1, best_macro_f1) and validation_loss < best_validation_loss
        )
        if improved:
            best_macro_f1 = macro_f1
            best_validation_loss = validation_loss
            stale_epochs = 0
        else:
            stale_epochs += 1
        history.append(
            {
                "epoch": epoch,
                "train_loss": float(np.mean(losses)),
                "validation_loss": validation_loss,
                "validation_macro_f1": macro_f1,
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
            }
        )
        save_checkpoint(
            last_checkpoint,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            best_macro_f1=best_macro_f1,
            best_validation_loss=best_validation_loss,
            stale_epochs=stale_epochs,
            label_index=label_index,
            architecture=architecture,
            config=config,
            dataset_manifest_checksum=dataset_manifest_checksum,
        )
        if improved:
            shutil.copy2(last_checkpoint, best_checkpoint)
        if stale_epochs >= config.early_stopping_patience:
            break
    load_checkpoint(best_checkpoint, model=model)

    validation_logits, validation_targets = _predict(
        model, splits["validation"], batch_size=config.batch_size
    )
    unknown_validation_logits, _ = _predict(
        model, splits["unknown_calibration"], batch_size=config.batch_size
    )
    calibration = calibrate_unknown(
        validation_logits, validation_targets, unknown_validation_logits
    )
    validation_metrics = classification_metrics(
        validation_logits,
        validation_targets,
        labels,
        temperature=float(calibration["temperature"]),
    )
    validation_unknown = unknown_metrics(
        validation_logits,
        validation_targets,
        unknown_validation_logits,
        calibration,
    )
    test_logits, test_targets = _predict(
        model, splits["test"], batch_size=config.batch_size
    )
    unknown_test_logits, _ = _predict(
        model, splits["unknown_test"], batch_size=config.batch_size
    )
    test_metrics = classification_metrics(
        test_logits,
        test_targets,
        labels,
        temperature=float(calibration["temperature"]),
    )
    test_unknown = unknown_metrics(
        test_logits, test_targets, unknown_test_logits, calibration
    )
    latency = inference_latency(model, splits["test"][0].path)
    result = {
        "architecture": architecture,
        "parameter_count": parameter_count(model),
        "training_duration_seconds": perf_counter() - started,
        "epochs_completed": history[-1]["epoch"] if history else start_epoch - 1,
        "best_checkpoint": best_checkpoint.as_posix(),
        "checkpoint_size_bytes": best_checkpoint.stat().st_size,
        "history": history,
        "validation": validation_metrics,
        "validation_unknown": validation_unknown,
        "test": test_metrics,
        "test_unknown": test_unknown,
        "calibration": calibration,
        "latency": latency,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "training-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return model, result


def candidate_selection_key(result: dict[str, Any]) -> tuple[float, ...]:
    validation = result["validation"]
    unknown = result["validation_unknown"]
    return (
        float(validation["macro_f1"]),
        float(validation["balanced_accuracy"]),
        float(validation["top1_accuracy"]),
        float(validation["top3_accuracy"]),
        float(unknown["balanced_unknown_accuracy"]),
        -float(result["latency"]["p95_ms"]),
        -float(result["parameter_count"]),
    )


def write_scoped_vocabulary(
    path: Path,
    *,
    active_labels: list[str],
    selected_scope: str,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    active = set(active_labels)
    for item in payload["labels"]:
        label = str(item["label_key"])
        is_active = label in active
        item["active_model_v1"] = is_active
        if is_active:
            item["active_scope_reason"] = ""
        elif item["supported_status"] == "SUPPORTED_FOR_TRAINING":
            item["active_scope_reason"] = (
                "eligible_but_deferred_by_a_priori_numeric_vs_lexical_scope"
            )
        else:
            item["active_scope_reason"] = str(item["exclusion_reason"])
    payload["active_model_scope"] = selected_scope
    payload["active_model_label_count"] = len(active)
    payload["active_model_labels"] = sorted(active)
    payload["eligible_supported_label_count"] = int(payload["supported_label_count"])
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    csv_path = path.with_suffix(".csv")
    fields = list(payload["labels"][0]) if payload["labels"] else ["label_key"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(payload["labels"])
    return payload


def _write_confusion_matrix(path: Path, matrix: list[list[int]], labels: list[str]) -> None:
    import matplotlib.pyplot as plt

    size = max(7.0, len(labels) * 0.55)
    figure, axes = plt.subplots(figsize=(size, size))
    axes.imshow(np.asarray(matrix), cmap="Blues")
    axes.set_xticks(range(len(labels)), labels=labels, rotation=90)
    axes.set_yticks(range(len(labels)), labels=labels)
    axes.set_xlabel("Predicted")
    axes.set_ylabel("True")
    axes.set_title("MoSL isolated-sign test confusion matrix")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def export_onnx(
    model: nn.Module,
    *,
    output: Path,
    labels: list[str],
    validation_sample: Path,
) -> dict[str, Any]:
    import onnx
    import onnxruntime as ort

    landmarks, _ = load_landmarks(validation_sample)
    sample = landmarks[None, :, :, :].astype(np.float32)
    tensor = torch.from_numpy(sample)
    model.eval()
    with torch.no_grad():
        torch_logits = model(tensor).detach().cpu().numpy()
    torch.onnx.export(
        model,
        tensor,
        output,
        input_names=["landmarks"],
        output_names=["logits"],
        dynamic_axes={"landmarks": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    onnx.checker.check_model(str(output))
    session = ort.InferenceSession(str(output), providers=["CPUExecutionProvider"])
    onnx_logits = session.run(None, {"landmarks": sample})[0]
    torch_order = np.argsort(torch_logits[0])[::-1]
    onnx_order = np.argsort(onnx_logits[0])[::-1]
    max_abs_diff = float(np.max(np.abs(torch_logits - onnx_logits)))
    top_k_match = torch_order[:3].tolist() == onnx_order[:3].tolist()
    report = {
        "valid": max_abs_diff < 1e-4 and top_k_match,
        "checker": "passed",
        "runtime_provider": "CPUExecutionProvider",
        "input_name": session.get_inputs()[0].name,
        "input_shape": list(session.get_inputs()[0].shape),
        "output_name": session.get_outputs()[0].name,
        "output_shape": list(session.get_outputs()[0].shape),
        "label_count": len(labels),
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": float(np.mean(np.abs(torch_logits - onnx_logits))),
        "top_k_match": top_k_match,
        "torch_top_k": [labels[index] for index in torch_order[:3]],
        "onnx_top_k": [labels[index] for index in onnx_order[:3]],
    }
    if not report["valid"]:
        raise RuntimeError(f"ONNX validation failed: {report}")
    return report


def validate_model_package(path: Path) -> dict[str, Any]:
    required = {
        "model.onnx",
        "labels.json",
        "supported-signs.json",
        "landmark-schema.json",
        "preprocessing.json",
        "training-config.yaml",
        "metrics.json",
        "confusion-matrix.png",
        "classification-report.csv",
        "confidence-calibration.json",
        "dataset-manifest-checksum.txt",
        "checksums.json",
        "model-card.md",
        "onnx-validation.json",
        "training-split-provenance.json",
    }
    missing = sorted(name for name in required if not (path / name).exists())
    errors: list[str] = [f"missing {name}" for name in missing]

    def read_json(name: str, fallback: Any) -> Any:
        file_path = path / name
        if not file_path.exists():
            return fallback
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid {name}: {exc}")
            return fallback

    labels = read_json("labels.json", [])
    supported = read_json("supported-signs.json", {})
    calibration = read_json("confidence-calibration.json", {})
    landmark_schema = read_json("landmark-schema.json", {})
    preprocessing = read_json("preprocessing.json", {})
    onnx_validation = read_json("onnx-validation.json", {})
    split_provenance = read_json("training-split-provenance.json", {})
    if len(labels) != int(supported.get("vocabulary_size", -1)):
        errors.append("label count differs from supported vocabulary size")
    if [item["label_key"] for item in supported.get("signs", [])] != labels:
        errors.append("supported sign order differs from labels.json")
    if not labels or any(not isinstance(label, str) or not label for label in labels):
        errors.append("labels.json must contain non-empty string labels")
    if any(
        item.get("status") != "SUPPORTED_FOR_TRAINING"
        for item in supported.get("signs", [])
    ):
        errors.append("supported-signs.json claims an unsupported label")
    for key in ("temperature", "unknown_threshold", "margin_threshold"):
        if key not in calibration:
            errors.append(f"calibration missing {key}")
    if float(calibration.get("temperature", 0.0)) <= 0.0:
        errors.append("calibration temperature must be positive")
    for key in ("unknown_threshold", "margin_threshold"):
        value = float(calibration.get(key, -1.0))
        if not 0.0 <= value <= 1.0:
            errors.append(f"calibration {key} must be between zero and one")
    expected_shape: list[Any] = ["batch", 60, 75, 3]
    if landmark_schema.get("schema_version") != "OPEN_SIGNE_LANDMARK_SCHEMA_V1":
        errors.append("landmark schema version is incompatible")
    if landmark_schema.get("input_shape") != expected_shape:
        errors.append("landmark schema input shape is incompatible")
    if (
        preprocessing.get("frames"),
        preprocessing.get("landmarks"),
        preprocessing.get("coordinates"),
    ) != (60, 75, 3):
        errors.append("preprocessing dimensions are incompatible")
    if preprocessing.get("offline_only") is not True:
        errors.append("preprocessing package must be marked offline_only")
    if not onnx_validation.get("valid") or not onnx_validation.get("top_k_match"):
        errors.append("ONNX parity report is not valid")
    if onnx_validation.get("input_shape") != expected_shape:
        errors.append("ONNX parity report input shape is incompatible")
    if onnx_validation.get("output_shape") != ["batch", len(labels)]:
        errors.append("ONNX parity report output shape is incompatible")
    if int(onnx_validation.get("label_count", -1)) != len(labels):
        errors.append("ONNX parity report label count differs from labels.json")
    if float(onnx_validation.get("max_abs_diff", math.inf)) >= 1e-4:
        errors.append("ONNX numerical parity exceeds tolerance")

    label_ar_by_key = {
        str(item.get("label_key", "")): str(item.get("label_ar", ""))
        for item in supported.get("signs", [])
        if isinstance(item, dict)
    }
    if split_provenance.get("schema_version") != "OPEN_SIGNE_MOSL_SPLIT_V1":
        errors.append("training split provenance schema is incompatible")
    if split_provenance.get("valid") is not True:
        errors.append("training split provenance is not valid")
    if split_provenance.get("supported_labels") != labels:
        errors.append("training split labels differ from labels.json")
    if split_provenance.get("label_index") != {
        label: index for index, label in enumerate(labels)
    }:
        errors.append("training split label index differs from labels.json")
    ambiguous_labels = set(split_provenance.get("ambiguous_label_keys_excluded", []))
    if set(labels) & ambiguous_labels:
        errors.append("packaged labels intersect ambiguous label keys")
    assignments = split_provenance.get("assignments", [])
    if not isinstance(assignments, list) or not assignments:
        errors.append("training split provenance has no assignments")
        assignments = []
    assignment_labels: set[str] = set()
    assignment_displays: dict[str, set[str]] = defaultdict(set)
    for item in assignments:
        if not isinstance(item, dict):
            errors.append("training split assignment is not an object")
            continue
        label = str(item.get("label_key", ""))
        display = str(item.get("label_ar", ""))
        assignment_labels.add(label)
        assignment_displays[label].add(display)
        if label not in labels:
            errors.append(f"training split contains unpackaged label {label!r}")
        elif display != label_ar_by_key.get(label):
            errors.append(f"training split Arabic label differs for {label!r}")
    if assignment_labels != set(labels):
        errors.append("training split assignments do not cover packaged labels exactly")
    if any(len(displays) != 1 for displays in assignment_displays.values()):
        errors.append("training split label maps to multiple Arabic displays")
    for pool_name in ("unknown_calibration", "unknown_test"):
        pool = split_provenance.get(pool_name, [])
        if not isinstance(pool, list):
            errors.append(f"training split {pool_name} is not a list")
            continue
        pool_labels = {
            str(item.get("label_key", ""))
            for item in pool
            if isinstance(item, dict)
        }
        if pool_labels & set(labels):
            errors.append(f"training split {pool_name} contains packaged labels")
        if pool_labels & ambiguous_labels:
            errors.append(f"training split {pool_name} contains ambiguous labels")

    checksums = read_json("checksums.json", {})
    for required_name in sorted(required - {"checksums.json"}):
        if required_name not in checksums:
            errors.append(f"checksum manifest missing {required_name}")
    for name, expected in checksums.items():
        file_path = path / name
        if not file_path.exists() or sha256_file(file_path) != expected:
            errors.append(f"checksum mismatch for {name}")
    manifest_checksum_path = path / "dataset-manifest-checksum.txt"
    if manifest_checksum_path.exists():
        manifest_checksum = manifest_checksum_path.read_text(encoding="utf-8").strip()
        if len(manifest_checksum) != 64 or any(
            character not in "0123456789abcdef" for character in manifest_checksum
        ):
            errors.append("dataset manifest checksum is not a lowercase SHA-256")
        if split_provenance.get("dataset_manifest_checksum_sha256") != manifest_checksum:
            errors.append("training split and package manifest checksums differ")

    runtime: dict[str, Any] = {}
    model_path = path / "model.onnx"
    if model_path.exists() and labels:
        try:
            import onnx
            import onnxruntime as ort

            onnx.checker.check_model(str(model_path))
            session = ort.InferenceSession(
                str(model_path), providers=["CPUExecutionProvider"]
            )
            input_metadata = session.get_inputs()[0]
            output_metadata = session.get_outputs()[0]
            runtime_output = session.run(
                None,
                {
                    input_metadata.name: np.zeros(
                        (1, 60, 75, 3), dtype=np.float32
                    )
                },
            )[0]
            runtime = {
                "checker": "passed",
                "provider": "CPUExecutionProvider",
                "input_name": input_metadata.name,
                "input_shape": list(input_metadata.shape),
                "output_name": output_metadata.name,
                "output_shape": list(output_metadata.shape),
                "smoke_output_shape": list(runtime_output.shape),
                "smoke_output_finite": bool(np.isfinite(runtime_output).all()),
            }
            if runtime["input_shape"] != expected_shape:
                errors.append("ONNX Runtime input shape is incompatible")
            if runtime["output_shape"] != ["batch", len(labels)]:
                errors.append("ONNX Runtime output shape differs from label count")
            if runtime["smoke_output_shape"] != [1, len(labels)]:
                errors.append("ONNX Runtime smoke output shape differs from label count")
            if not runtime["smoke_output_finite"]:
                errors.append("ONNX Runtime produced non-finite logits")
        except Exception as exc:
            errors.append(f"ONNX checker/runtime validation failed: {exc}")
    return {
        "valid": not errors,
        "required_files": sorted(required),
        "missing": missing,
        "errors": errors,
        "vocabulary_size": len(labels),
        "runtime": runtime,
    }


def package_selected_model(
    *,
    model: nn.Module,
    selected: dict[str, Any],
    benchmark: dict[str, Any],
    label_index: dict[str, int],
    splits: dict[str, list[Any]],
    split_report: dict[str, Any],
    vocabulary_path: Path,
    output_dir: Path,
    config: TrainingConfig,
    dataset_manifest_checksum: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = [label for label, _ in sorted(label_index.items(), key=lambda item: item[1])]
    vocabulary = json.loads(vocabulary_path.read_text(encoding="utf-8"))
    vocabulary_by_key = {item["label_key"]: item for item in vocabulary["labels"]}
    signs = [
        {
            "label_key": label,
            "label_ar": vocabulary_by_key[label]["label_ar"],
            "category": vocabulary_by_key[label]["category"],
            "examples": vocabulary_by_key[label]["examples"],
            "training_count": vocabulary_by_key[label]["training_count"],
            "validation_count": vocabulary_by_key[label]["validation_count"],
            "test_count": vocabulary_by_key[label]["test_count"],
            "status": vocabulary_by_key[label]["supported_status"],
        }
        for label in labels
    ]
    (output_dir / "labels.json").write_text(
        json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "supported-signs.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_SUPPORTED_SIGNS_V1",
                "model_name": MODEL_NAME,
                "vocabulary_scope": selected["vocabulary_scope"],
                "eligible_minimum_five_label_count": len(
                    benchmark["scope_benchmarks"][ALL_MIN5_SCOPE]["active_labels"]
                ),
                "vocabulary_size": len(labels),
                "label_integrity": {
                    "ambiguous_label_keys_excluded": split_report.get(
                        "ambiguous_label_keys_excluded", []
                    ),
                    "active_labels_disjoint_from_ambiguous_keys": not bool(
                        set(labels)
                        & set(split_report.get("ambiguous_label_keys_excluded", []))
                    ),
                },
                "signs": signs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "landmark-schema.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                "recognition_mode": "WORD_ISOLATED",
                "input_name": "landmarks",
                "input_shape": ["batch", 60, 75, 3],
                "pose_landmarks": 33,
                "left_hand_landmarks": 21,
                "right_hand_landmarks": 21,
                "coordinates": ["x", "y", "z"],
                "dtype": "float32",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "preprocessing.json").write_text(
        json.dumps(
            {
                "offline_only": True,
                "normalization": "shoulder_centered_v1",
                "frames": 60,
                "landmarks": 75,
                "coordinates": 3,
                "missing_landmarks": "zero_with_presence_mask_during_cache_creation",
                "temporal_sampling": "uniform_full_isolated_clip",
                "training_augmentation": {
                    "coordinate_noise_std": 0.003,
                    "frame_drop_max": 4,
                    "temporal_scale_range": [0.9, 1.1],
                    "coordinate_scale_range": [0.96, 1.04],
                    "translation_range": [-0.02, 0.02],
                    "horizontal_mirroring": False,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    calibration = dict(selected["calibration"])
    calibration["selection_split"] = "validation"
    calibration["validation"] = selected["validation_unknown"]
    calibration["test"] = selected["test_unknown"]
    (output_dir / "confidence-calibration.json").write_text(
        json.dumps(calibration, indent=2) + "\n", encoding="utf-8"
    )
    metrics = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "architecture": selected["architecture"],
        "vocabulary_scope": selected["vocabulary_scope"],
        "selection_basis": "validation_only",
        "vocabulary_size": len(labels),
        "test": selected["test"],
        "unknown_test": selected["test_unknown"],
        "latency": selected["latency"],
        "parameter_count": selected["parameter_count"],
        "training_duration_seconds": selected["training_duration_seconds"],
        "production_readiness": "LIMITED_LOCAL_BASELINE_NOT_SIGNER_VALIDATED",
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "classification-report.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["label_key", "precision", "recall", "f1", "support"]
        )
        writer.writeheader()
        writer.writerows(selected["test"]["per_class"])
    _write_confusion_matrix(
        output_dir / "confusion-matrix.png",
        selected["test"]["confusion_matrix"],
        labels,
    )
    (output_dir / "dataset-manifest-checksum.txt").write_text(
        dataset_manifest_checksum + "\n", encoding="utf-8"
    )
    (output_dir / "training-split-provenance.json").write_text(
        json.dumps(split_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "training-config.yaml").write_text(
        "\n".join(
            [
                f"model_name: {MODEL_NAME}",
                f"model_version: {MODEL_VERSION}",
                f"architecture: {selected['architecture']}",
                f"vocabulary_scope: {selected['vocabulary_scope']}",
                "schema_version: OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                f"vocabulary_size: {len(labels)}",
                f"seed: {config.seed}",
                f"epochs_requested: {config.epochs}",
                f"epochs_completed: {selected['epochs_completed']}",
                f"batch_size: {config.batch_size}",
                f"learning_rate: {config.learning_rate}",
                f"weight_decay: {config.weight_decay}",
                f"gradient_clip_norm: {config.gradient_clip_norm}",
                f"early_stopping_patience: {config.early_stopping_patience}",
                "class_weighted_loss: true",
                "balanced_sampling: true",
                "checkpoint_recovery: true",
                "horizontal_mirroring: false",
                "selection_split: validation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "candidate-benchmark.json").write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    onnx_report = export_onnx(
        model,
        output=output_dir / "model.onnx",
        labels=labels,
        validation_sample=splits["test"][0].path,
    )
    (output_dir / "onnx-validation.json").write_text(
        json.dumps(onnx_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "model-card.md").write_text(
        "\n".join(
            [
                "# MoSL Isolated Sign V1",
                "",
                f"- Supported signs: **{len(labels)}**",
                f"- Selected architecture: `{selected['architecture']}`",
                f"- Active vocabulary scope: `{selected['vocabulary_scope']}`",
                (
                    "- Minimum-five eligible labels audited: "
                    f"**{len(benchmark['scope_benchmarks'][ALL_MIN5_SCOPE]['active_labels'])}**"
                ),
                "- Input: `60 x 75 x 3` shoulder-centered landmarks",
                "- Dataset: only the native local OpenSigne MoSL video copy",
                "- Status: limited local baseline; not signer-validated production recognition",
                f"- Held-out Top-1: **{selected['test']['top1_accuracy']:.3f}**",
                f"- Held-out macro F1: **{selected['test']['macro_f1']:.3f}**",
                (
                    "- Held-out out-of-vocabulary rejection: "
                    f"**{selected['test_unknown']['unknown_rejection_rate']:.3f}**"
                ),
                "",
                "## Honest limitations",
                "",
                "Signer identity is unavailable, so signer-independent performance cannot be measured. ",
                "Each supported class has only five or six independent videos and exactly one test sample. ",
                "Metrics are therefore highly uncertain. Confidence thresholds were selected on validation ",
                "only, using a documented safety Pareto trade-off. Out-of-vocabulary rejection remains below ",
                "a production safety bar, so this package must not be promoted as production-ready. Excluded ",
                "labels are not claimed as recognized vocabulary. This is isolated-sign classification, not ",
                "continuous sign language translation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    checksum_files = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in {"checksums.json", "package-validation.json"}
    ]
    checksums = {path.name: sha256_file(path) for path in sorted(checksum_files)}
    (output_dir / "checksums.json").write_text(
        json.dumps(checksums, indent=2) + "\n", encoding="utf-8"
    )
    package_report = validate_model_package(output_dir)
    package_report["onnx"] = onnx_report
    (output_dir / "package-validation.json").write_text(
        json.dumps(package_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not package_report["valid"]:
        raise RuntimeError(f"model package validation failed: {package_report}")
    return package_report


def run_pipeline(
    *,
    config: TrainingConfig,
    output_dir: Path = MODEL_DIR,
    report_dir: Path = REPORT_DIR,
    resume: bool = False,
    verify_raw_checksums: bool = True,
) -> dict[str, Any]:
    _, vocabulary, eligible_split_report = build_local_audit(
        report_dir=report_dir,
        minimum_samples=5,
        seed=config.seed,
        verify_raw_checksums=verify_raw_checksums,
    )
    vocabulary_path = report_dir / "supported-sign-vocabulary-v1.json"
    dataset_manifest_checksum = str(vocabulary["dataset_manifest_checksum_sha256"])
    eligible_labels = sorted(str(label) for label in eligible_split_report["supported_labels"])
    lexical_labels = [label for label in eligible_labels if not label.isdecimal()]
    if len(eligible_labels) < 3 or len(lexical_labels) < 3:
        raise RuntimeError("min-5 eligible or lexical vocabulary is too small to benchmark")

    scope_reports = {
        ALL_MIN5_SCOPE: scoped_split_report(
            eligible_split_report,
            active_labels=eligible_labels,
            scope=ALL_MIN5_SCOPE,
        ),
        LEXICAL_MIN5_SCOPE: scoped_split_report(
            eligible_split_report,
            active_labels=lexical_labels,
            scope=LEXICAL_MIN5_SCOPE,
        ),
    }
    scope_data: dict[
        str, tuple[dict[str, int], dict[str, list[Any]]]
    ] = {}
    for scope, report in scope_reports.items():
        if not report["valid"] or any(
            int(report["counts"][split]) < len(report["supported_labels"])
            for split in ("train", "validation", "test")
        ):
            raise RuntimeError(f"invalid or incomplete {scope} split report")
        path = report_dir / f"model-v1-split-report-{scope.replace('_', '-')}.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        scope_data[scope] = samples_from_split_report(path)

    scope_results: dict[str, list[dict[str, Any]]] = {}
    scope_models: dict[str, dict[str, nn.Module]] = {}
    scope_selected: dict[str, dict[str, Any]] = {}
    for scope, (scope_label_index, scope_splits) in scope_data.items():
        results: list[dict[str, Any]] = []
        models: dict[str, nn.Module] = {}
        for architecture in ARCHITECTURES:
            candidate_dir = output_dir / "candidates" / scope / architecture
            model, result = fit_candidate(
                architecture,
                label_index=scope_label_index,
                splits=scope_splits,
                config=config,
                output_dir=candidate_dir,
                dataset_manifest_checksum=dataset_manifest_checksum,
                resume=resume,
            )
            result["vocabulary_scope"] = scope
            results.append(result)
            models[architecture] = model
        scope_results[scope] = results
        scope_models[scope] = models
        scope_selected[scope] = max(results, key=candidate_selection_key)

    selected_scope, scope_comparison = choose_vocabulary_scope(
        scope_selected[ALL_MIN5_SCOPE], scope_selected[LEXICAL_MIN5_SCOPE]
    )
    selected = scope_selected[selected_scope]
    selected_architecture = str(selected["architecture"])
    label_index, splits = scope_data[selected_scope]
    split_report = scope_reports[selected_scope]
    (report_dir / "model-v1-split-report.json").write_text(
        json.dumps(split_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_scoped_vocabulary(
        vocabulary_path,
        active_labels=list(label_index),
        selected_scope=selected_scope,
    )
    scope_benchmarks = {
        scope: {
            "active_labels": report["supported_labels"],
            "deferred_eligible_labels": report["deferred_eligible_labels"],
            "label_index": scope_data[scope][0],
            "split_counts": report["counts"],
            "unknown_calibration_count": len(report["unknown_calibration"]),
            "unknown_test_count": len(report["unknown_test"]),
            "candidates": scope_results[scope],
            "selected_architecture": scope_selected[scope]["architecture"],
            "selected_using_test_metrics": False,
        }
        for scope, report in scope_reports.items()
    }
    benchmark = {
        "schema_version": "OPEN_SIGNE_MODEL_BENCHMARK_V1",
        "selection_split": "validation",
        "selection_priority": [
            "macro_f1",
            "balanced_accuracy",
            "top1_accuracy",
            "top3_accuracy",
            "unknown_rejection",
            "p95_latency",
            "parameter_count",
        ],
        "same_dataset_preprocessing_and_evaluation": True,
        "same_split_and_label_index_within_each_scope": True,
        "scope_comparison": scope_comparison,
        "scope_benchmarks": scope_benchmarks,
        "selected_vocabulary_scope": selected_scope,
        "label_index": label_index,
        "split_counts": split_report["counts"],
        "candidates": scope_results[selected_scope],
        "selected_architecture": selected_architecture,
        "selected_using_test_metrics": False,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "model-v1-benchmark.json").write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    smoke_status = {
        "model_name": "mosl-word-smoke-v1",
        "status": "TECHNICAL_SMOKE_ONLY",
        "user_model": False,
        "production_ready": False,
        "labels": ["16", "17"],
        "replacement_model": MODEL_NAME,
        "replacement_package_validated": False,
    }
    (report_dir / "smoke-model-status.json").write_text(
        json.dumps(smoke_status, indent=2) + "\n", encoding="utf-8"
    )
    package_report = package_selected_model(
        model=scope_models[selected_scope][selected_architecture],
        selected=selected,
        benchmark=benchmark,
        label_index=label_index,
        splits=splits,
        split_report=split_report,
        vocabulary_path=vocabulary_path,
        output_dir=output_dir,
        config=config,
        dataset_manifest_checksum=dataset_manifest_checksum,
    )
    smoke_status["replacement_package_validated"] = bool(package_report["valid"])
    (report_dir / "smoke-model-status.json").write_text(
        json.dumps(smoke_status, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "selected_vocabulary_scope": selected_scope,
        "supported_labels": list(label_index),
        "selected_architecture": selected_architecture,
        "package": package_report,
        "test_metrics": selected["test"],
        "unknown_test": selected["test_unknown"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train, benchmark, calibrate and export the local MoSL V1 model."
    )
    parser.add_argument("--output-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-raw-checksums", action="store_true")
    args = parser.parse_args()
    config = TrainingConfig(
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        hidden_size=args.hidden_size,
        early_stopping_patience=args.patience,
    )
    print(
        json.dumps(
            run_pipeline(
                config=config,
                output_dir=args.output_dir,
                report_dir=args.report_dir,
                resume=args.resume,
                verify_raw_checksums=not args.skip_raw_checksums,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
