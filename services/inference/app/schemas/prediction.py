from math import isfinite
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class PredictMockRequest(BaseModel):
    frames_count: int = Field(default=0, ge=0, le=300)


class ModelInfo(BaseModel):
    name: str
    version: str


class PredictionItem(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)
    is_unknown: bool = False


class PredictionResponse(BaseModel):
    request_id: str
    sequence_id: str | None = None
    model: ModelInfo
    feature_schema_version: str = "1.0.0"
    inference_mode: str = "mock"
    status: str
    decision: str = "known"
    confidence_level: str = "high"
    predictions: list[PredictionItem]
    unknown_probability: float = Field(ge=0, le=1)
    processing_time_ms: int = Field(ge=0)


class AlphabetPredictionRequest(BaseModel):
    sequence_id: UUID
    captured_at: str = Field(min_length=10, max_length=40)
    feature_schema_version: str = Field(pattern="^1\\.0\\.0$")
    hand: str = Field(default="unknown", pattern="^(left|right|unknown)$")
    features: list[float] = Field(min_length=63, max_length=63)
    presence_mask: list[int] = Field(min_length=21, max_length=21)
    stability_frames: int = Field(default=0, ge=0, le=120)
    anonymous_session_id: str | None = Field(default=None, max_length=80)

    @field_validator("features")
    @classmethod
    def finite_features(cls, value: list[float]) -> list[float]:
        if any(not isfinite(item) or abs(item) > 20 for item in value):
            raise ValueError("features must be finite and within range")
        return value

    @field_validator("presence_mask")
    @classmethod
    def binary_mask(cls, value: list[int]) -> list[int]:
        if any(item not in (0, 1) for item in value):
            raise ValueError("presence_mask must contain only 0 or 1")
        return value


class CompactFrame(BaseModel):
    index: int = Field(ge=0, le=59)
    timestamp_ms: int = Field(ge=0, le=10_000)
    features: list[float] = Field(min_length=63, max_length=63)
    presence_mask: list[int] = Field(min_length=21, max_length=21)

    @field_validator("features")
    @classmethod
    def finite_features(cls, value: list[float]) -> list[float]:
        if any(not isfinite(item) or abs(item) > 20 for item in value):
            raise ValueError("features must be finite and within range")
        return value

    @field_validator("presence_mask")
    @classmethod
    def binary_mask(cls, value: list[int]) -> list[int]:
        if any(item not in (0, 1) for item in value):
            raise ValueError("presence_mask must contain only 0 or 1")
        return value


class MoslLandmarkFrame(BaseModel):
    index: int = Field(ge=0, le=59)
    timestamp_ms: int = Field(ge=0, le=10_000)
    landmarks: list[list[float]] = Field(min_length=75, max_length=75)
    presence_mask: list[int] = Field(min_length=75, max_length=75)

    @field_validator("landmarks")
    @classmethod
    def finite_landmarks(cls, value: list[list[float]]) -> list[list[float]]:
        for landmark in value:
            if len(landmark) != 3:
                raise ValueError("each landmark must contain x, y, z")
            if any(not isfinite(item) or abs(item) > 20 for item in landmark):
                raise ValueError("landmarks must be finite and within range")
        return value

    @field_validator("presence_mask")
    @classmethod
    def binary_mask(cls, value: list[int]) -> list[int]:
        if any(item not in (0, 1) for item in value):
            raise ValueError("presence_mask must contain only 0 or 1")
        return value


class SequenceQualityPayload(BaseModel):
    detected_hand_ratio: float = Field(ge=0, le=1)
    detected_face_ratio: float = Field(ge=0, le=1)
    detected_pose_ratio: float = Field(ge=0, le=1)
    missing_frame_ratio: float = Field(ge=0, le=1)
    movement_score: float = Field(ge=0, le=1)


class LandmarkSequenceRequest(BaseModel):
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
    def frame_count_matches(self) -> "LandmarkSequenceRequest":
        if len(self.frames) != self.target_frame_count:
            raise ValueError("target_frame_count must match frames length")
        return self


class WordLandmarkSequenceRequest(BaseModel):
    sequence_id: UUID
    captured_at: str = Field(min_length=10, max_length=40)
    recognition_mode: str = Field(pattern="^WORD_ISOLATED$")
    duration_ms: int = Field(ge=500, le=8000)
    source_fps: float = Field(gt=0, le=60)
    target_frame_count: int = Field(default=60, ge=60, le=60)
    landmark_count: int = Field(default=75, ge=75, le=75)
    coordinate_count: int = Field(default=3, ge=3, le=3)
    coordinate_format: str = Field(pattern="^shoulder_centered_v1$")
    feature_schema_version: str = Field(pattern="^OPEN_SIGNE_LANDMARK_SCHEMA_V1$")
    frames: list[MoslLandmarkFrame] = Field(min_length=60, max_length=60)
    quality: SequenceQualityPayload
    anonymous_session_id: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def frame_count_matches(self) -> "WordLandmarkSequenceRequest":
        if len(self.frames) != self.target_frame_count:
            raise ValueError("target_frame_count must match frames length")
        return self
