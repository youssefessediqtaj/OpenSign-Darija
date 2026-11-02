"""Explicitly enabled loopback-only color model diagnostics."""

import hmac
from functools import lru_cache
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.runtime.colors_model import (
    FEATURE_VERSION,
    ExperimentalColorsModel,
    IncompatibleModelOutputError,
    digest,
)
from app.schemas.prediction import WordLandmarkSequenceRequest

router = APIRouter()


@lru_cache(maxsize=4)
def _load_model(
    registry: str, manifest: str, version: str, registry_hash: str, manifest_hash: str
) -> ExperimentalColorsModel:
    # Hashes are cache keys so replacing either file forces compatibility revalidation.
    return ExperimentalColorsModel(registry, manifest, version)


def local_model() -> ExperimentalColorsModel:
    settings = get_settings()
    if not settings.colors_experimental_dataset_manifest:
        raise ValueError("current dataset manifest is required")
    if not settings.colors_experimental_model_version:
        raise ValueError("explicit experimental model version is required")
    model = _load_model(
        settings.colors_experimental_registry,
        settings.colors_experimental_dataset_manifest,
        settings.colors_experimental_model_version,
        digest(Path(settings.colors_experimental_registry)),
        digest(Path(settings.colors_experimental_dataset_manifest)),
    )
    model.verify_artifacts()
    return model


def require_local(request: Request) -> None:
    settings = get_settings()
    token = settings.colors_experimental_token
    try:
        address = ip_address(request.client.host) if request.client else None
        allowed = bool(
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
    payload: WordLandmarkSequenceRequest,
    request: Request,
    diagnostic: bool = False,
    trace: bool = False,
) -> dict[str, Any]:
    require_local(request)
    unavailable: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental",
        "model_version": get_settings().colors_experimental_model_version or "unselected",
        "recognition_state": "MODEL_NOT_READY",
        "semantic_label": None,
        "sign_variant_id": None,
        "candidate": None,
        "raw_score": None,
        "calibration_status": "UNCALIBRATED",
        "experimental": True,
    }

    def failure(stage: str) -> dict[str, Any]:
        if not (diagnostic and trace):
            return {}
        return {
            "diagnostics": {
                "feature_schema_version": FEATURE_VERSION,
                "output_shape": None,
                "top_three": [],
                "failure_stage": stage,
            }
        }

    try:
        model = local_model()
    except Exception:
        return {**unavailable, **failure("model_load")}
    landmarks = np.array([frame.landmarks for frame in payload.frames], dtype=np.float32)
    mask = np.array([frame.presence_mask for frame in payload.frames], dtype=np.float32)
    try:
        return model.predict(
            landmarks,
            mask,
            payload.usable_frame_count,
            include_candidate=diagnostic,
            include_trace=diagnostic and trace,
        )
    except IncompatibleModelOutputError:
        return {
            **unavailable,
            "recognition_state": "INCOMPATIBLE_MODEL_OUTPUT",
            **failure("inference"),
        }
    except Exception:
        return {**unavailable, "recognition_state": "INFERENCE_ERROR", **failure("inference")}
