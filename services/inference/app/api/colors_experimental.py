"""Explicitly enabled loopback-only color model diagnostics."""

import hmac
from functools import lru_cache
from ipaddress import ip_address
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.runtime.colors_model import ExperimentalColorsModel
from app.schemas.prediction import WordLandmarkSequenceRequest

router = APIRouter()


@lru_cache
def local_model() -> ExperimentalColorsModel:
    return ExperimentalColorsModel(get_settings().colors_experimental_registry)


def require_local(request: Request) -> None:
    token = get_settings().colors_experimental_token
    try:
        allowed = bool(request.client and ip_address(request.client.host).is_loopback)
    except ValueError:
        allowed = False
    if (
        any(header in request.headers for header in ("forwarded", "x-forwarded-for", "x-real-ip"))
        or not allowed
        or len(token) < 16
        or not hmac.compare_digest(
            request.headers.get("x-colors-dev-token", "").encode("utf-8"), token.encode("utf-8")
        )
    ):
        raise HTTPException(status_code=403, detail="Experimental local access denied")


@router.post("/predict/colors-experimental")
def predict_colors(
    payload: WordLandmarkSequenceRequest, request: Request, diagnostic: bool = False
) -> dict[str, Any]:
    require_local(request)
    unavailable: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental",
        "model_version": "0.1.0-smoke",
        "recognition_state": "MODEL_NOT_READY",
        "semantic_label": None,
        "sign_variant_id": None,
        "candidate": None,
        "raw_score": None,
        "calibration_status": "UNCALIBRATED",
        "experimental": True,
    }
    try:
        model = local_model()
    except Exception:
        return unavailable
    landmarks = np.array([frame.landmarks for frame in payload.frames], dtype=np.float32)
    mask = np.array([frame.presence_mask for frame in payload.frames], dtype=np.float32)
    try:
        return model.predict(
            landmarks, mask, payload.usable_frame_count, include_candidate=diagnostic
        )
    except Exception:
        return {**unavailable, "recognition_state": "INFERENCE_ERROR"}
