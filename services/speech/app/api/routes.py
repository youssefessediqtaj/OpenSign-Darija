from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.providers.local import LocalSpeechProvider, SpeechProvider
from app.schemas.synthesis import SynthesisRequest, SynthesisResult
from app.services.synthesis_service import SynthesisService

router = APIRouter()


def get_speech_provider() -> SpeechProvider:
    return LocalSpeechProvider()


def get_synthesis_service(
    provider: Annotated[SpeechProvider, Depends(get_speech_provider)],
) -> SynthesisService:
    return SynthesisService(provider=provider)


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    status = "disabled" if settings.speech_mode == "disabled" else "healthy"
    return {"status": status, "mode": settings.speech_mode}


@router.get("/ready")
def ready(
    provider: Annotated[SpeechProvider, Depends(get_speech_provider)],
) -> dict[str, object]:
    if not provider.is_ready():
        raise HTTPException(status_code=503, detail={"status": "FAILED"})
    return {"status": "READY", "voices": len(provider.list_voices())}


@router.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": "speech",
        "version": "0.2.0",
        "model_version": settings.speech_model_version,
    }


@router.get("/voices")
def voices(
    provider: Annotated[SpeechProvider, Depends(get_speech_provider)],
) -> dict[str, object]:
    return {"voices": [voice.model_dump() for voice in provider.list_voices()]}


@router.post("/synthesize", response_model=SynthesisResult)
def synthesize(
    payload: SynthesisRequest,
    service: Annotated[SynthesisService, Depends(get_synthesis_service)],
) -> SynthesisResult:
    try:
        return service.synthesize(payload)
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "VOICE_NOT_FOUND" else 422
        raise HTTPException(status_code=status, detail={"code": code}) from exc
