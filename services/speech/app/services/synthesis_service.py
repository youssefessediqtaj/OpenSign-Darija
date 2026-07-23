import base64
import hashlib
import uuid
from threading import BoundedSemaphore

from app.core.config import get_settings
from app.providers.local import LocalSpeechProvider, SpeechProvider, SynthesisInput
from app.schemas.synthesis import AudioMetadata, SynthesisRequest, SynthesisResult
from app.services.audio_validation import validate_wav
from app.services.text_normalization import normalize_darija
from app.services.text_validation import validate_text


class SynthesisService:
    def __init__(self, provider: SpeechProvider | None = None) -> None:
        self.settings = get_settings()
        self.provider = provider or LocalSpeechProvider()
        self._capacity = BoundedSemaphore(self.settings.speech_max_concurrent_generations)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        validate_text(
            request.text,
            self.settings.speech_min_text_length,
            self.settings.speech_max_text_length,
            self.settings.speech_max_sentences,
        )
        normalized = normalize_darija(request.text, self.settings.normalization_version)
        validate_text(
            normalized.normalized_text,
            self.settings.speech_min_text_length,
            self.settings.speech_max_text_length,
            self.settings.speech_max_sentences,
        )
        if request.voice_id not in {
            voice.id for voice in self.provider.list_voices() if voice.is_active
        }:
            raise ValueError("VOICE_NOT_FOUND")
        if not self._capacity.acquire(blocking=False):
            raise ValueError("SPEECH_BUSY")
        try:
            output = self.provider.synthesize(
                SynthesisInput(
                    text=normalized.normalized_text,
                    language=request.language,
                    voice_id=request.voice_id,
                    speed=request.speed,
                    output_format=request.output_format,
                )
            )
        finally:
            self._capacity.release()
        validation = validate_wav(output.audio_bytes)
        original_hash = hashlib.sha256(request.text.encode("utf-8")).hexdigest()
        normalized_hash = hashlib.sha256(normalized.normalized_text.encode("utf-8")).hexdigest()
        return SynthesisResult(
            generation_id=str(uuid.uuid4()),
            status="completed",
            provider=output.provider,
            model_version=output.model_version,
            requested_language=request.language,
            synthesis_language=output.synthesis_language,
            fallback_used=output.fallback_used,
            original_text_hash=original_hash,
            normalized_text_hash=normalized_hash,
            normalized_text=normalized.normalized_text,
            normalization_version=normalized.normalization_version,
            audio_base64=base64.b64encode(output.audio_bytes).decode("ascii"),
            audio=AudioMetadata(**validation.__dict__),
        )
