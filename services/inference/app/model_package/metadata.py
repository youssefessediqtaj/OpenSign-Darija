from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelMetadata:
    name: str
    version: str
    status: str
    vocabulary_size: int
    feature_schema_version: str
    dataset_version: str | None
    labels: list[str]
    label_ar_by_key: dict[str, str]
    thresholds: dict[str, float]
    calibration: dict[str, float]
