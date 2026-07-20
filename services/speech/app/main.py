from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app.core.config import get_settings
from app.models.synthesis_request import SynthesisRequest
from app.models.synthesis_result import SynthesisResult
from app.providers.registry import ProviderRegistry
from app.services.synthesis_service import SynthesisService

app = FastAPI(title="OpenSign Darija Speech")


def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()


def get_synthesis_service() -> SynthesisService:
    return SynthesisService()


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    status = "disabled" if settings.speech_mode == "disabled" else "healthy"
    return {"status": status, "mode": settings.speech_mode}


@app.get("/ready")
def ready(
    registry: Annotated[ProviderRegistry, Depends(get_provider_registry)],
) -> dict[str, object]:
    is_ready = registry.ready()
    if not is_ready:
        raise HTTPException(status_code=503, detail={"status": "FAILED"})
    return {"status": "READY", "voices": len(registry.list_voices())}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"service": "speech", "version": "0.2.0", "model_version": settings.speech_model_version}


@app.get("/voices")
def voices(
    registry: Annotated[ProviderRegistry, Depends(get_provider_registry)],
) -> dict[str, object]:
    return {"voices": [voice.model_dump() for voice in registry.list_voices()]}


@app.post("/synthesize", response_model=SynthesisResult)
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
