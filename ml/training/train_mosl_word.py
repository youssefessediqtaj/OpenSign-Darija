from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np


def require_torch() -> Any:
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise RuntimeError("PyTorch is required. Run `make ml-install`.") from exc
    return torch


class MoslWordGru:
    def __init__(self, class_count: int, hidden_size: int = 128) -> None:
        torch = require_torch()

        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.projection = torch.nn.Linear(225, hidden_size)
                self.encoder = torch.nn.GRU(
                    hidden_size,
                    hidden_size,
                    num_layers=2,
                    dropout=0.2,
                    bidirectional=True,
                    batch_first=True,
                )
                self.classifier = torch.nn.Linear(hidden_size * 2, class_count)

            def forward(self, landmarks: Any) -> Any:
                batch, frames, landmarks_per_frame, coordinates = landmarks.shape
                flattened = landmarks.reshape(batch, frames, landmarks_per_frame * coordinates)
                projected = torch.relu(self.projection(flattened))
                encoded, _ = self.encoder(projected)
                return self.classifier(encoded[:, -1, :])

        self.model = Model()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_npz(path: Path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as data:
        landmarks = data["landmarks"].astype(np.float32)
    if landmarks.shape != (60, 75, 3):
        raise ValueError(f"{path} must contain landmarks with shape 60 x 75 x 3")
    return landmarks


def load_manifest_samples(manifest_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    smoke_subset = manifest.get("smoke_subset", {})
    labels = sorted(smoke_subset)
    if len(labels) < 2:
        raise RuntimeError("Smoke training requires at least two eligible labels.")
    by_sha = {sample["source_sha256"]: sample for sample in manifest["samples"]}
    selected: list[dict[str, Any]] = []
    for label in labels:
        for sha in smoke_subset[label]:
            sample = by_sha[sha]
            if not sample.get("eligible"):
                raise RuntimeError(f"Smoke sample {sha} is not eligible.")
            selected.append(sample)
    return labels, selected


def make_batches(samples: list[dict[str, Any]], label_index: dict[str, int], batch_size: int) -> list[tuple[np.ndarray, np.ndarray]]:
    batches = []
    for offset in range(0, len(samples), batch_size):
        chunk = samples[offset : offset + batch_size]
        features = np.stack([load_npz(Path(sample["processed_landmark_path"])) for sample in chunk])
        labels = np.asarray([label_index[sample["label_key"]] for sample in chunk], dtype=np.int64)
        batches.append((features, labels))
    return batches


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def evaluate(model: Any, samples: list[dict[str, Any]], label_index: dict[str, int]) -> dict[str, Any]:
    torch = require_torch()
    model.eval()
    latencies: list[float] = []
    y_true: list[int] = []
    y_pred: list[int] = []
    probabilities: list[np.ndarray] = []
    with torch.no_grad():
        for sample in samples:
            features = load_npz(Path(sample["processed_landmark_path"]))[None, :, :, :]
            started = perf_counter()
            logits = model(torch.from_numpy(features)).numpy()
            latencies.append((perf_counter() - started) * 1000)
            probs = softmax(logits)[0]
            probabilities.append(probs)
            y_true.append(label_index[sample["label_key"]])
            y_pred.append(int(probs.argmax()))
    class_count = len(label_index)
    confusion = np.zeros((class_count, class_count), dtype=np.int64)
    for truth, pred in zip(y_true, y_pred, strict=True):
        confusion[truth, pred] += 1
    per_class = []
    for label, index in sorted(label_index.items(), key=lambda item: item[1]):
        tp = int(confusion[index, index])
        fp = int(confusion[:, index].sum() - tp)
        fn = int(confusion[index, :].sum() - tp)
        support = int(confusion[index, :].sum())
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        per_class.append(
            {
                "label": label,
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "f1": round(f1, 6),
                "support": support,
            }
        )
    total = max(len(y_true), 1)
    top1 = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth == pred) / total
    top3 = 0.0
    if class_count >= 3:
        top3 = sum(
            1 for truth, probs in zip(y_true, probabilities, strict=True) if truth in np.argsort(probs)[::-1][:3]
        ) / total
    supports = np.asarray([item["support"] for item in per_class], dtype=np.float32)
    f1s = np.asarray([item["f1"] for item in per_class], dtype=np.float32)
    return {
        "metric_scope": "SMOKE TEST ONLY - NOT PRODUCTION METRICS",
        "top1_accuracy": round(top1, 6),
        "top3_accuracy": round(top3, 6) if class_count >= 3 else None,
        "macro_precision": round(float(np.mean([item["precision"] for item in per_class])), 6),
        "macro_recall": round(float(np.mean([item["recall"] for item in per_class])), 6),
        "macro_f1": round(float(np.mean(f1s)), 6),
        "weighted_f1": round(float((f1s * supports).sum() / max(supports.sum(), 1)), 6),
        "average_inference_latency_ms": round(float(np.mean(latencies)), 6),
        "p95_inference_latency_ms": round(float(np.percentile(latencies, 95)), 6),
        "per_class": per_class,
        "confusion_matrix": confusion.tolist(),
    }


def write_plots(output_dir: Path, history: list[dict[str, float]], metrics: dict[str, Any]) -> None:
    import matplotlib.pyplot as plt

    epochs = [item["epoch"] for item in history]
    plt.figure(figsize=(6, 4))
    plt.plot(epochs, [item["train_loss"] for item in history], label="train_loss")
    plt.plot(epochs, [item["validation_loss"] for item in history], label="validation_loss")
    plt.title("SMOKE TEST ONLY")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "training-curves.png")
    plt.close()

    plt.figure(figsize=(4, 4))
    plt.imshow(metrics["confusion_matrix"], cmap="Blues")
    plt.title("SMOKE TEST ONLY")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(output_dir / "confusion-matrix.png")
    plt.close()


def export_and_validate_onnx(model: Any, output_dir: Path, validation_sample: dict[str, Any], labels: list[str]) -> dict[str, Any]:
    torch = require_torch()
    import onnx
    import onnxruntime as ort

    onnx_path = output_dir / "model.onnx"
    sample = load_npz(Path(validation_sample["processed_landmark_path"]))[None, :, :, :]
    tensor = torch.from_numpy(sample)
    model.eval()
    with torch.no_grad():
        torch_logits = model(tensor).numpy()
    torch.onnx.export(
        model,
        tensor,
        onnx_path,
        input_names=["landmarks"],
        output_names=["logits"],
        dynamic_axes={"landmarks": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    onnx.checker.check_model(str(onnx_path))
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    ort_logits = session.run(None, {"landmarks": sample})[0]
    max_diff = float(np.max(np.abs(torch_logits - ort_logits)))
    mean_diff = float(np.mean(np.abs(torch_logits - ort_logits)))
    torch_order = np.argsort(torch_logits[0])[::-1].tolist()
    ort_order = np.argsort(ort_logits[0])[::-1].tolist()
    report = {
        "status": "passed" if max_diff < 1e-4 and torch_order[:3] == ort_order[:3] else "failed",
        "input_name": "landmarks",
        "input_shape": ["batch", 60, 75, 3],
        "output_name": "logits",
        "output_shape": ["batch", len(labels)],
        "max_abs_diff": max_diff,
        "mean_abs_diff": mean_diff,
        "torch_top1": labels[torch_order[0]],
        "onnx_top1": labels[ort_order[0]],
        "torch_topk": [labels[index] for index in torch_order[: min(3, len(labels))]],
        "onnx_topk": [labels[index] for index in ort_order[: min(3, len(labels))]],
    }
    if report["status"] != "passed":
        raise RuntimeError(f"ONNX parity failed: {report}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the MoSL WORD_ISOLATED smoke model.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/datasets/mosl-word-isolated-v1/manifest.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/models/mosl-word-smoke-v1"))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    torch = require_torch()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    labels, samples = load_manifest_samples(args.manifest)
    label_index = {label: index for index, label in enumerate(labels)}
    train_samples = [sample for sample in samples if sample["split"] == "train"]
    validation_samples = [sample for sample in samples if sample["split"] == "validation"]
    if not train_samples or not validation_samples:
        raise RuntimeError("Smoke training requires train and validation samples.")

    model = MoslWordGru(class_count=len(labels)).model
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.CrossEntropyLoss()
    history: list[dict[str, float]] = []
    best_loss = float("inf")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        random.shuffle(train_samples)
        train_losses: list[float] = []
        for features, targets in make_batches(train_samples, label_index, args.batch_size):
            optimizer.zero_grad()
            logits = model(torch.from_numpy(features))
            loss = criterion(logits, torch.from_numpy(targets))
            if not torch.isfinite(loss):
                raise RuntimeError("NaN or infinite training loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_losses.append(float(loss.detach().numpy()))

        model.eval()
        validation_losses: list[float] = []
        with torch.no_grad():
            for features, targets in make_batches(validation_samples, label_index, args.batch_size):
                logits = model(torch.from_numpy(features))
                loss = criterion(logits, torch.from_numpy(targets))
                validation_losses.append(float(loss.detach().numpy()))
        validation_loss = float(np.mean(validation_losses))
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": round(float(np.mean(train_losses)), 6),
                "validation_loss": round(validation_loss, 6),
            }
        )
        checkpoint = {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "epoch": epoch,
            "label_index": label_index,
            "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
            "dataset_manifest_checksum": json.loads(args.manifest.read_text(encoding="utf-8"))[
                "dataset_manifest_checksum"
            ],
            "config": {"epochs": args.epochs, "batch_size": args.batch_size, "seed": args.seed},
        }
        torch.save(checkpoint, args.output_dir / "last-checkpoint.pt")
        if validation_loss <= best_loss:
            best_loss = validation_loss
            torch.save(checkpoint, args.output_dir / "best-checkpoint.pt")

    metrics = evaluate(model, validation_samples, label_index)
    parity = export_and_validate_onnx(model, args.output_dir, validation_samples[0], labels)
    write_plots(args.output_dir, history, metrics)
    (args.output_dir / "labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "landmark-schema.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                "recognition_mode": "WORD_ISOLATED",
                "landmarks": 75,
                "coordinates": 3,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "preprocessing.json").write_text(
        json.dumps({"normalization": "shoulder_centered_v1", "frames": 60}, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "training-history.json").write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "onnx-validation.json").write_text(json.dumps(parity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "error-analysis.json").write_text(
        json.dumps({"scope": "SMOKE TEST ONLY", "validation_samples": len(validation_samples)}, indent=2) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "classification-report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "precision", "recall", "f1", "support"])
        writer.writeheader()
        writer.writerows(metrics["per_class"])
    dataset_checksum = json.loads(args.manifest.read_text(encoding="utf-8"))["dataset_manifest_checksum"]
    (args.output_dir / "dataset-manifest-checksum.txt").write_text(dataset_checksum + "\n", encoding="utf-8")
    (args.output_dir / "model-card.md").write_text(
        "# MoSL Word Smoke Model\n\nStatus: VALIDATED_SMOKE, not production-ready.\n\n"
        "Metrics are SMOKE TEST ONLY and must not be interpreted as MoSL performance.\n",
        encoding="utf-8",
    )
    checksums = {
        path.name: sha256_file(path)
        for path in sorted(args.output_dir.iterdir())
        if path.is_file() and path.name != "checksums.json"
    }
    (args.output_dir / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_dir": args.output_dir.as_posix(),
                "labels": labels,
                "train_samples": len(train_samples),
                "validation_samples": len(validation_samples),
                "metrics": metrics,
                "onnx_validation": parity,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
