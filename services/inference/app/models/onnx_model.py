from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.core.config import get_settings
from app.models.model_metadata import ModelMetadata
from app.schemas.prediction import LandmarkSequenceRequest, PredictionItem


class OnnxModel:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.model_path:
            raise FileNotFoundError("MODEL_PATH is required in real inference mode")
        model_path = Path(settings.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        if model_path.stat().st_size > settings.model_max_size_bytes:
            raise ValueError("ONNX model exceeds MODEL_MAX_SIZE_BYTES")
        labels_path = Path(settings.labels_path or "")
        if not labels_path.exists():
            raise FileNotFoundError("labels.json is required")
        thresholds_path = Path(settings.thresholds_path or "")
        calibration_path = Path(settings.calibration_path or "")
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        thresholds = (
            json.loads(thresholds_path.read_text(encoding="utf-8"))
            if thresholds_path.exists()
            else {}
        )
        calibration = (
            json.loads(calibration_path.read_text(encoding="utf-8"))
            if calibration_path.exists()
            else {}
        )
        if not isinstance(labels, list) or not labels:
            raise ValueError("labels.json must contain a non-empty list")

        import onnxruntime as ort  # type: ignore[import-untyped]

        providers = [settings.onnx_execution_provider]
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        self.metadata = ModelMetadata(
            name=settings.model_name,
            version=settings.model_version,
            status="active",
            vocabulary_size=len(labels),
            feature_schema_version=settings.feature_schema_version,
            dataset_version=None,
            labels=[str(label) for label in labels],
            thresholds={
                "unknown_threshold": float(thresholds.get("unknown_threshold", 0.6)),
                "margin_threshold": float(thresholds.get("margin_threshold", 0.15)),
            },
            calibration={"temperature": float(calibration.get("temperature", 1.0))},
        )

    def predict(
        self, payload: LandmarkSequenceRequest
    ) -> tuple[list[PredictionItem], str, str, float]:
        features = np.asarray([frame.features for frame in payload.frames], dtype=np.float32)[
            None, :, :
        ]
        mask = np.asarray([frame.presence_mask for frame in payload.frames], dtype=np.float32)[
            None, :, :
        ]
        logits = self.session.run(None, {"features": features, "presence_mask": mask})[0][0]
        temperature = max(self.metadata.calibration["temperature"], 1e-6)
        scaled = logits / temperature
        scaled -= scaled.max()
        exp = np.exp(scaled)
        probabilities = exp / exp.sum()
        order = np.argsort(probabilities)[::-1][:3]
        predictions = [
            PredictionItem(
                label=self.metadata.labels[int(index)],
                confidence=float(probabilities[int(index)]),
                rank=rank,
            )
            for rank, index in enumerate(order, start=1)
        ]
        top = float(probabilities[int(order[0])])
        margin = (
            float(probabilities[int(order[0])] - probabilities[int(order[1])])
            if len(order) > 1
            else top
        )
        if top < self.metadata.thresholds["unknown_threshold"]:
            return predictions, "unknown", "low", 1.0 - top
        if margin < self.metadata.thresholds["margin_threshold"]:
            return predictions, "uncertain", "medium", 1.0 - top
        return predictions, "known", "high", 1.0 - top
