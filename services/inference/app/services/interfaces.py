from abc import ABC, abstractmethod

import numpy as np

from app.schemas.prediction import PredictionItem


class LandmarkExtractor(ABC):
    @abstractmethod
    def extract(self, frames: list[np.ndarray]) -> np.ndarray:
        raise NotImplementedError


class SequencePreprocessor(ABC):
    @abstractmethod
    def transform(self, landmarks: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class InferenceModel(ABC):
    @abstractmethod
    def predict(self, sequence: np.ndarray) -> list[PredictionItem]:
        raise NotImplementedError


class ModelRegistry(ABC):
    @abstractmethod
    def active_model(self) -> InferenceModel:
        raise NotImplementedError
