from __future__ import annotations

import math

import numpy as np


def softmax(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    scaled = logits.astype(np.float64) / max(temperature, 1e-6)
    scaled -= scaled.max(axis=-1, keepdims=True)
    exp = np.exp(scaled)
    return (exp / exp.sum(axis=-1, keepdims=True)).astype(np.float32)


def expected_calibration_error(confidences: np.ndarray, correct: np.ndarray, bins: int = 10) -> float:
    ece = 0.0
    for lower in np.linspace(0, 1, bins, endpoint=False):
        upper = lower + 1 / bins
        mask = (confidences >= lower) & (confidences < upper)
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(correct[mask].mean()) - float(confidences[mask].mean()))
    return ece


def negative_log_likelihood(probabilities: np.ndarray, target_indices: np.ndarray) -> float:
    selected = probabilities[np.arange(len(target_indices)), target_indices]
    return float(-np.log(np.clip(selected, 1e-9, 1.0)).mean())


def calibrate_temperature(logits: np.ndarray, target_indices: np.ndarray) -> dict[str, float]:
    best_temperature = 1.0
    best_nll = math.inf
    for temperature in np.linspace(0.5, 5.0, 46):
        probabilities = softmax(logits, float(temperature))
        nll = negative_log_likelihood(probabilities, target_indices)
        if nll < best_nll:
            best_nll = nll
            best_temperature = float(temperature)
    probabilities = softmax(logits, best_temperature)
    confidences = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == target_indices
    return {
        "temperature": best_temperature,
        "nll": best_nll,
        "ece": expected_calibration_error(confidences, correct),
    }
