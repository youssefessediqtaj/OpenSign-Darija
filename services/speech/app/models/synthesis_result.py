from pydantic import BaseModel


class AudioMetadata(BaseModel):
    mime_type: str
    extension: str
    sample_rate: int
    channels: int
    duration_ms: int
    file_size_bytes: int
    checksum: str


class SynthesisResult(BaseModel):
    generation_id: str
    status: str
    provider: str
    model_version: str
    requested_language: str
    synthesis_language: str
    fallback_used: bool
    original_text_hash: str
    normalized_text_hash: str
    normalized_text: str
    normalization_version: str
    audio_base64: str
    audio: AudioMetadata
