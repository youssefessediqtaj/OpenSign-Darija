from time import perf_counter
from uuid import uuid4

import numpy as np

from app.core.config import get_settings
from app.models.mock_model import MockInferenceModel
from app.schemas.prediction import ModelInfo, PredictionResponse
from app.services.interfaces import InferenceModel, ModelRegistry


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
            status="completed",
            predictions=predictions,
            unknown_probability=0.03,
            processing_time_ms=elapsed_ms,
        )
