"""Bounded local COLORS_V1 memorization diagnostics; never an activation or evaluation tool."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
import torch
from torch import nn

from ml.datasets.colors_v1.baseline import check_features, distances
from ml.datasets.colors_v1.preprocess import FEATURE_VERSION
from ml.models.mosl_v1 import ModelSpec, build_model

LABELS = ["black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_verified(
    manifest: Path,
    source_root: Path,
    feature_dir: Path,
    asset: Path,
    *,
    allow_pending_review: bool = False,
) -> dict[str, Any]:
    """Fail closed on stale inputs; the caller explicitly requested local pending-review work."""
    records = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) != 10:
        raise ValueError("expected exactly ten source records")
    config_path = Path(__file__).resolve().parents[2] / "configs/colors_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mapping = {v: c["id"] for c in config["labels"] for v in c["variants"]}
    if sorted(set(mapping.values())) != LABELS or len(mapping) != 10:
        raise ValueError("incompatible color configuration")
    root = source_root.resolve(strict=True)
    legacy = (
        Path(__file__).resolve().parents[2] / "data/external/mosl-video-dataset"
    ).resolve()
    if root == legacy or root.is_relative_to(legacy) or legacy.is_relative_to(root):
        raise ValueError("source root overlaps the legacy dataset")
    asset_hash = sha256(asset)
    seen: set[str] = set()
    tensors, masks, rows, feature_hashes = [], [], [], {}
    for item in records:
        variant = item["sign_variant_id"]
        identifier = item["video_id"]
        if (
            variant in seen
            or variant not in mapping
            or mapping[variant] != item["semantic_label"]
        ):
            raise ValueError("duplicate or mismatched variant mapping")
        if identifier != variant:
            raise ValueError("unexpected feature identity")
        seen.add(variant)
        if item.get("local_experimental_training_permission") not in {
            "owner_confirmed",
            "owner_confirmed_2026-11-01",
        }:
            raise ValueError("local experimental training is not authorized")
        if item.get("linguistic_review_status") not in {"APPROVED", "PENDING_REVIEW"}:
            raise ValueError("source review status does not permit local diagnostics")
        if (
            item.get("linguistic_review_status") == "PENDING_REVIEW"
            and not allow_pending_review
        ):
            raise ValueError(
                "pending review requires explicit local diagnostic override"
            )
        source = root / item["file_path"]
        if (
            source.is_symlink()
            or not source.is_file()
            or not source.resolve().is_relative_to(root)
        ):
            raise ValueError("source file missing or outside source root")
        source_hash = sha256(source)
        if source_hash != item["file_hash"]:
            raise ValueError("source hash does not match manifest")
        feature = feature_dir / f"{identifier}.npz"
        if feature.is_symlink() or not feature.is_file():
            raise ValueError("feature missing or symlinked")
        with np.load(feature, allow_pickle=False) as data:
            x = data["landmarks"].astype(np.float32)
            mask = data["presence_mask"].astype(np.float32)
            times = data["sampled_source_times_seconds"].astype(np.float64)
            metadata = json.loads(str(data["metadata"].item()))
        check_features(x, mask)
        valid_frames = metadata.get("valid_frames")
        detector_frames = metadata.get("detector_frames")
        if not isinstance(valid_frames, int) or valid_frames < 2:
            raise ValueError("invalid distinct source frame count")
        if detector_frames is not None and (
            not isinstance(detector_frames, int) or detector_frames < valid_frames
        ):
            raise ValueError("valid frame count exceeds detector frame count")
        if (
            times.shape != (60,)
            or not np.isfinite(times).all()
            or np.any(np.diff(times) < 0)
        ):
            raise ValueError("invalid sampled timestamps")
        if (
            metadata.get("source_sha256") != source_hash
            or metadata.get("video_id") != identifier
            or metadata.get("semantic_label") != item["semantic_label"]
            or metadata.get("sign_variant_id") != variant
            or metadata.get("feature_version") != FEATURE_VERSION
            or metadata.get("asset_sha256") != asset_hash
        ):
            raise ValueError("feature provenance mismatch")
        if not np.array_equal(x[mask == 0], np.zeros_like(x[mask == 0])):
            raise ValueError("masked landmarks must be zero")
        if not np.any(mask[:, 33:]):
            raise ValueError("missing all hands")
        tensors.append(x)
        masks.append(mask)
        feature_hashes[variant] = sha256(feature)
        rows.append(
            {
                "semantic_label": item["semantic_label"],
                "sign_variant": variant,
                "source_filename": source.name,
                "source_sha256": source_hash,
                "shape": list(x.shape),
                "source_valid_frames": int(metadata["valid_frames"]),
                "unique_sampled_timestamps": int(np.unique(times).size),
                "repeated_resampled_frames": int(60 - np.unique(times).size),
                "valid_landmark_fraction": float(mask.mean()),
                "missing_landmark_fraction": float(1 - mask.mean()),
                "hand_point_fraction": float(mask[:, 33:].mean()),
                "finite": bool(np.isfinite(x).all()),
                "min": float(x.min()),
                "max": float(x.max()),
                "mean": float(x.mean()),
                "std": float(x.std()),
                "nonzero_coordinates": int(np.count_nonzero(x)),
                "segment_method": metadata.get("segmentation_method"),
            }
        )
    if seen != set(mapping):
        raise ValueError("incomplete variant set")
    return {
        "manifest_sha256": sha256(manifest),
        "asset_sha256": asset_hash,
        "feature_sha256": feature_hashes,
        "rows": rows,
        "tensors": np.stack(tensors),
        "masks": np.stack(masks),
        "labels": [r["semantic_label"] for r in rows],
    }


def gradient_summary(model: nn.Module) -> dict[str, Any]:
    grads = [p.grad for p in model.parameters() if p.requires_grad]
    present = [g for g in grads if g is not None]
    finite = bool(present and all(torch.isfinite(g).all().item() for g in present))
    norm = (
        float(torch.sqrt(sum(torch.sum(g.detach() ** 2) for g in present)))
        if present
        else 0.0
    )
    return {
        "finite": finite,
        "nonzero": norm > 0,
        "global_l2": norm,
        "parameter_tensors_with_grad": len(present),
        "parameter_tensors": len(grads),
    }


def dtw_distance(a: np.ndarray, am: np.ndarray, b: np.ndarray, bm: np.ndarray) -> float:
    """Uncalibrated temporal distance with shared-landmark masking and no acceptance threshold."""
    weights = np.ones(75, dtype=np.float64)
    weights[33:] = 2
    shared = am[:, None, :] * bm[None, :, :] * weights[None, None, :]
    denominator = shared.sum(axis=2)
    squared = ((a[:, None, :, :] - b[None, :, :, :]) ** 2).sum(axis=3)
    local = np.divide(
        (squared * shared).sum(axis=2),
        denominator,
        out=np.full(denominator.shape, np.inf),
        where=denominator > 0,
    )
    costs = np.full((61, 61), np.inf)
    lengths = np.zeros((61, 61), dtype=np.int32)
    costs[0, 0] = 0
    for i in range(1, 61):
        for j in range(1, 61):
            choices = (costs[i - 1, j], costs[i, j - 1], costs[i - 1, j - 1])
            choice = int(np.argmin(choices))
            pi, pj = ((i - 1, j), (i, j - 1), (i - 1, j - 1))[choice]
            costs[i, j] = local[i - 1, j - 1] + costs[pi, pj]
            lengths[i, j] = lengths[pi, pj] + 1
    return float(costs[60, 60] / lengths[60, 60]) if lengths[60, 60] else float("inf")


def snapshot(model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> dict[str, Any]:
    model.eval()
    with torch.no_grad():
        logits = model(x)
        loss = nn.functional.cross_entropy(logits, y)
    return {
        "loss": float(loss),
        "correct_count": int((logits.argmax(1) == y).sum()),
        "logits": logits.numpy().tolist(),
    }


def checkpoint_probe(
    path: Path, data: dict[str, Any], x: torch.Tensor, y: torch.Tensor
) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if checkpoint.get("labels") != LABELS:
        raise ValueError("checkpoint label mapping is incompatible")
    model = build_model(
        ModelSpec("bidirectional_gru", len(LABELS), hidden_size=16, dropout=0.1)
    )
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    result = snapshot(model, x, y)
    result["checkpoint_manifest_sha256"] = checkpoint.get("manifest_sha256")
    result["matches_current_manifest"] = (
        checkpoint.get("manifest_sha256") == data["manifest_sha256"]
    )
    result["checkpoint_sha256"] = sha256(path)
    model.train()
    model.zero_grad(set_to_none=True)
    nn.functional.cross_entropy(model(x), y).backward()
    result["gradient"] = gradient_summary(model)
    return result


def run(
    manifest: Path,
    source_root: Path,
    feature_dir: Path,
    asset: Path,
    output: Path,
    old_checkpoint: Path,
    clean_smoke_checkpoint: Path,
    *,
    max_epochs: int = 120,
    seed: int = 42,
    allow_pending_review: bool = False,
) -> dict[str, Any]:
    if max_epochs < 1 or max_epochs > 120:
        raise ValueError("max_epochs must be between 1 and 120")
    if output.exists():
        raise FileExistsError("refusing to overwrite any experiment")
    torch.set_num_threads(1)
    data = load_verified(
        manifest,
        source_root,
        feature_dir,
        asset,
        allow_pending_review=allow_pending_review,
    )
    x = torch.from_numpy(data["tensors"])
    y = torch.tensor(
        [LABELS.index(label) for label in data["labels"]], dtype=torch.long
    )
    if set(y.tolist()) != set(range(9)) or len(data["labels"]) != 10:
        raise ValueError("expected all nine classes and ten examples")
    torch.manual_seed(seed)
    model = build_model(ModelSpec("bidirectional_gru", 9, hidden_size=16, dropout=0.1))
    initial = snapshot(model, x, y)
    old_probe = checkpoint_probe(old_checkpoint, data, x, y)
    clean_probe = checkpoint_probe(clean_smoke_checkpoint, data, x, y)
    # Probes initialize/load models and must not alter the predeclared training RNG stream.
    torch.manual_seed(seed)
    model = build_model(ModelSpec("bidirectional_gru", 9, hidden_size=16, dropout=0.1))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=0.01)
    history, training_losses, stable, last_gradient = [], [], 0, {}
    for epoch in range(1, max_epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(x), y)
        if not torch.isfinite(loss):
            raise ValueError("non-finite training loss")
        loss.backward()
        last_gradient = gradient_summary(model)
        if not last_gradient["finite"] or not last_gradient["nonzero"]:
            raise ValueError("gradient failure")
        optimizer.step()
        training_losses.append(float(loss.detach()))
        if epoch == 1 or epoch % 5 == 0 or epoch == max_epochs:
            evaluation = snapshot(model, x, y)
            history.append(
                {
                    "epoch": epoch,
                    "train_loss_dropout": float(loss.detach()),
                    "in_sample_eval_loss": evaluation["loss"],
                    "in_sample_correct": evaluation["correct_count"],
                    "in_sample_predictions": [
                        LABELS[int(i)]
                        for i in np.asarray(evaluation["logits"]).argmax(axis=1)
                    ],
                    "gradient": last_gradient,
                }
            )
            if evaluation["correct_count"] == len(y) and evaluation["loss"] < 0.25:
                stable += 1
            else:
                stable = 0
            if stable >= 3:
                break
    final = snapshot(model, x, y)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    checkpoint = output / "checkpoint.pt"
    onnx_path = output / "model.onnx"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "labels": LABELS,
            "manifest_sha256": data["manifest_sha256"],
            "feature_sha256": data["feature_sha256"],
            "feature_version": FEATURE_VERSION,
            "model_spec": {
                "name": "bidirectional_gru",
                "class_count": 9,
                "hidden_size": 16,
                "dropout": 0.1,
            },
            "status": "EXPERIMENTAL_INACTIVE",
            "calibration": "UNAVAILABLE",
        },
        checkpoint,
    )
    model.eval()
    torch.onnx.export(
        model,
        x[:1],
        str(onnx_path),
        input_names=["landmarks"],
        output_names=["logits"],
        dynamic_axes={"landmarks": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    onnx.checker.check_model(onnx.load(str(onnx_path)))
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    onnx_logits = session.run(None, {"landmarks": data["tensors"]})[0]
    expected = np.asarray(final["logits"], dtype=np.float32)
    max_error = float(np.max(np.abs(onnx_logits - expected)))
    if not np.allclose(expected, onnx_logits, rtol=1e-4, atol=1e-5):
        raise ValueError("ONNX parity failed")
    batch_parity = {}
    for size in (1, 2, len(data["tensors"])):
        batch_output = session.run(None, {"landmarks": data["tensors"][:size]})[0]
        batch_expected = expected[:size]
        error = float(np.max(np.abs(batch_output - batch_expected)))
        matches = bool(np.array_equal(batch_output.argmax(1), batch_expected.argmax(1)))
        if (
            not np.allclose(batch_output, batch_expected, rtol=1e-4, atol=1e-5)
            or not matches
        ):
            raise ValueError("ONNX batch parity failed")
        batch_parity[str(size)] = {"max_abs_error": error, "argmax_matches": matches}
    restored = build_model(
        ModelSpec("bidirectional_gru", 9, hidden_size=16, dropout=0.1)
    )
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    restored.load_state_dict(saved["state_dict"], strict=True)
    if not np.allclose(
        np.asarray(snapshot(restored, x, y)["logits"]), expected, rtol=1e-6, atol=1e-6
    ):
        raise ValueError("checkpoint reload mismatch")
    temporal = np.array(
        [
            [
                dtw_distance(a, am, b, bm)
                for b, bm in zip(data["tensors"], data["masks"], strict=True)
            ]
            for a, am in zip(data["tensors"], data["masks"], strict=True)
        ]
    )
    comparisons = []
    for i, row in enumerate(data["rows"]):
        direct = distances(
            data["tensors"][i], data["masks"][i], data["tensors"], data["masks"]
        )
        d_others, t_others = direct.copy(), temporal[i].copy()
        d_others[i] = np.inf
        t_others[i] = np.inf
        pred = int(np.argmax(onnx_logits[i]))
        comparisons.append(
            {
                **row,
                "expected_index": int(y[i]),
                "predicted_label": LABELS[pred],
                "predicted_index": pred,
                "raw_logits": onnx_logits[i].tolist(),
                "correct_in_sample": pred == int(y[i]),
                "template_self_distance": float(direct[i]),
                "template_nearest_other_variant": data["rows"][
                    int(np.argmin(d_others))
                ]["sign_variant"],
                "template_nearest_other_distance": float(np.min(d_others)),
                "dtw_self_distance": float(temporal[i, i]),
                "dtw_nearest_other_variant": data["rows"][int(np.argmin(t_others))][
                    "sign_variant"
                ],
                "dtw_nearest_other_distance": float(np.min(t_others)),
            }
        )
    report = {
        "experiment_id": output.name,
        "dataset": "colors_v1",
        "manifest_sha256": data["manifest_sha256"],
        "asset_sha256": data["asset_sha256"],
        "feature_sha256": data["feature_sha256"],
        "feature_version": FEATURE_VERSION,
        "labels": LABELS,
        "label_mapping": {label: i for i, label in enumerate(LABELS)},
        "status": "EXPERIMENTAL_INACTIVE",
        "calibration": "UNAVAILABLE",
        "evaluation": "NO_INDEPENDENT_EVALUATION",
        "pending_review_override": allow_pending_review,
        "training_config": {
            "seed": seed,
            "max_epochs": max_epochs,
            "epochs_run": epoch,
            "optimizer": "AdamW",
            "learning_rate": 0.003,
            "weight_decay": 0.01,
            "batch_size": 10,
            "loss": "cross_entropy",
            "dropout": 0.1,
            "hidden_size": 16,
            "early_stop": "3 evaluation checks with 10/10 and in-sample cross-entropy < 0.25; checked every 5 epochs",
        },
        "initial": initial,
        "final": final,
        "history": history,
        "training_loss_every_epoch": training_losses,
        "historical_checkpoint_on_clean_features": old_probe,
        "clean_smoke_checkpoint": clean_probe,
        "onnx_parity_max_abs": max_error,
        "onnx_batch_parity": batch_parity,
        "versions": {
            "python": platform.python_version(),
            "torch": str(torch.__version__),
            "numpy": np.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
        },
        "onnx_input_shape": session.get_inputs()[0].shape,
        "onnx_output_shape": list(onnx_logits.shape),
        "onnx_argmax_matches_pytorch": bool(
            np.array_equal(onnx_logits.argmax(1), expected.argmax(1))
        ),
        "examples": comparisons,
        "checkpoint_sha256": sha256(checkpoint),
        "onnx_sha256": sha256(onnx_path),
    }
    report_path = output / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for file in (checkpoint, onnx_path, report_path):
        os.chmod(file, 0o600)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--allow-pending-review",
        action="store_true",
        help="allow owner-authorized local diagnostics on pending-review data",
    )
    parser.add_argument("--old-checkpoint", type=Path, required=True)
    parser.add_argument("--clean-smoke-checkpoint", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        args.manifest,
        args.source_root,
        args.features,
        args.asset,
        args.output,
        args.old_checkpoint,
        args.clean_smoke_checkpoint,
        allow_pending_review=args.allow_pending_review,
    )
    print(
        json.dumps(
            {
                "experiment": result["experiment_id"],
                "status": result["status"],
                "epochs": result["training_config"]["epochs_run"],
                "initial_loss": result["initial"]["loss"],
                "final_loss": result["final"]["loss"],
                "in_sample_correct": result["final"]["correct_count"],
                "onnx_parity_max_abs": result["onnx_parity_max_abs"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
