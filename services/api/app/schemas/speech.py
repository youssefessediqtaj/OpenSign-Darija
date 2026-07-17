from datetime import datetime

from pydantic import BaseModel, Field


class SpeechVoiceResponse(BaseModel):
    id: str
    provider: str
    display_name: str
    language: str
    locale: str
    model_version: str
    license_info: dict[str, object]
    is_default: bool
    is_active: bool
    is_experimental: bool


class SpeechVoicesResponse(BaseModel):
    voices: list[SpeechVoiceResponse]


class SpeechStatusResponse(BaseModel):
    mode: str
    service_available: bool
    browser_fallback_enabled: bool
    voices_available: int


class SpeechGenerationRequest(BaseModel):
    voice_id: str = "darija-default"
    speed: float = Field(default=1.0, ge=0.75, le=1.5)
    format: str = "wav"
    text_source: str = "final_darija_arabic"
    sensitive_confirmed: bool = False


class SpeechAudioResponse(BaseModel):
    url: str
    mime_type: str
    duration_ms: int
    file_size_bytes: int
    expires_at: datetime


class SpeechProviderResponse(BaseModel):
    name: str
    model_version: str


class SpeechGenerationResponse(BaseModel):
    generation_id: str
    status: str
    cache_hit: bool
    estimated_mode: str = "synchronous"
    audio: SpeechAudioResponse | None = None
    voice: SpeechVoiceResponse | None = None
    provider: SpeechProviderResponse | None = None
    fallback_used: bool = False
    requested_language: str = "ary-MA"
    synthesis_language: str = "ary-MA"
    expires_at: datetime | None = None
    error_code: str | None = None
