from app.models.voice import Voice
from app.providers.base import SpeechProvider
from app.providers.local_arabic_fallback import LocalArabicFallbackProvider
from app.providers.local_darija import LocalDarijaProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: list[SpeechProvider] = [LocalDarijaProvider(), LocalArabicFallbackProvider()]

    def list_voices(self) -> list[Voice]:
        voices: list[Voice] = []
        for provider in self.providers:
            if provider.is_ready():
                voices.extend(voice for voice in provider.list_voices() if voice.is_active)
        return voices

    def provider_for_voice(self, voice_id: str) -> SpeechProvider:
        for provider in self.providers:
            for voice in provider.list_voices():
                if voice.id == voice_id and voice.is_active:
                    return provider
        raise ValueError("VOICE_NOT_FOUND")

    def ready(self) -> bool:
        return any(provider.is_ready() and provider.list_voices() for provider in self.providers)
