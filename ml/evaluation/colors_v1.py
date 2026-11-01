"""Experimental semantic metrics and fail-closed decisions for future COLORS_V1 models.

These helpers do not calibrate scores or activate a runtime model. A threshold must be
selected separately from representative validation examples, including unknown signs.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any


def decide(label: str, score: float, threshold: float | None) -> dict[str, Any]:
    if not isinstance(label, str) or not label:
        raise ValueError("label must be nonempty")
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("score must be finite and between 0 and 1")
    if threshold is None:
        return {"status": "UNKNOWN_SIGN", "label": None, "score": score,
                "calibrated": False, "reason": "threshold unavailable"}
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be finite and between 0 and 1")
    return {"status": "RECOGNIZED_COLOR" if score >= threshold else "UNKNOWN_SIGN",
            "label": label if score >= threshold else None, "score": score,
            "calibrated": False, "reason": "threshold supplied; calibration not established"}


def evaluate(actual: list[str | None], predicted: list[str | None], labels: list[str]) -> dict[str, Any]:
    """Evaluate held-out semantic decisions; None represents an unknown sign/abstention."""
    if len(actual) != len(predicted) or not actual:
        raise ValueError("nonempty actual and predicted lists must have equal lengths")
    if not labels or len(set(labels)) != len(labels) or any(not x for x in labels):
        raise ValueError("labels must be unique and nonempty")
    allowed = set(labels)
    if any(x is not None and x not in allowed for x in actual + predicted):
        raise ValueError("unknown semantic label")
    matrix = {a: {p: 0 for p in [*labels, "UNKNOWN_SIGN"]} for a in [*labels, "UNKNOWN_SIGN"]}
    for truth, prediction in zip(actual, predicted, strict=True):
        matrix[truth or "UNKNOWN_SIGN"][prediction or "UNKNOWN_SIGN"] += 1
    per_class: dict[str, dict[str, Any]] = {}
    for label in labels:
        tp = sum(a == label and p == label for a, p in zip(actual, predicted, strict=True))
        fp = sum(a != label and p == label for a, p in zip(actual, predicted, strict=True))
        fn = sum(a == label and p != label for a, p in zip(actual, predicted, strict=True))
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
        per_class[label] = {"support": sum(a == label for a in actual), "precision": precision,
                            "recall": recall, "f1": f1}
    known = sum(a is not None for a in actual)
    unknown = len(actual) - known
    correct_known = sum(a is not None and a == p for a, p in zip(actual, predicted, strict=True))
    false_rejected = sum(a is not None and p is None for a, p in zip(actual, predicted, strict=True))
    false_accepted = sum(a is None and p is not None for a, p in zip(actual, predicted, strict=True))
    return {"sample_count": len(actual), "class_distribution": dict(Counter(a or "UNKNOWN_SIGN" for a in actual)),
            "accuracy": sum(a == p for a, p in zip(actual, predicted, strict=True)) / len(actual),
            "per_class": per_class, "confusion_matrix": matrix,
            "known_sign_recall": correct_known / known if known else None,
            "false_rejection_rate": false_rejected / known if known else None,
            "false_acceptance_rate": false_accepted / unknown if unknown else None,
            "unknown_rejection_rate": (unknown - false_accepted) / unknown if unknown else None,
            "limitations": ["Metrics describe only supplied observations; signer independence and calibration require separate evidence."]}


def evaluation_report(records: list[dict[str, Any]], labels: list[str], *, split: str,
                      training_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Summarize supplied decisions; independent test reports require disjoint evidence."""
    if split not in ("in_sample", "validation", "held_out_test"):
        raise ValueError("unsupported evaluation split")
    if not records:
        raise ValueError("no evaluation observations")
    if split != "in_sample":
        if not training_records:
            raise ValueError("training source metadata required for independent evaluation")
        for field in ("lineage_group_id", "signer_id", "file_hash"):
            if any(not isinstance(item.get(field), str) or not item[field].strip()
                   for item in [*records, *training_records]):
                raise ValueError(f"{field} is required to check independent evaluation")
            if {x[field] for x in records} & {x[field] for x in training_records}:
                raise ValueError(f"{field} overlaps training and evaluation")
    actual = [item.get("actual") for item in records]
    predicted = [item.get("predicted") for item in records]
    metrics = evaluate(actual, predicted, labels)
    return {"dataset": "colors_v1", "evaluation_split": split,
            "sample_count": len(records),
            "known_signer_count": len({x["signer_id"] for x in records if isinstance(x.get("signer_id"), str) and x["signer_id"]}),
            "declared_lineage_count": len({x["lineage_group_id"] for x in records if isinstance(x.get("lineage_group_id"), str) and x["lineage_group_id"]}),
            "signer_independence": "metadata_disjoint_unverified" if split != "in_sample" else "not_established",
            "metrics": metrics}


def calibration_readiness(validation: list[dict[str, Any]], training: list[dict[str, Any]],
                          test: list[dict[str, Any]]) -> dict[str, Any]:
    """Check evidence for a later calibration experiment; never choose a threshold."""
    blockers: list[str] = []
    if not validation or not any(item.get("actual") is not None for item in validation):
        blockers.append("known validation examples are required")
    if not validation or not any(item.get("actual") is None for item in validation):
        blockers.append("unknown validation examples are required")
    if not training or not test:
        blockers.append("training and separate held-out test metadata are required")
    for field in ("lineage_group_id", "signer_id", "file_hash"):
        partitions = (training, validation, test)
        if any(not isinstance(item.get(field), str) or not item[field].strip()
               for group in partitions for item in group):
            blockers.append(f"{field} is missing")
            continue
        sets = [{item[field] for item in group} for group in partitions]
        if any(sets[i] & sets[j] for i, j in ((0, 1), (0, 2), (1, 2))):
            blockers.append(f"{field} overlaps partitions")
    return {"ready_to_design_calibration": not blockers, "blockers": blockers,
            "calibration_status": "UNCALIBRATED", "threshold": None,
            "limitations": ["Identity and label claims require independent review; no threshold is computed."]}


def promotion_readiness(evidence: dict[str, Any]) -> dict[str, Any]:
    """Evaluate explicit evidence fields without changing model state or defining accuracy thresholds."""
    required = ("protocol_documented", "compatibility_passed", "independent_evaluation_complete",
                "known_and_unknown_calibration_complete", "rights_and_linguistic_review_complete")
    blockers = [field for field in required if evidence.get(field) is not True]
    if not isinstance(evidence.get("approver"), str) or not evidence["approver"].strip():
        blockers.append("approver")
    return {"eligible_for_manual_review": not blockers, "missing": blockers,
            "activation_status": "INACTIVE", "note": "No automatic promotion or universal threshold."}
