import numpy as np

from app.schemas.prediction import PredictionItem
from app.services.interfaces import InferenceModel


class MockInferenceModel(InferenceModel):
    def predict(self, sequence: np.ndarray) -> list[PredictionItem]:
        frame_factor = min(float(sequence.shape[0]) / 100.0, 1.0) if sequence.ndim > 0 else 0.0
        top_confidence = round(0.78 + frame_factor * 0.04, 2)
        return [
            PredictionItem(label="medecin", confidence=top_confidence, rank=1),
            PredictionItem(label="douleur", confidence=0.11, rank=2),
            PredictionItem(label="urgence", confidence=0.04, rank=3),
        ]
