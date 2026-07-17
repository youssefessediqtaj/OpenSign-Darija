import io
import math
import struct
import wave


def synthesize_tone_speech(text: str, sample_rate: int, speed: float) -> tuple[bytes, int]:
    cleaned = text.strip()
    if not cleaned:
        cleaned = " "
    frame_chunks: list[bytes] = []
    base_duration = max(0.045, 0.075 / speed)
    silence_duration = max(0.025, 0.045 / speed)
    amplitude = 0.22
    for char in cleaned:
        if char.isspace() or char in "،,.؟?!:;\n":
            samples = int(sample_rate * (silence_duration * (2.2 if char in ".؟?!" else 1.0)))
            frame_chunks.append(b"\x00\x00" * samples)
            continue
        codepoint = ord(char)
        frequency = 180 + (codepoint % 34) * 17
        samples = int(sample_rate * base_duration)
        chunk = bytearray()
        fade = max(1, int(samples * 0.08))
        for index in range(samples):
            envelope = 1.0
            if index < fade:
                envelope = index / fade
            elif index > samples - fade:
                envelope = max(0.0, (samples - index) / fade)
            value = amplitude * envelope * math.sin(2 * math.pi * frequency * index / sample_rate)
            chunk.extend(struct.pack("<h", int(value * 32767)))
        frame_chunks.append(bytes(chunk))
    pcm = b"".join(frame_chunks)
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    duration_ms = int((len(pcm) / 2) / sample_rate * 1000)
    return output.getvalue(), duration_ms
