"""Reproducible unvalidated GRU fitting/export smoke test for COLORS_V1 templates."""
from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
import torch

from ml.datasets.colors_v1.baseline import load
from ml.models.mosl_v1 import ModelSpec, build_model


def train(package: Path, output_dir: Path, *, epochs: int = 1, seed: int = 42) -> dict[str, Any]:
    """Fit in-sample only, export ONNX and measure numerical parity; never activate."""
    if epochs < 1 or epochs > 100:
        raise ValueError("epochs must be between 1 and 100")
    data = load(package)
    if data["metadata"].get("status") != "EXPERIMENTAL_NOT_VALIDATED":
        raise ValueError("expected an explicit experimental COLORS_V1 package")
    labels = sorted(set(str(x) for x in data["labels"]))
    if len(labels) < 2:
        raise ValueError("at least two semantic classes are required")
    if output_dir.exists():
        raise FileExistsError("output directory already exists")
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(1)
    model = build_model(ModelSpec("bidirectional_gru", len(labels), hidden_size=16, dropout=0.1))
    model.train()
    x = torch.from_numpy(data["templates"].astype(np.float32))
    y = torch.tensor([labels.index(str(label)) for label in data["labels"]], dtype=torch.long)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    losses = []
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(model(x), y)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    model.eval()
    output_dir.mkdir(parents=True, mode=0o700)
    try:
        with torch.no_grad():
            expected = model(x[:1]).numpy()
        onnx_path = output_dir / "model.onnx"
        torch.onnx.export(model, x[:1], str(onnx_path), input_names=["landmarks"], output_names=["logits"],
                          dynamic_axes={"landmarks": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17)
        onnx.checker.check_model(onnx.load(str(onnx_path)))
        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        actual = session.run(None, {"landmarks": x[:1].numpy()})[0]
        error = float(np.max(np.abs(expected - actual)))
        if not np.allclose(expected, actual, rtol=1e-4, atol=1e-5):
            raise ValueError("ONNX numerical parity check failed")
        checkpoint = output_dir / "checkpoint.pt"
        torch.save({"state_dict": model.state_dict(), "labels": labels, "seed": seed,
                    "manifest_sha256": data["metadata"]["manifest_sha256"]}, checkpoint)
        report = {"dataset": "colors_v1", "status": "SMOKE_ONLY_NOT_VALIDATED", "epochs": epochs,
                  "seed": seed, "architecture": "bidirectional_gru", "hidden_size": 16,
                  "sample_count": len(y), "labels": labels, "in_sample_loss": losses,
                  "feature_version": data["metadata"]["feature_version"],
                  "manifest_sha256": data["metadata"]["manifest_sha256"],
                  "python": platform.python_version(), "torch": torch.__version__,
                  "numpy": np.__version__, "onnx": onnx.__version__, "onnxruntime": ort.__version__,
                  "onnx_parity_max_abs_error": error, "independent_accuracy": "NOT_ESTABLISHED",
                  "calibration": "UNAVAILABLE", "activation": "DISABLED"}
        (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        for path in (onnx_path, checkpoint, output_dir / "report.json"):
            os.chmod(path, 0o600)
        return report
    except Exception:
        # Preserve partial artifacts for inspection instead of deleting an unexpected directory.
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(train(args.package, args.output_dir, epochs=args.epochs, seed=args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
