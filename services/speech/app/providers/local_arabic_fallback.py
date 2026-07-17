from app.audio.waveform import synthesize_tone_speech
from app.core.config import get_settings
from app.models.voice import Voice
from app.providers.base import SpeechProvider, SynthesisInput, SynthesisOutput


class LocalArabicFallbackProvider(SpeechProvider):
    name = "local-arabic-fallback"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_ready(self) -> bool:
        return self.settings.speech_mode in {"local", "browser_fallback"}

    def list_voices(self) -> list[Voice]:
        return [
            Voice(
                id="arabic-fallback",
                provider=self.name,
                voice_code="opensign-tone-ar-1",
                display_name="Voix arabe de secours",
                language="ar",
                locale="ar",
                description="Voix de secours clairement identifiee, non presentee comme Darija native.",
                model_version=self.settings.speech_model_version,
                license="Apache-2.0 project code; no external weights bundled",
                is_default=False,
                is_experimental=True,
                supports_speed=True,
            )
        ]

    def synthesize(self, request: SynthesisInput) -> SynthesisOutput:
        audio, duration_ms = synthesize_tone_speech(
            request.text, self.settings.speech_sample_rate, request.speed
        )
        return SynthesisOutput(
            audio_bytes=audio,
            sample_rate=self.settings.speech_sample_rate,
            duration_ms=duration_ms,
            format="wav",
            provider=self.name,
            model_version=self.settings.speech_model_version,
            synthesis_language="ar",
            fallback_used=True,
        )
