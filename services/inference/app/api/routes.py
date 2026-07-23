from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.runtime.model_loader import model_loader
from app.runtime.prediction import PredictionService
from app.schemas.prediction import (
    PredictionResponse,
    WordLandmarkSequenceRequest,
)

router = APIRouter()
prediction_service = PredictionService()


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    status = "healthy" if model_loader.state == "READY" else "degraded"
    return {
        "status": status,
        "state": model_loader.state,
        "service": "opensign-inference",
        "version": settings.app_version,
    }


@router.get("/ready")
def ready() -> dict[str, str]:
    if model_loader.state != "READY":
        raise HTTPException(
            status_code=503, detail={"state": model_loader.state, "error": model_loader.error}
        )
    return {"status": "ready", "state": model_loader.state}


@router.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"service": "opensign-inference", "version": settings.app_version}


@router.get("/model")
def model() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "name": settings.model_name,
        "version": settings.model_version,
        "status": "active" if model_loader.state == "READY" else model_loader.state,
        "mock": False,
        "feature_schema_version": settings.feature_schema_version,
    }


@router.post("/predict/word", response_model=PredictionResponse)
def predict_word(payload: WordLandmarkSequenceRequest) -> PredictionResponse:
    try:
        return prediction_service.predict_word(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
