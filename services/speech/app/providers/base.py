from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.voice import Voice


@dataclass(frozen=True)
class SynthesisInput:
    text: str
    language: str
    voice_id: str
    speed: float
    output_format: str


@dataclass(frozen=True)
class SynthesisOutput:
    audio_bytes: bytes
    sample_rate: int
    duration_ms: int
    format: str
    provider: str
    model_version: str
    synthesis_language: str
    fallback_used: bool


class SpeechProvider(ABC):
    @abstractmethod
    def is_ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_voices(self) -> list[Voice]:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, request: SynthesisInput) -> SynthesisOutput:
        raise NotImplementedError
