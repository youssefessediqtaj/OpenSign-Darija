import hashlib
import io
import wave
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioValidation:
    mime_type: str
    extension: str
    sample_rate: int
    channels: int
    duration_ms: int
    file_size_bytes: int
    checksum: str


def validate_wav(audio_bytes: bytes) -> AudioValidation:
    if len(audio_bytes) < 64:
        raise ValueError("AUDIO_TOO_SMALL")
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        frames = wav.getnframes()
        sample_width = wav.getsampwidth()
        pcm = wav.readframes(frames)
    if channels != 1:
        raise ValueError("INVALID_CHANNELS")
    if sample_width != 2:
        raise ValueError("INVALID_SAMPLE_WIDTH")
    if frames <= 0:
        raise ValueError("EMPTY_AUDIO")
    non_zero = sum(1 for byte in pcm if byte)
    if non_zero == 0:
        raise ValueError("SILENT_AUDIO")
    duration_ms = int(frames / sample_rate * 1000)
    if duration_ms <= 0:
        raise ValueError("INVALID_DURATION")
    return AudioValidation(
        mime_type="audio/wav",
        extension="wav",
        sample_rate=sample_rate,
        channels=channels,
        duration_ms=duration_ms,
        file_size_bytes=len(audio_bytes),
        checksum=hashlib.sha256(audio_bytes).hexdigest(),
    )
