"""Optional, loopback-only gateway for experimental color diagnostics."""

import hmac
from ipaddress import ip_address, ip_network
from typing import Annotated, Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.recognition import WordLandmarkRecognitionRequest
from app.services.request_protection import enforce_recognition_request_limits

router = APIRouter(prefix="/recognitions", tags=["local experimental"])


ColorLabel = Literal["black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"]
SafeIdentifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")]


class RankedColor(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    label: ColorLabel
    raw_score: float


class ColorDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_schema_version: Literal["COLORS_V1_VIDEO_V1_EXPERIMENTAL"]
    output_shape: tuple[Literal[1], Literal[9]] | None
    top_three: list[RankedColor]
    failure_stage: Literal["model_load", "inference"] | None = None


class ExperimentalColorResult(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    model_id: Literal["colors_v1_gru_experimental"]
    model_version: SafeIdentifier
    experiment_id: SafeIdentifier | None = None
    recognition_state: Literal[
        "UNKNOWN_SIGN",
        "NO_HAND_DETECTED",
        "INSUFFICIENT_FRAMES",
        "MODEL_NOT_READY",
        "PREPROCESSING_ERROR",
        "INFERENCE_ERROR",
        "INCOMPATIBLE_MODEL_OUTPUT",
    ]
    semantic_label: None
    sign_variant_id: None
    candidate: ColorLabel | None
    raw_score: float | None
    calibration_status: Literal["UNCALIBRATED"]
    experimental: Literal[True]
    diagnostics: ColorDiagnostics | None = None

    @model_validator(mode="after")
    def validate_candidate_state(self) -> "ExperimentalColorResult":
        if self.candidate is not None and self.recognition_state != "UNKNOWN_SIGN":
            raise ValueError("candidate is inconsistent with recognition state")
        return self


@router.post("/colors-experimental", response_model=ExperimentalColorResult)
async def predict_colors(
    payload: WordLandmarkRecognitionRequest,
    request: Request,
    diagnostic: bool = False,
    trace: bool = False,
) -> ExperimentalColorResult:
    settings = get_settings()
    try:
        address = ip_address(request.client.host) if request.client else None
        local = bool(
            address
            and (
                address.is_loopback
                or (
                    settings.colors_experimental_trusted_network
                    and address in ip_network(settings.colors_experimental_trusted_network)
                )
            )
        )
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
                params={
                    "diagnostic": str(diagnostic).lower(),
                    "trace": str(diagnostic and trace).lower(),
                },
                headers={"x-colors-dev-token": settings.colors_experimental_token},
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            result = ExperimentalColorResult.model_validate(data)
            if result.recognition_state == "MODEL_NOT_READY":
                raise ApiError(
                    "MODEL_NOT_READY", "Modèle de reconnaissance indisponible.", 503,
                    {"status": "MODEL_NOT_READY", "prediction": None, "candidate": None,
                     "model_id": "colors_v1"},
                )
            return result
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Inference request timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Inference service unavailable") from exc
    except (ValueError, TypeError) as exc:
        raise ApiError(
            "INCOMPATIBLE_MODEL_OUTPUT", "La réponse du modèle couleurs est incompatible.", 502
        ) from exc
