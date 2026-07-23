from app.clients.speech import SpeechServiceClient
from app.core.errors import ApiError
from app.schemas.speech import SignSpeechAudioResponse, SignSpeechRequest, SignSpeechResponse
from app.services.supported_signs import resolve_supported_sign


def synthesize_supported_sign(payload: SignSpeechRequest) -> SignSpeechResponse:
    """Synthesize only labels verified against the active model package.

    The public browser supplies a label key, never arbitrary text. The API resolves
    that key from the checksum-verified package and prefers local ar-MA speech before
    the explicit local Arabic fallback.
    """

    label_ar = resolve_supported_sign(payload.label_key)
    client = SpeechServiceClient()
    fallback_used = False
    try:
        result = client.synthesize(
            text=label_ar,
            language="ar-MA",
            voice_id="darija-default",
            speed=1.0,
            output_format="wav",
        )
    except ApiError:
        fallback_used = True
        result = client.synthesize(
            text=label_ar,
            language="ar",
            voice_id="arabic-fallback",
            speed=1.0,
            output_format="wav",
        )

    generation_id = result.get("generation_id")
    audio = result.get("audio")
    audio_base64 = result.get("audio_base64")
    if (
        not isinstance(generation_id, str)
        or not generation_id
        or not isinstance(audio, dict)
        or not isinstance(audio_base64, str)
        or not audio_base64
    ):
        raise ApiError(
            "SPEECH_GENERATION_FAILED",
            "Le service vocal a retourne un audio invalide.",
            502,
        )
    mime_type = str(audio.get("mime_type") or "audio/wav")
    return SignSpeechResponse(
        generation_id=generation_id,
        status="completed",
        label_key=payload.label_key,
        label_ar=label_ar,
        audio=SignSpeechAudioResponse(
            url=f"data:{mime_type};base64,{audio_base64}",
            mime_type=mime_type,
            duration_ms=int(audio.get("duration_ms") or 0),
            file_size_bytes=int(audio.get("file_size_bytes") or 0),
        ),
        fallback_used=fallback_used or bool(result.get("fallback_used", False)),
    )
