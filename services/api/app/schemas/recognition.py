from math import isfinite
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.signs import SignResponse


class RecognitionMockRequest(BaseModel):
    source: str = Field(default="demo", max_length=40)
    frames_count: int = Field(default=0, ge=0, le=300)


class PredictionResponse(BaseModel):
    prediction_id: str | None = None
    label: str
    confidence: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)
    sign: SignResponse | None = None
    is_unknown: bool = False


class RecognitionResponse(BaseModel):
    recognition_id: str | None = None
    request_id: str
    sequence_id: str | None = None
    status: str
    model_name: str
    model_version: str
    feature_schema_version: str | None = None
    inference_mode: str = "mock"
    decision: str = "known"
    confidence_level: str = "high"
    predictions: list[PredictionResponse]
    unknown_probability: float = Field(ge=0, le=1)
    processing_time_ms: int = Field(ge=0)


class CompactFrame(BaseModel):
    index: int = Field(ge=0, le=59)
    timestamp_ms: int = Field(ge=0, le=10_000)
    features: list[float] = Field(min_length=63, max_length=63)
    presence_mask: list[int] = Field(min_length=21, max_length=21)

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[float]) -> list[float]:
        if any(not isfinite(item) or abs(item) > 20 for item in value):
            raise ValueError("features must be finite and in range")
        return value

    @field_validator("presence_mask")
    @classmethod
    def validate_mask(cls, value: list[int]) -> list[int]:
        if any(item not in (0, 1) for item in value):
            raise ValueError("presence_mask must contain 0 or 1")
        return value


class SequenceQualityPayload(BaseModel):
    detected_hand_ratio: float = Field(ge=0, le=1)
    detected_face_ratio: float = Field(ge=0, le=1)
    detected_pose_ratio: float = Field(ge=0, le=1)
    missing_frame_ratio: float = Field(ge=0, le=1)
    movement_score: float = Field(ge=0, le=1)


class LandmarkRecognitionRequest(BaseModel):
    sequence_id: UUID
    captured_at: str = Field(min_length=10, max_length=40)
    duration_ms: int = Field(ge=500, le=8000)
    source_fps: float = Field(gt=0, le=60)
    target_frame_count: int = Field(ge=1, le=60)
    coordinate_format: str = Field(pattern="^torso_normalized_v1$")
    feature_schema_version: str = Field(pattern="^1\\.0\\.0$")
    frames: list[CompactFrame] = Field(min_length=1, max_length=60)
    quality: SequenceQualityPayload
    anonymous_session_id: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_sequence(self) -> "LandmarkRecognitionRequest":
        if len(self.frames) != self.target_frame_count:
            raise ValueError("target_frame_count must match frames length")
        if self.quality.detected_hand_ratio < 0.35:
            raise ValueError("insufficient_hand_visibility")
        return self


class ActiveModelResponse(BaseModel):
    id: str | None = None
    name: str
    semantic_version: str
    status: str
    architecture: str
    vocabulary_size: int
    feature_schema_version: str
    metrics_json: dict[str, object] = Field(default_factory=dict)
    thresholds_json: dict[str, object] = Field(default_factory=dict)
    is_active: bool


class ConfirmRecognitionRequest(BaseModel):
    prediction_id: UUID


class CorrectRecognitionRequest(BaseModel):
    correct_sign_id: UUID | None = None
    reason: str = Field(default="wrong_prediction", max_length=80)
    comment: str | None = Field(default=None, max_length=500)
