import base64
import hashlib
import uuid

from app.audio.validator import validate_wav
from app.core.config import get_settings
from app.models.synthesis_request import SynthesisRequest
from app.models.synthesis_result import AudioMetadata, SynthesisResult
from app.preprocessing.darija_normalizer import normalize_darija
from app.preprocessing.validation import validate_text
from app.providers.base import SynthesisInput
from app.providers.registry import ProviderRegistry


class SynthesisService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.registry = ProviderRegistry()

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
        if request.output_format not in self.settings.allowed_formats:
            raise ValueError("UNSUPPORTED_FORMAT")
        provider = self.registry.provider_for_voice(request.voice_id)
        output = provider.synthesize(
            SynthesisInput(
                text=normalized.normalized_text,
                language=request.language,
                voice_id=request.voice_id,
                speed=request.speed,
                output_format=request.output_format,
            )
        )
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
