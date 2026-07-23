from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpenSign Darija Inference"
    app_version: str = "0.1.0"
    model_name: str = "mosl-isolated-sign-v1"
    model_version: str = "1.0.0"
    feature_schema_version: str = "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
    model_path: str | None = None
    labels_path: str | None = None
    supported_signs_path: str | None = None
    calibration_path: str | None = None
    model_checksum_required: bool = True
    model_max_size_bytes: int = 50_000_000
    model_warmup_enabled: bool = True
    inference_max_concurrent_requests: int = Field(default=4, ge=1, le=32)
    onnx_execution_provider: str = "CPUExecutionProvider"


@lru_cache
def get_settings() -> Settings:
    return Settings()
