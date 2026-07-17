import base64
import hashlib
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.api.v1.messages import assert_message_access, load_message, message_response
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.enums import MessageStatus, SpeechGenerationStatus
from app.models.speech import SpeechGeneration, SpeechVoice
from app.models.user import User
from app.schemas.speech import (
    SpeechAudioResponse,
    SpeechGenerationRequest,
    SpeechGenerationResponse,
    SpeechProviderResponse,
    SpeechStatusResponse,
    SpeechVoiceResponse,
    SpeechVoicesResponse,
)
from app.services.object_storage import ObjectStorage
from app.services.speech import SpeechServiceClient

router = APIRouter(tags=["speech"])

TEXT_SOURCES = {
    "final_darija_arabic",
    "final_darija_latin",
    "generated_darija_arabic",
    "generated_darija_latin",
}
SENSITIVE_LEVELS = {"MEDICAL", "LEGAL", "FINANCIAL", "EMERGENCY"}
MIME_BY_FORMAT = {"wav": "audio/wav", "mp3": "audio/mpeg", "ogg": "audio/ogg"}


def voice_response(voice: SpeechVoice) -> SpeechVoiceResponse:
    return SpeechVoiceResponse(
        id=voice.id,
        provider=voice.provider,
        display_name=voice.display_name,
        language=voice.language,
        locale=voice.locale,
        model_version=voice.model_version,
        license_info=voice.license_info,
        is_default=voice.is_default,
        is_active=voice.is_active,
        is_experimental=voice.is_experimental,
    )


def generation_audio(generation: SpeechGeneration) -> SpeechAudioResponse | None:
    if (
        not generation.audio_object_key
        or not generation.duration_ms
        or not generation.file_size_bytes
    ):
        return None
    expires_at = datetime.now(UTC) + timedelta(seconds=get_settings().speech_signed_url_ttl_seconds)
    return SpeechAudioResponse(
        url=ObjectStorage().presigned_speech_get_url(generation.audio_object_key),
        mime_type=MIME_BY_FORMAT.get(generation.format, "audio/wav"),
        duration_ms=generation.duration_ms,
        file_size_bytes=generation.file_size_bytes,
        expires_at=expires_at,
    )


def generation_response(
    generation: SpeechGeneration, cache_hit: bool | None = None
) -> SpeechGenerationResponse:
    return SpeechGenerationResponse(
        generation_id=generation.id,
        status=generation.status.value.lower(),
        cache_hit=generation.cache_hit if cache_hit is None else cache_hit,
        audio=generation_audio(generation),
        voice=voice_response(generation.voice),
        provider=SpeechProviderResponse(
            name=generation.provider, model_version=generation.model_version
        ),
        fallback_used=generation.fallback_used,
        requested_language=generation.requested_language,
        synthesis_language=generation.synthesis_language,
        expires_at=generation.expires_at,
        error_code=generation.error_code,
    )


def message_text(message_id: str, source: str, db: Session) -> str:
    message = load_message(db, message_id)
    if source not in TEXT_SOURCES:
        raise ApiError("INVALID_TEXT_SOURCE", "Source de texte non supportee.", 422)
    value = getattr(message, source)
    text = str(value or "").strip()
    if not text:
        raise ApiError("EMPTY_MESSAGE", "Le message final est vide.", 422)
    if len(text) > get_settings().speech_max_text_length:
        raise ApiError(
            "TEXT_TOO_LONG",
            "Le message est trop long pour etre lu en une seule fois.",
            413,
            {"max_characters": get_settings().speech_max_text_length},
        )
    return text


def cache_key(
    normalized_text_hash: str, voice_id: str, speed: float, fmt: str, model_version: str
) -> str:
    canonical = f"{normalized_text_hash}:{voice_id}:{speed:.2f}:{fmt}:{model_version}"
    return "speech:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def latest_completed_for_text(
    db: Session, message_id: str, text_hash: str, voice_id: str, speed: float, fmt: str
) -> SpeechGeneration | None:
    return db.scalar(
        select(SpeechGeneration)
        .where(
            SpeechGeneration.message_id == message_id,
            SpeechGeneration.original_text_hash == text_hash,
            SpeechGeneration.voice_id == voice_id,
            SpeechGeneration.speed == speed,
            SpeechGeneration.format == fmt,
            SpeechGeneration.status == SpeechGenerationStatus.COMPLETED,
            SpeechGeneration.deleted_at.is_(None),
            SpeechGeneration.expires_at > datetime.now(UTC),
        )
        .order_by(SpeechGeneration.completed_at.desc())
    )


@router.get("/speech/voices", response_model=SpeechVoicesResponse)
def list_speech_voices(db: Annotated[Session, Depends(get_db)]) -> SpeechVoicesResponse:
    voices = db.scalars(select(SpeechVoice).where(SpeechVoice.is_active.is_(True))).all()
    return SpeechVoicesResponse(voices=[voice_response(voice) for voice in voices])


@router.get("/speech/status", response_model=SpeechStatusResponse)
def speech_status(db: Annotated[Session, Depends(get_db)]) -> SpeechStatusResponse:
    voices_count = db.scalar(
        select(func.count()).select_from(SpeechVoice).where(SpeechVoice.is_active.is_(True))
    )
    return SpeechStatusResponse(
        mode=get_settings().speech_mode,
        service_available=SpeechServiceClient().status(),
        browser_fallback_enabled=get_settings().speech_enable_browser_fallback,
        voices_available=voices_count or 0,
    )


@router.post("/messages/{message_id}/speech", response_model=SpeechGenerationResponse)
def create_message_speech(
    message_id: str,
    payload: SpeechGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> SpeechGenerationResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    if message.status != MessageStatus.COMPLETED:
        raise ApiError(
            "MESSAGE_NOT_FINALIZED", "Finalisez le message avant la lecture vocale.", 409
        )
    risk = message_response(db, message).risk_level
    if risk in SENSITIVE_LEVELS and not payload.sensitive_confirmed:
        raise ApiError(
            "SENSITIVE_CONFIRMATION_REQUIRED",
            "Verifiez le message avant de le lire a voix haute.",
            409,
            {"risk_level": risk},
        )
    voice = db.get(SpeechVoice, payload.voice_id)
    if voice is None or not voice.is_active:
        raise ApiError("VOICE_NOT_FOUND", "Voix introuvable ou inactive.", 404)
    if payload.format not in MIME_BY_FORMAT:
        raise ApiError("UNSUPPORTED_AUDIO_FORMAT", "Format audio non supporte.", 422)
    if idempotency_key:
        existing = db.scalar(
            select(SpeechGeneration).where(
                SpeechGeneration.message_id == message_id,
                SpeechGeneration.idempotency_key == idempotency_key,
                SpeechGeneration.deleted_at.is_(None),
            )
        )
        if existing:
            return generation_response(existing)
    text = message_text(message_id, payload.text_source, db)
    original_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cached = latest_completed_for_text(
        db, message_id, original_hash, voice.id, payload.speed, payload.format
    )
    if cached:
        cached.cache_hit = True
        db.commit()
        return generation_response(cached, cache_hit=True)
    created_at = datetime.now(UTC)
    ttl = (
        get_settings().speech_user_audio_ttl_seconds
        if message.user_id
        else get_settings().speech_guest_audio_ttl_seconds
    )
    generation = SpeechGeneration(
        message_id=message.id,
        user_id=message.user_id,
        anonymous_session_id=message.anonymous_session_id,
        voice_id=voice.id,
        status=SpeechGenerationStatus.PROCESSING,
        requested_language="ary-MA",
        synthesis_language=voice.language,
        original_text_hash=original_hash,
        normalized_text_hash=original_hash,
        text_length=len(text),
        speed=payload.speed,
        format=payload.format,
        provider=voice.provider,
        model_version=voice.model_version,
        normalization_version="pending",
        fallback_used=voice.id == "arabic-fallback",
        cache_hit=False,
        cache_key="pending",
        idempotency_key=idempotency_key,
        expires_at=created_at + timedelta(seconds=ttl),
    )
    db.add(generation)
    db.flush()
    started = time.perf_counter()
    try:
        result = SpeechServiceClient().synthesize(
            text=text,
            language="ary-MA",
            voice_id=voice.id,
            speed=payload.speed,
            output_format=payload.format,
        )
        audio = result["audio"]
        audio_bytes = base64.b64decode(str(result["audio_base64"]))
        generation.normalized_text_hash = str(result["normalized_text_hash"])
        generation.normalization_version = str(result["normalization_version"])
        generation.synthesis_language = str(result["synthesis_language"])
        generation.provider = str(result["provider"])
        generation.model_version = str(result["model_version"])
        generation.fallback_used = bool(result["fallback_used"])
        generation.cache_key = cache_key(
            generation.normalized_text_hash,
            voice.id,
            payload.speed,
            payload.format,
            generation.model_version,
        )
        extension = str(audio.get("extension") or payload.format)
        object_key = (
            f"speech/{created_at.year:04d}/{created_at.month:02d}/{generation.id}/audio.{extension}"
        )
        ObjectStorage().put_bytes(
            get_settings().speech_audio_bucket,
            object_key,
            audio_bytes,
            str(audio.get("mime_type") or MIME_BY_FORMAT[payload.format]),
        )
        generation.audio_object_key = object_key
        generation.audio_checksum = str(audio["checksum"])
        generation.duration_ms = int(audio["duration_ms"])
        generation.file_size_bytes = int(audio["file_size_bytes"])
        generation.processing_time_ms = int((time.perf_counter() - started) * 1000)
        generation.status = SpeechGenerationStatus.COMPLETED
        generation.completed_at = datetime.now(UTC)
    except ApiError:
        generation.status = SpeechGenerationStatus.FAILED
        generation.error_code = "SPEECH_SERVICE_UNAVAILABLE"
        db.commit()
        raise
    db.commit()
    db.refresh(generation)
    return generation_response(generation)


@router.get("/messages/{message_id}/speech", response_model=list[SpeechGenerationResponse])
def list_message_speech(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> list[SpeechGenerationResponse]:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    generations = db.scalars(
        select(SpeechGeneration)
        .where(SpeechGeneration.message_id == message_id, SpeechGeneration.deleted_at.is_(None))
        .order_by(SpeechGeneration.created_at.desc())
    ).all()
    return [generation_response(item) for item in generations]


@router.get(
    "/messages/{message_id}/speech/{generation_id}",
    response_model=SpeechGenerationResponse,
)
def get_message_speech(
    message_id: str,
    generation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> SpeechGenerationResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    generation = db.get(SpeechGeneration, generation_id)
    if generation is None or generation.message_id != message_id or generation.deleted_at:
        raise ApiError("SPEECH_GENERATION_NOT_FOUND", "Generation vocale introuvable.", 404)
    if generation.expires_at and generation.expires_at <= datetime.now(UTC):
        generation.status = SpeechGenerationStatus.EXPIRED
        db.commit()
    return generation_response(generation)


@router.post(
    "/messages/{message_id}/speech/{generation_id}/refresh-url",
    response_model=SpeechGenerationResponse,
)
def refresh_message_speech_url(
    message_id: str,
    generation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> SpeechGenerationResponse:
    generation = get_message_speech(
        message_id, generation_id, db, current_user, x_anonymous_session_id
    )
    if generation.status == "expired":
        raise ApiError("SPEECH_AUDIO_EXPIRED", "Audio expire; regenerez le message.", 410)
    return generation


@router.delete("/messages/{message_id}/speech/{generation_id}")
def delete_message_speech(
    message_id: str,
    generation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> dict[str, str]:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    generation = db.get(SpeechGeneration, generation_id)
    if generation is None or generation.message_id != message_id:
        raise ApiError("SPEECH_GENERATION_NOT_FOUND", "Generation vocale introuvable.", 404)
    if generation.audio_object_key:
        ObjectStorage().delete_object(
            get_settings().speech_audio_bucket, generation.audio_object_key
        )
    generation.status = SpeechGenerationStatus.DELETED
    generation.deleted_at = datetime.now(UTC)
    db.commit()
    return {"status": "deleted", "generation_id": generation_id}
