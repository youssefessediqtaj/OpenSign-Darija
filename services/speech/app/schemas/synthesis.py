from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SynthesisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    language: Literal["ar-MA", "ar"] = "ar-MA"
    voice_id: str = Field(default="darija-default", min_length=1, max_length=80)
    speed: float = Field(default=1.0, ge=0.75, le=1.5)
    output_format: Literal["wav"] = "wav"


class AudioMetadata(BaseModel):
    mime_type: str
    extension: Literal["wav"]
    sample_rate: int
    channels: int
    duration_ms: int
    file_size_bytes: int
    checksum: str


class SynthesisResult(BaseModel):
    generation_id: str
    status: Literal["completed"]
    provider: str
    model_version: str
    requested_language: str
    synthesis_language: str
    fallback_used: bool
    original_text_hash: str
    normalized_text_hash: str
    normalized_text: str
    normalization_version: str
    audio_base64: str
    audio: AudioMetadata


class Voice(BaseModel):
    id: str
    provider: str
    voice_code: str
    display_name: str
    language: str
    locale: str
    gender_label: str | None = None
    description: str
    model_version: str
    license: str
    is_default: bool = False
    is_active: bool = True
    is_experimental: bool = True
    supports_speed: bool = True
