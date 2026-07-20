import asyncio

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.system import HealthResponse, VersionResponse

router = APIRouter(tags=["system"])


async def service_health(url: str, timeout_seconds: float) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url)
        return "healthy" if response.status_code == 200 else "unhealthy"
    except httpx.HTTPError:
        return "unhealthy"


@router.get("/health", response_model=HealthResponse)
async def api_health() -> HealthResponse:
    settings = get_settings()
    inference, speech = await asyncio.gather(
        service_health(
            f"{settings.inference_service_url.rstrip('/')}/health",
            settings.inference_timeout_seconds,
        ),
        service_health(
            f"{settings.speech_service_url.rstrip('/')}/health",
            min(float(settings.speech_generation_timeout_seconds), 3.0),
        ),
    )
    dependencies = {
        "inference": inference,
        "speech": speech,
    }
    status = (
        "healthy" if all(value == "healthy" for value in dependencies.values()) else "degraded"
    )
    return HealthResponse(
        status=status,
        service="opensign-api",
        version=settings.app_version,
        dependencies=dependencies,
    )


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(service="opensign-api", version=settings.app_version)
