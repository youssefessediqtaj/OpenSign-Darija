from app.audio.waveform import synthesize_tone_speech
from app.core.config import get_settings
from app.models.voice import Voice
from app.providers.base import SpeechProvider, SynthesisInput, SynthesisOutput


class LocalDarijaProvider(SpeechProvider):
    name = "local-darija"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_ready(self) -> bool:
        return self.settings.speech_mode == "local"

    def list_voices(self) -> list[Voice]:
        return [
            Voice(
                id="darija-default",
                provider=self.name,
                voice_code="opensign-tone-ary-ma-1",
                display_name="Voix synthétique expérimentale en Darija",
                language="ary-MA",
                locale="ary-MA",
                description=(
                    "Voix locale expérimentale non humaine pour valider le flux audio Darija. "
                    "Elle ne clone aucune personne réelle."
                ),
                model_version=self.settings.speech_model_version,
                license="Apache-2.0 project code; no external weights bundled",
                is_default=True,
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
            synthesis_language="ary-MA",
            fallback_used=False,
        )
