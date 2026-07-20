from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def system_tts_available() -> bool:
    return bool(shutil.which("espeak-ng") or shutil.which("say"))


def synthesize_arabic_speech(text: str, speed: float) -> bytes:
    """Synthesize intelligible Arabic speech without a network service."""
    safe_speed = min(max(speed, 0.7), 1.3)
    with tempfile.TemporaryDirectory(prefix="opensign-speech-") as directory:
        output = Path(directory) / "speech.wav"
        espeak = shutil.which("espeak-ng")
        macos_say = shutil.which("say")
        if espeak:
            words_per_minute = round(155 * safe_speed)
            command = [
                espeak,
                "-v",
                "ar",
                "-s",
                str(words_per_minute),
                "-w",
                str(output),
                text,
            ]
        elif macos_say:
            words_per_minute = round(175 * safe_speed)
            command = [
                macos_say,
                "-v",
                "Majed",
                "-r",
                str(words_per_minute),
                "-o",
                str(output),
                "--file-format=WAVE",
                "--data-format=LEI16@22050",
                text,
            ]
        else:
            raise RuntimeError("SYSTEM_ARABIC_TTS_UNAVAILABLE")
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=20,
        )
        if completed.returncode != 0 or not output.exists():
            raise RuntimeError("SYSTEM_ARABIC_TTS_FAILED")
        audio = output.read_bytes()
        if len(audio) < 64:
            raise RuntimeError("SYSTEM_ARABIC_TTS_EMPTY")
        return audio
