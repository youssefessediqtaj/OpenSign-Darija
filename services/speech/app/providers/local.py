from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings
from app.providers.system_tts import synthesize_arabic_speech, system_tts_available
from app.schemas.synthesis import Voice
from app.services.audio_validation import validate_wav


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
    provider: str
    model_version: str
    synthesis_language: str
    fallback_used: bool


class SpeechProvider(Protocol):
    def is_ready(self) -> bool: ...

    def list_voices(self) -> list[Voice]: ...

    def synthesize(self, request: SynthesisInput) -> SynthesisOutput: ...


class LocalSpeechProvider:
    """The single local provider with explicit ar-MA and ar voice identities."""

    name = "local-system-arabic"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_ready(self) -> bool:
        return self.settings.speech_mode == "local" and system_tts_available()

    def list_voices(self) -> list[Voice]:
        version = self.settings.speech_model_version
        license_text = "System speech engine; no downloaded voice weights bundled"
        return [
            Voice(
                id="darija-default",
                provider="local-darija",
                voice_code="opensign-system-ar-1",
                display_name="Voix arabe locale",
                language="ar-MA",
                locale="ar-MA",
                description=(
                    "Synthèse arabe locale pour lire les libellés Darija. "
                    "Elle ne clone aucune personne réelle et son accent marocain reste limité."
                ),
                model_version=version,
                license=license_text,
                is_default=True,
                is_experimental=True,
                supports_speed=True,
            ),
            Voice(
                id="arabic-fallback",
                provider="local-arabic-fallback",
                voice_code="opensign-system-ar-fallback-1",
                display_name="Voix arabe de secours",
                language="ar",
                locale="ar",
                description=(
                    "Voix de secours clairement identifiee, non presentee comme Darija native."
                ),
                model_version=version,
                license=license_text,
                is_default=False,
                is_experimental=True,
                supports_speed=True,
            ),
        ]

    def synthesize(self, request: SynthesisInput) -> SynthesisOutput:
        voices = {voice.id: voice for voice in self.list_voices() if voice.is_active}
        voice = voices.get(request.voice_id)
        if voice is None:
            raise ValueError("VOICE_NOT_FOUND")
        audio = synthesize_arabic_speech(
            request.text,
            request.speed,
            self.settings.speech_generation_timeout_seconds,
        )
        validate_wav(audio)
        fallback_used = voice.id == "arabic-fallback"
        return SynthesisOutput(
            audio_bytes=audio,
            provider=str(voice.provider),
            model_version=self.settings.speech_model_version,
            synthesis_language="ar" if fallback_used else "ar-MA",
            fallback_used=fallback_used,
        )
