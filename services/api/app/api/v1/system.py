from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.system import HealthResponse, VersionResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def api_health(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    settings = get_settings()
    dependencies = {"database": "unhealthy", "redis": "unhealthy", "inference": "unhealthy"}
    try:
        db.execute(text("select 1"))
        dependencies["database"] = "healthy"
    except Exception:
        dependencies["database"] = "unhealthy"
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=0.5, socket_timeout=0.5).ping()
        dependencies["redis"] = "healthy"
    except Exception:
        dependencies["redis"] = "unhealthy"
    try:
        async with httpx.AsyncClient(timeout=settings.inference_timeout_seconds) as client:
            response = await client.get(f"{settings.inference_service_url.rstrip('/')}/health")
            dependencies["inference"] = "healthy" if response.status_code == 200 else "unhealthy"
    except httpx.HTTPError:
        dependencies["inference"] = "unhealthy"
    status = "healthy" if all(value == "healthy" for value in dependencies.values()) else "degraded"
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
