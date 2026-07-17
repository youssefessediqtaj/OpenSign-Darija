from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpenSign Darija Inference"
    app_version: str = "0.1.0"
    model_name: str = "opensign-darija-landmark-mock"
    model_version: str = "0.2.0"
    feature_schema_version: str = "1.0.0"
    inference_mode: str = "mock"
    active_model_id: str | None = None
    model_bucket: str = "opensign-model-artifacts"
    model_cache_dir: str = "/tmp/opensign-model-cache"
    model_path: str | None = None
    labels_path: str | None = None
    thresholds_path: str | None = None
    calibration_path: str | None = None
    model_download_timeout_seconds: float = 10
    model_load_timeout_seconds: float = 10
    model_warmup_enabled: bool = True
    model_checksum_required: bool = True
    model_max_size_bytes: int = 50_000_000
    onnx_execution_provider: str = "CPUExecutionProvider"
    inference_max_batch_size: int = 1
    inference_max_concurrent_requests: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
