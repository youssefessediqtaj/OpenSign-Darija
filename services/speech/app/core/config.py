from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    speech_mode: str = "local"
    speech_provider: str = "local_darija"
    speech_model_version: str = "opensign-tone-v1"
    speech_default_voice_id: str = "darija-default"
    speech_fallback_provider: str = "local_arabic_fallback"
    speech_max_text_length: int = 500
    speech_min_text_length: int = 1
    speech_max_sentences: int = 5
    speech_generation_timeout_seconds: int = 20
    speech_audio_format: str = "wav"
    speech_sample_rate: int = 22050
    speech_enable_browser_fallback: bool = True
    speech_max_concurrent_generations: int = 2
    normalization_version: str = "darija-normalizer-1.0.0"
    allowed_formats: set[str] = Field(default_factory=lambda: {"wav", "mp3", "ogg"})


@lru_cache
def get_settings() -> Settings:
    return Settings()
