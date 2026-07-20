from app.audio.system_tts import synthesize_arabic_speech, system_tts_available
from app.audio.validator import validate_wav
from app.core.config import get_settings
from app.models.voice import Voice
from app.providers.base import SpeechProvider, SynthesisInput, SynthesisOutput


class LocalArabicFallbackProvider(SpeechProvider):
    name = "local-arabic-fallback"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_ready(self) -> bool:
        return self.settings.speech_mode in {"local", "browser_fallback"} and system_tts_available()

    def list_voices(self) -> list[Voice]:
        return [
            Voice(
                id="arabic-fallback",
                provider=self.name,
                voice_code="opensign-system-ar-fallback-1",
                display_name="Voix arabe de secours",
                language="ar",
                locale="ar",
                description="Voix de secours clairement identifiee, non presentee comme Darija native.",
                model_version=self.settings.speech_model_version,
                license="System speech engine; no downloaded voice weights bundled",
                is_default=False,
                is_experimental=True,
                supports_speed=True,
            )
        ]

    def synthesize(self, request: SynthesisInput) -> SynthesisOutput:
        audio = synthesize_arabic_speech(request.text, request.speed)
        validation = validate_wav(audio)
        return SynthesisOutput(
            audio_bytes=audio,
            sample_rate=validation.sample_rate,
            duration_ms=validation.duration_ms,
            format="wav",
            provider=self.name,
            model_version=self.settings.speech_model_version,
            synthesis_language="ar",
            fallback_used=True,
        )
