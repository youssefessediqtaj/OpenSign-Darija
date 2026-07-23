from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    speech_mode: str = "local"
    speech_model_version: str = "opensign-system-arabic-v1"
    speech_max_text_length: int = 500
    speech_min_text_length: int = 1
    speech_max_sentences: int = 5
    speech_generation_timeout_seconds: int = 20
    speech_max_concurrent_generations: int = 2
    normalization_version: str = "darija-normalizer-1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
