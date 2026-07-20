from time import perf_counter
from uuid import uuid4

from app.core.config import get_settings
from app.schemas.prediction import (
    ModelInfo,
    PredictionResponse,
    WordLandmarkSequenceRequest,
)
from app.services.model_loader import ModelLoader, model_loader


class PredictionService:
    def __init__(self, loader: ModelLoader | None = None) -> None:
        self.loader = loader or model_loader

    def predict_word(self, payload: WordLandmarkSequenceRequest) -> PredictionResponse:
        started = perf_counter()
        if self.loader.state != "READY" or self.loader.model is None:
            raise RuntimeError(self.loader.error or "model not loaded")

        predictions, decision, confidence_level, unknown_probability = self.loader.model.predict(
            payload
        )
        settings = get_settings()
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
