from __future__ import annotations

import numpy as np


def decision_from_probabilities(
    probabilities: np.ndarray,
    *,
    unknown_threshold: float,
    margin_threshold: float,
) -> tuple[str, str]:
    ordered = np.sort(probabilities)[::-1]
    max_probability = float(ordered[0])
    margin = float(ordered[0] - ordered[1]) if len(ordered) > 1 else max_probability
    if max_probability < unknown_threshold:
        return "unknown", "low"
    if margin < margin_threshold:
        return "uncertain", "medium"
    return "known", "high"
