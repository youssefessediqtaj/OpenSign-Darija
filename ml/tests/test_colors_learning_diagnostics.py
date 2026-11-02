"""Regression checks for provenance, class mapping, gradients and inactive exports."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from ml.datasets.colors_v1.learning_diagnostics import (
    LABELS,
    dtw_distance,
    load_verified,
    run,
)
from ml.models.mosl_v1 import ModelSpec, build_model

ROOT = Path(__file__).resolve().parents[2]


def fixture_data(tmp_path: Path) -> dict[str, Path]:
    root, features = tmp_path / "source", tmp_path / "features"
    root.mkdir()
    features.mkdir()
    asset = tmp_path / "model.task"
    asset.write_bytes(b"test asset")
    asset_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    config = json.loads((ROOT / "ml/configs/colors_v1.json").read_text())
    rows = []
    for group in config["labels"]:
        for variant in group["variants"]:
            source = root / f"{variant}.mp4"
            source.write_bytes(variant.encode())
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            row = {
                "video_id": variant,
                "semantic_label": group["id"],
                "sign_variant_id": variant,
                "file_path": source.name,
                "file_hash": source_hash,
                "local_experimental_training_permission": "owner_confirmed",
                "linguistic_review_status": "PENDING_REVIEW",
            }
            rows.append(row)
            points = np.full((60, 75, 3), 0.01 * (len(rows)), dtype=np.float32)
            mask = np.ones((60, 75), dtype=np.float32)
            metadata = {
                "source_sha256": source_hash,
                "video_id": variant,
                "semantic_label": group["id"],
                "sign_variant_id": variant,
                "feature_version": "COLORS_V1_VIDEO_V1_EXPERIMENTAL",
                "asset_sha256": asset_hash,
                "valid_frames": 60,
            }
            np.savez(
                features / f"{variant}.npz",
                landmarks=points,
                presence_mask=mask,
                sampled_source_times_seconds=np.arange(60) / 24,
                metadata=json.dumps(metadata),
            )
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(rows))
    return {"root": root, "features": features, "asset": asset, "manifest": manifest}


def test_verified_inputs_fail_closed_on_source_or_feature_mismatch(
    tmp_path: Path,
) -> None:
    f = fixture_data(tmp_path)
    with pytest.raises(ValueError, match="pending review"):
        load_verified(f["manifest"], f["root"], f["features"], f["asset"])
    data = load_verified(
        f["manifest"], f["root"], f["features"], f["asset"], allow_pending_review=True
    )
    assert data["tensors"].shape == (10, 60, 75, 3)
    assert sorted(set(data["labels"])) == LABELS
    assert data["labels"].count("blue") == 2
    old_hash = data["manifest_sha256"]
    rows = json.loads(f["manifest"].read_text())
    (f["root"] / rows[0]["file_path"]).write_bytes(b"changed source")
    with pytest.raises(ValueError, match="source hash"):
        load_verified(
            f["manifest"],
            f["root"],
            f["features"],
            f["asset"],
            allow_pending_review=True,
        )
    (f["root"] / rows[0]["file_path"]).write_bytes(rows[0]["sign_variant_id"].encode())
    rows[0]["file_hash"] = "0" * 64
    f["manifest"].write_text(json.dumps(rows))
    assert hashlib.sha256(f["manifest"].read_bytes()).hexdigest() != old_hash
    with pytest.raises(ValueError, match="source hash"):
        load_verified(
            f["manifest"],
            f["root"],
            f["features"],
            f["asset"],
            allow_pending_review=True,
        )


def test_feature_cache_from_another_source_is_rejected(tmp_path: Path) -> None:
    f = fixture_data(tmp_path)
    feature = next(f["features"].glob("*.npz"))
    with np.load(feature, allow_pickle=False) as package:
        saved = {key: package[key].copy() for key in package.files}
    metadata = json.loads(str(saved["metadata"].item()))
    metadata["source_sha256"] = "0" * 64
    saved["metadata"] = np.asarray(json.dumps(metadata))
    np.savez(feature, **saved)
    with pytest.raises(ValueError, match="feature provenance"):
        load_verified(
            f["manifest"],
            f["root"],
            f["features"],
            f["asset"],
            allow_pending_review=True,
        )


def test_invalid_feature_rejected_and_temporal_distance_has_no_acceptance_threshold(
    tmp_path: Path,
) -> None:
    f = fixture_data(tmp_path)
    data = load_verified(
        f["manifest"], f["root"], f["features"], f["asset"], allow_pending_review=True
    )
    assert (
        dtw_distance(
            data["tensors"][0], data["masks"][0], data["tensors"][0], data["masks"][0]
        )
        == 0
    )
    path = next(f["features"].glob("*.npz"))
    with np.load(path, allow_pickle=False) as npz:
        saved = {key: npz[key].copy() for key in npz.files}
    saved["landmarks"][0, 0, 0] = np.nan
    np.savez(path, **saved)
    with pytest.raises(ValueError, match="finite"):
        load_verified(
            f["manifest"],
            f["root"],
            f["features"],
            f["asset"],
            allow_pending_review=True,
        )


def test_label_mapping_agrees_across_model_gateway_and_frontend() -> None:
    config = json.loads((ROOT / "ml/configs/colors_v1.json").read_text())
    assert sorted(item["id"] for item in config["labels"]) == LABELS
    blue = next(item for item in config["labels"] if item["id"] == "blue")
    assert sorted(blue["variants"]) == ["blue_variant_01", "blue_variant_02"]
    runtime = ast.parse(
        (ROOT / "services/inference/app/runtime/colors_model.py").read_text()
    )
    assign = next(
        node
        for node in runtime.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "LABELS"
            for target in node.targets
        )
    )
    assert ast.literal_eval(assign.value) == LABELS
    gateway = ast.parse(
        (ROOT / "services/api/app/api/v1/colors_experimental.py").read_text()
    )
    color_type = next(
        node.value
        for node in gateway.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "ColorLabel"
            for target in node.targets
        )
    )
    assert isinstance(color_type, ast.Subscript) and isinstance(
        color_type.slice, ast.Tuple
    )
    assert [ast.literal_eval(node) for node in color_type.slice.elts] == LABELS
    source = (
        ROOT / "apps/web/src/features/recognition/components/RecognitionWorkspace.tsx"
    ).read_text()
    declaration = re.search(
        r"const COLOR_LABELS: Record<string, string> = \{(.*?)\n\};", source, re.S
    )
    assert declaration is not None
    assert sorted(re.findall(r"\b([a-z]+):\s*'", declaration.group(1))) == LABELS


def test_training_gradients_checkpoint_and_onnx_are_inactive(tmp_path: Path) -> None:
    f = fixture_data(tmp_path)
    model = build_model(ModelSpec("bidirectional_gru", 9, hidden_size=16, dropout=0.1))
    x = torch.ones((2, 60, 75, 3))
    y = torch.tensor([0, 1])
    loss = nn.functional.cross_entropy(model(x), y)
    loss.backward()
    assert torch.isfinite(loss).item()
    assert all(
        p.grad is not None and torch.isfinite(p.grad).all().item()
        for p in model.parameters()
    )
    assert (
        sum(float(p.grad.abs().sum()) for p in model.parameters() if p.grad is not None)
        > 0
    )
    checkpoints = []
    for name, fingerprint in [
        ("old.pt", "old-manifest"),
        ("clean.pt", hashlib.sha256(f["manifest"].read_bytes()).hexdigest()),
    ]:
        path = tmp_path / name
        torch.save(
            {
                "state_dict": model.state_dict(),
                "labels": LABELS,
                "manifest_sha256": fingerprint,
            },
            path,
        )
        checkpoints.append(path)
    result = run(
        f["manifest"],
        f["root"],
        f["features"],
        f["asset"],
        tmp_path / "experiment",
        checkpoints[0],
        checkpoints[1],
        max_epochs=2,
        allow_pending_review=True,
    )
    assert result["status"] == "EXPERIMENTAL_INACTIVE"
    assert result["calibration"] == "UNAVAILABLE"
    assert result["evaluation"] == "NO_INDEPENDENT_EVALUATION"
    assert result["training_config"]["epochs_run"] == 2
    assert (
        result["historical_checkpoint_on_clean_features"]["matches_current_manifest"]
        is False
    )
    assert result["clean_smoke_checkpoint"]["matches_current_manifest"] is True
    assert len(result["history"][0]["in_sample_predictions"]) == 10
    assert result["onnx_batch_parity"]["1"]["argmax_matches"] is True
    assert result["onnx_batch_parity"]["10"]["argmax_matches"] is True
    assert result["onnx_argmax_matches_pytorch"] is True
    assert result["onnx_parity_max_abs"] < 1e-5
    assert len(result["examples"]) == 10 and all(
        len(item["raw_logits"]) == 9 for item in result["examples"]
    )
    with pytest.raises(FileExistsError):
        run(
            f["manifest"],
            f["root"],
            f["features"],
            f["asset"],
            tmp_path / "experiment",
            checkpoints[0],
            checkpoints[1],
            max_epochs=2,
            allow_pending_review=True,
        )
