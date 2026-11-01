"""Optional, loopback-only gateway for experimental color diagnostics."""

import hmac
from ipaddress import ip_address
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.schemas.recognition import WordLandmarkRecognitionRequest
from app.services.request_protection import enforce_recognition_request_limits

router = APIRouter(prefix="/recognitions", tags=["local experimental"])


class ExperimentalColorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    model_version: str
    recognition_state: Literal[
        "UNKNOWN_SIGN",
        "NO_HAND_DETECTED",
        "INSUFFICIENT_FRAMES",
        "MODEL_NOT_READY",
        "PREPROCESSING_ERROR",
        "INFERENCE_ERROR",
    ]
    semantic_label: None
    sign_variant_id: None
    candidate: (
        Literal["black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"]
        | None
    )
    raw_score: float | None
    calibration_status: Literal["UNCALIBRATED"]
    experimental: Literal[True]


@router.post("/colors-experimental", response_model=ExperimentalColorResult)
async def predict_colors(
    payload: WordLandmarkRecognitionRequest, request: Request, diagnostic: bool = False
) -> ExperimentalColorResult:
    settings = get_settings()
    try:
        local = bool(request.client and ip_address(request.client.host).is_loopback)
    except ValueError:
        local = False
    if (
        any(header in request.headers for header in ("forwarded", "x-forwarded-for", "x-real-ip"))
        or not local
        or len(settings.colors_experimental_token) < 16
        or not hmac.compare_digest(
            request.headers.get("x-colors-dev-token", "").encode("utf-8"),
            settings.colors_experimental_token.encode("utf-8"),
        )
    ):
        raise HTTPException(status_code=403, detail="Experimental local access denied")
    enforce_recognition_request_limits(request)
    url = f"{settings.inference_service_url.rstrip('/')}/predict/colors-experimental"
    try:
        async with httpx.AsyncClient(timeout=settings.inference_timeout_seconds) as client:
            response = await client.post(
                url,
                params={"diagnostic": str(diagnostic).lower()},
                headers={"x-colors-dev-token": settings.colors_experimental_token},
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return ExperimentalColorResult.model_validate(data)
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=503, detail="Experimental model unavailable") from exc
