from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpenSigne Darija"
    app_version: str = "1.0.0"
    colors_experimental_enabled: bool = False
    colors_experimental_token: str = ""
    colors_experimental_trusted_network: str = ""
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

    # Optional community contribution subsystem. Public collection is deliberately
    # fail-closed and remains independent from recognition, inference, and speech.
    contribution_collection_enabled: bool = False
    contribution_reference_videos_approved: bool = False
    data_controller_name: str = ""
    data_controller_address: str = ""
    data_controller_contact: str = ""
    data_processing_purpose: str = ""
    data_recipient_categories: str = ""
    data_model_collaborator_sharing: str = ""
    data_storage_location_category: str = ""
    data_retention_days: int | None = None
    data_rights_contact: str = ""
    cndp_procedure_type: str = ""
    cndp_receipt_or_authorization_reference: str = ""
    consent_notice_version: str = ""
    contribution_storage_backend: str = "local"
    contribution_storage_root: Path = Path("var/contributions")
    contribution_database_path: Path | None = None
    contribution_s3_bucket: str = ""
    contribution_s3_prefix: str = "contributions"
    contribution_s3_endpoint_url: str = ""
    contribution_s3_region: str = ""
    contribution_s3_server_side_encryption: str = "AES256"
    contribution_max_video_bytes: int = 25_000_000
    contribution_min_video_bytes: int = 1_024
    contribution_min_duration_seconds: float = 2.0
    contribution_max_duration_seconds: float = 10.0
    contribution_allowed_video_types: str = "video/webm,video/webm;codecs=vp9,video/webm;codecs=vp8"
    contribution_ffprobe_path: str = "ffprobe"
    contribution_ffmpeg_path: str = "ffmpeg"
    contribution_probe_timeout_seconds: float = 12.0
    contribution_rate_limit: int = 5
    contribution_readiness_dwell_ms: int = 1_000

    @field_validator("data_retention_days", mode="before")
    @classmethod
    def empty_optional_integer_is_unconfirmed(cls, value: object) -> object:
        return None if value == "" else value

    @property
    def contribution_database_file(self) -> Path:
        return self.contribution_database_path or (
            self.contribution_storage_root / "metadata" / "contributions.sqlite3"
        )

    @property
    def contribution_allowed_mime_types(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.contribution_allowed_video_types.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
