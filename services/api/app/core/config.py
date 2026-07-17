from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "OpenSign Darija"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./opensign_dev.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-in-local-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    inference_service_url: str = "http://localhost:8001"
    inference_mode: str = "mock"
    inference_timeout_seconds: float = 3
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    recognition_max_frames: int = 60
    recognition_max_payload_bytes: int = 262_144
    recognition_min_duration_ms: int = 500
    recognition_max_duration_ms: int = 8000
    recognition_rate_limit: int = 30
    feature_schema_version: str = "1.0.0"
    minio_endpoint: str = "localhost:9000"
    minio_public_endpoint: str = "localhost:9000"
    minio_access_key: str = "opensign"
    minio_secret_key: str = "opensign_dev_password"
    minio_secure: bool = False
    dataset_presigned_url_expire_seconds: int = 600
    dataset_max_recordings_per_contribution: int = 8
    dataset_cleanup_draft_days: int = 14
    linguistic_engine_mode: str = "controlled"
    linguistic_engine_version: str = "1.0.0"
    linguistic_dictionary_version: str = "demo-1.0.0"
    linguistic_template_version: str = "demo-1.0.0"
    message_max_items: int = 30
    message_max_text_length: int = 1200
    message_max_revisions: int = 80
    message_autosave_delay_ms: int = 800
    message_history_enabled: bool = True
    guest_message_ttl_minutes: int = 120
    speech_service_url: str = "http://speech:8010"
    speech_mode: str = "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
