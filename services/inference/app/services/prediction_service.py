from time import perf_counter
from uuid import uuid4

import numpy as np

from app.core.config import get_settings
from app.models.mock_model import MockInferenceModel
from app.schemas.prediction import (
    AlphabetPredictionRequest,
    LandmarkSequenceRequest,
    ModelInfo,
    PredictionItem,
    PredictionResponse,
    WordLandmarkSequenceRequest,
)
from app.services.interfaces import InferenceModel, ModelRegistry
from app.services.model_loader import model_loader


class StaticModelRegistry(ModelRegistry):
    def __init__(self, model: InferenceModel | None = None) -> None:
        self._model = model or MockInferenceModel()

    def active_model(self) -> InferenceModel:
        return self._model


class PredictionService:
    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or StaticModelRegistry()

    def predict_mock(self, frames_count: int) -> PredictionResponse:
        started = perf_counter()
        fake_sequence = np.zeros((max(frames_count, 1), 21, 3), dtype=np.float32)
        predictions = sorted(
            self.registry.active_model().predict(fake_sequence), key=lambda item: item.rank
        )[:3]
        elapsed_ms = max(1, int((perf_counter() - started) * 1000))
        settings = get_settings()
        return PredictionResponse(
            request_id=str(uuid4()),
            model=ModelInfo(name=settings.model_name, version=settings.model_version),
            feature_schema_version=settings.feature_schema_version,
            inference_mode=settings.inference_mode,
            status="completed",
            decision="known",
            confidence_level="high",
            predictions=predictions,
            unknown_probability=0.03,
            processing_time_ms=elapsed_ms,
        )

    def predict_sequence(
        self, payload: LandmarkSequenceRequest | WordLandmarkSequenceRequest
    ) -> PredictionResponse:
        started = perf_counter()
        settings = get_settings()
        if settings.inference_mode == "real":
            if model_loader.model is None:
                raise RuntimeError(model_loader.error or "model not loaded")
            predictions, decision, confidence_level, unknown_probability = (
                model_loader.model.predict(payload)
            )
            return PredictionResponse(
                request_id=str(uuid4()),
                sequence_id=str(payload.sequence_id),
                model=ModelInfo(name=settings.model_name, version=settings.model_version),
                feature_schema_version=settings.feature_schema_version,
                inference_mode="real",
                status="completed",
                decision=decision,
                confidence_level=confidence_level,
                predictions=predictions,
                unknown_probability=round(unknown_probability, 4),
                processing_time_ms=max(1, int((perf_counter() - started) * 1000)),
            )
        labels = [
            "oui",
            "non",
            "aide",
            "eau",
            "medecin",
            "douleur",
            "merci",
            "vouloir",
            "ou",
            "urgence",
        ]
        seed = sum(ord(char) for char in str(payload.sequence_id))
        movement = payload.quality.movement_score
        hand_ratio = payload.quality.detected_hand_ratio
        base_index = int((seed + round(movement * 100) + round(hand_ratio * 10)) % len(labels))
        first = labels[base_index]
        second = labels[(base_index + 3) % len(labels)]
        third = labels[(base_index + 6) % len(labels)]
        top_confidence = round(min(0.82, max(0.62, 0.65 + movement * 0.12 + hand_ratio * 0.05)), 2)
        second_confidence = round(max(0.08, 0.16 - movement * 0.03), 2)
        third_confidence = round(max(0.04, 0.08 - hand_ratio * 0.02), 2)
        return PredictionResponse(
            request_id=str(uuid4()),
            sequence_id=str(payload.sequence_id),
            model=ModelInfo(name=settings.model_name, version=settings.model_version),
            feature_schema_version=payload.feature_schema_version,
            inference_mode=settings.inference_mode,
            status="completed",
            decision="known" if top_confidence >= 0.7 else "uncertain",
            confidence_level="high" if top_confidence >= 0.75 else "medium",
            predictions=[
                PredictionItem(label=first, confidence=top_confidence, rank=1),
                PredictionItem(label=second, confidence=second_confidence, rank=2),
                PredictionItem(label=third, confidence=third_confidence, rank=3),
            ],
            unknown_probability=round(
                max(0.02, 1 - top_confidence - second_confidence - third_confidence), 2
            ),
            processing_time_ms=max(1, int((perf_counter() - started) * 1000)),
        )

    def predict_alphabet(self, payload: AlphabetPredictionRequest) -> PredictionResponse:
        started = perf_counter()
        settings = get_settings()
        if settings.inference_mode == "real":
            raise RuntimeError("alphabet model not loaded")
        labels = [
            "ARABIC_LETTER_ALEF",
            "ARABIC_LETTER_BAA",
            "ARABIC_LETTER_TAA",
            "ARABIC_LETTER_THAA",
            "ARABIC_LETTER_JEEM",
        ]
        visible = sum(payload.presence_mask) / len(payload.presence_mask)
        seed = int(sum(abs(item) for item in payload.features) * 1000) + payload.stability_frames
        base_index = seed % len(labels)
        top_confidence = round(min(0.86, max(0.52, 0.56 + visible * 0.2)), 2)
        decision = "known" if top_confidence >= 0.65 else "uncertain"
        return PredictionResponse(
            request_id=str(uuid4()),
            sequence_id=str(payload.sequence_id),
            model=ModelInfo(name="opensign-mosl-alphabet-mock", version="0.1.0"),
            feature_schema_version=payload.feature_schema_version,
            inference_mode=settings.inference_mode,
            status="completed",
            decision=decision,
            confidence_level="medium" if decision == "known" else "low",
            predictions=[
                PredictionItem(label=labels[base_index], confidence=top_confidence, rank=1),
                PredictionItem(
                    label=labels[(base_index + 1) % len(labels)],
                    confidence=round(max(0.05, 0.18 - visible * 0.03), 2),
                    rank=2,
                ),
                PredictionItem(
                    label=labels[(base_index + 2) % len(labels)],
                    confidence=round(max(0.03, 0.1 - visible * 0.02), 2),
                    rank=3,
                ),
            ],
            unknown_probability=round(max(0.02, 1 - top_confidence), 2),
            processing_time_ms=max(1, int((perf_counter() - started) * 1000)),
        )
