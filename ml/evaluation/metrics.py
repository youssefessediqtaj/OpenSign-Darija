from __future__ import annotations

import numpy as np


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> np.ndarray:
    index = {label: position for position, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for true, pred in zip(y_true, y_pred, strict=False):
        if true in index and pred in index:
            matrix[index[true], index[pred]] += 1
    return matrix


def classification_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict[str, object]:
    matrix = confusion_matrix(y_true, y_pred, labels)
    per_class: dict[str, dict[str, float | int]] = {}
    precisions = []
    recalls = []
    f1s = []
    supports = []
    for idx, label in enumerate(labels):
        tp = float(matrix[idx, idx])
        fp = float(matrix[:, idx].sum() - matrix[idx, idx])
        fn = float(matrix[idx, :].sum() - matrix[idx, idx])
        support = int(matrix[idx, :].sum())
        precision = tp / max(tp + fp, 1.0)
        recall = tp / max(tp + fn, 1.0)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)
    total = max(sum(supports), 1)
    return {
        "accuracy_top1": sum(true == pred for true, pred in zip(y_true, y_pred, strict=False)) / total,
        "macro_precision": float(np.mean(precisions)) if precisions else 0.0,
        "macro_recall": float(np.mean(recalls)) if recalls else 0.0,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "weighted_f1": float(np.average(f1s, weights=supports)) if sum(supports) else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def top_k_accuracy(y_true: list[str], ranked_predictions: list[list[str]], k: int) -> float:
    if not y_true:
        return 0.0
    hits = sum(true in predictions[:k] for true, predictions in zip(y_true, ranked_predictions, strict=False))
    return hits / len(y_true)
