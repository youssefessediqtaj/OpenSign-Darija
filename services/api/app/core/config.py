from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpenSigne Darija"
    app_version: str = "1.0.0"
    inference_service_url: str = "http://localhost:8001"
    inference_timeout_seconds: float = 3
    supported_signs_path: str | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    recognition_max_payload_bytes: int = 1_500_000
    recognition_min_duration_ms: int = 500
    recognition_max_duration_ms: int = 8000
    recognition_rate_limit: int = 30
    recognition_min_usable_frames: int = 12
    recognition_min_hand_ratio: float = 0.35
    recognition_max_missing_frame_ratio: float = 0.5
    recognition_min_dynamic_movement: float = 0.04
    speech_service_url: str = "http://speech:8010"
    speech_generation_timeout_seconds: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
