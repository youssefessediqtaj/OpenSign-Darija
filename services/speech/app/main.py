from fastapi import FastAPI, HTTPException

from app.core.config import get_settings
from app.models.synthesis_request import LegacySpeechPrepareRequest, SynthesisRequest
from app.models.synthesis_result import LegacySpeechPrepareResponse, SynthesisResult
from app.providers.registry import ProviderRegistry
from app.services.synthesis_service import SynthesisService

app = FastAPI(title="OpenSign Darija Speech")


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    status = "disabled" if settings.speech_mode == "disabled" else "healthy"
    return {"status": status, "mode": settings.speech_mode}


@app.get("/ready")
def ready() -> dict[str, object]:
    registry = ProviderRegistry()
    is_ready = registry.ready()
    if not is_ready:
        raise HTTPException(status_code=503, detail={"status": "FAILED"})
    return {"status": "READY", "voices": len(registry.list_voices())}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"service": "speech", "version": "0.2.0", "model_version": settings.speech_model_version}


@app.get("/voices")
def voices() -> dict[str, object]:
    return {"voices": [voice.model_dump() for voice in ProviderRegistry().list_voices()]}


@app.post("/synthesize", response_model=SynthesisResult)
def synthesize(payload: SynthesisRequest) -> SynthesisResult:
    try:
        return SynthesisService().synthesize(payload)
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "VOICE_NOT_FOUND" else 422
        raise HTTPException(status_code=status, detail={"code": code}) from exc


@app.get("/generations/{generation_id}")
def generation(generation_id: str) -> dict[str, str]:
    return {"generation_id": generation_id, "status": "ephemeral"}


@app.post("/admin/reload-model")
def reload_model() -> dict[str, str]:
    return {"status": "reloaded", "mode": get_settings().speech_mode}


@app.post("/prepare", response_model=LegacySpeechPrepareResponse)
def prepare(payload: LegacySpeechPrepareRequest) -> LegacySpeechPrepareResponse:
    return LegacySpeechPrepareResponse(
        status="ready",
        message="Le service speech reel est disponible via /synthesize.",
        contract=payload.model_dump(),
    )
