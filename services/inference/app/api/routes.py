from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.prediction import LandmarkSequenceRequest, PredictionResponse, PredictMockRequest
from app.services.model_loader import model_loader
from app.services.prediction_service import PredictionService

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
        "mock": settings.inference_mode == "mock",
        "feature_schema_version": settings.feature_schema_version,
    }


@router.post("/predict/mock", response_model=PredictionResponse)
def predict_mock(payload: PredictMockRequest) -> PredictionResponse:
    return prediction_service.predict_mock(payload.frames_count)


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: LandmarkSequenceRequest) -> PredictionResponse:
    try:
        return prediction_service.predict_sequence(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/admin/reload-model")
def reload_model() -> dict[str, str | None]:
    model_loader.reload()
    return {"state": model_loader.state, "error": model_loader.error}
