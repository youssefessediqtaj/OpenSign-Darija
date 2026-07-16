from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    AutomaticQualityStatus,
    CampaignStatus,
    ConsentType,
    ContributionStatus,
    DatasetSplit,
    DatasetVersionStatus,
    DominantHand,
    ReviewDecision,
    ReviewType,
    SigningExperienceLevel,
)
from app.schemas.signs import SignResponse

SHA256_RE = r"^[a-fA-F0-9]{64}$"


class ContributorProfileRequest(BaseModel):
    preferred_interface_language: str = Field(default="fr", min_length=2, max_length=10)
    region: str | None = Field(default=None, max_length=80)
    dominant_hand: DominantHand | None = None
    experience_level: SigningExperienceLevel | None = None
    accessibility_preferences: dict[str, object] = Field(default_factory=dict)


class ContributorProfileResponse(ContributorProfileRequest):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    public_id: str
    created_at: datetime
    updated_at: datetime


class ConsentTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    version: str
    title: str
    summary: str
    full_text: str
    language: str
    is_active: bool
    published_at: datetime | None


class ConsentChoice(BaseModel):
    consent_type: ConsentType
    granted: bool


class ConsentCreateRequest(BaseModel):
    consent_template_id: str = Field(min_length=20, max_length=36)
    choices: list[ConsentChoice] = Field(min_length=1, max_length=9)
    language: str = Field(default="fr", min_length=2, max_length=10)
    evidence: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_types(self) -> "ConsentCreateRequest":
        consent_types = [choice.consent_type for choice in self.choices]
        if len(set(consent_types)) != len(consent_types):
            raise ValueError("Chaque type de consentement doit apparaitre une seule fois.")
        return self


class ConsentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    consent_template_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime | None
    revoked_at: datetime | None
    evidence: dict[str, object]
    created_at: datetime
    updated_at: datetime
    template: ConsentTemplateResponse | None = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str
    status: CampaignStatus
    target_language: str
    target_sign_count: int
    target_repetitions_per_sign: int
    minimum_repetitions_per_submission: int
    maximum_repetitions_per_submission: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CampaignSignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    sign_id: str
    target_repetitions: int
    minimum_duration_ms: int
    maximum_duration_ms: int
    requires_left_hand: bool
    requires_right_hand: bool
    requires_face: bool
    requires_pose: bool
    instruction_text: str
    instruction_video_path: str | None
    reference_landmark_path: str | None
    is_active: bool
    sign: SignResponse


class ContributionCreateRequest(BaseModel):
    campaign_id: str = Field(min_length=20, max_length=36)
    campaign_sign_id: str = Field(min_length=20, max_length=36)
    wants_video: bool = False


class ContributionUpdateRequest(BaseModel):
    status: Literal["CAPTURING", "READY_TO_SUBMIT"] | None = None


class QualityMetricPayload(BaseModel):
    metric_name: str = Field(min_length=2, max_length=100)
    metric_value: float
    threshold_min: float | None = None
    threshold_max: float | None = None
    passed: bool
    details: dict[str, object] = Field(default_factory=dict)


class RecordingCreateRequest(BaseModel):
    repetition_index: int = Field(ge=1, le=20)
    feature_schema_version: str = Field(min_length=1, max_length=20)
    duration_ms: int = Field(ge=1, le=20_000)
    source_fps: float = Field(gt=0, le=60)
    target_frame_count: int = Field(ge=1, le=120)
    video_width: int | None = Field(default=None, ge=1, le=4096)
    video_height: int | None = Field(default=None, ge=1, le=4096)
    file_size_bytes: int = Field(default=0, ge=0, le=50_000_000)
    landmark_size_bytes: int = Field(ge=1, le=2_000_000)
    checksum_video: str | None = Field(default=None, pattern=SHA256_RE)
    checksum_landmarks: str = Field(pattern=SHA256_RE)
    quality_score: float = Field(ge=0, le=1)
    automatic_quality_status: AutomaticQualityStatus = AutomaticQualityStatus.WARNING
    metrics: list[QualityMetricPayload] = Field(default_factory=list, max_length=40)

    @model_validator(mode="after")
    def video_checksum_matches_file(self) -> "RecordingCreateRequest":
        if self.file_size_bytes == 0 and self.checksum_video is not None:
            raise ValueError("Un checksum video sans fichier video est invalide.")
        if self.file_size_bytes > 0 and self.checksum_video is None:
            raise ValueError("Le checksum video est requis lorsqu'une video est fournie.")
        return self


class QualityMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    metric_name: str
    metric_value: float
    threshold_min: float | None
    threshold_max: float | None
    passed: bool
    details: dict[str, object]
    created_at: datetime


class RecordingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contribution_id: str
    repetition_index: int
    video_object_key: str | None
    landmark_object_key: str
    thumbnail_object_key: str | None
    feature_schema_version: str
    duration_ms: int
    source_fps: float
    target_frame_count: int
    video_width: int | None
    video_height: int | None
    file_size_bytes: int
    landmark_size_bytes: int
    checksum_video: str | None
    checksum_landmarks: str
    quality_score: float
    automatic_quality_status: AutomaticQualityStatus
    upload_confirmed_at: datetime | None
    metrics: list[QualityMetricResponse] = Field(default_factory=list)


class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contributor_id: str
    campaign_id: str
    campaign_sign_id: str
    status: ContributionStatus
    consent_snapshot: dict[str, object]
    submitted_at: datetime | None
    review_started_at: datetime | None
    completed_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    campaign: CampaignResponse | None = None
    campaign_sign: CampaignSignResponse | None = None
    recordings: list[RecordingResponse] = Field(default_factory=list)


class UploadSessionRequest(BaseModel):
    include_video: bool = False
    landmark_content_type: Literal[
        "application/gzip", "application/json", "application/octet-stream"
    ] = "application/gzip"
    video_content_type: str | None = Field(default=None, max_length=80)

    @field_validator("video_content_type")
    @classmethod
    def video_type_allowed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"video/webm", "video/webm;codecs=vp8", "video/webm;codecs=vp9", "video/mp4"}
        if value not in allowed:
            raise ValueError("Format video non autorise.")
        return value


class UploadTarget(BaseModel):
    object_key: str
    upload_url: str
    expires_in_seconds: int
    content_type: str


class UploadSessionResponse(BaseModel):
    recording_id: str
    landmark: UploadTarget
    video: UploadTarget | None = None


class ConfirmUploadRequest(BaseModel):
    checksum_landmarks: str = Field(pattern=SHA256_RE)
    checksum_video: str | None = Field(default=None, pattern=SHA256_RE)
    landmark_size_bytes: int = Field(ge=1, le=2_000_000)
    video_size_bytes: int = Field(default=0, ge=0, le=50_000_000)


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision
    reason_code: str | None = Field(default=None, max_length=80)
    comment: str | None = Field(default=None, max_length=2000)
    recording_id: str | None = Field(default=None, min_length=20, max_length=36)
    metadata: dict[str, object] = Field(default_factory=dict)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contribution_id: str
    recording_id: str | None
    reviewer_id: str
    review_type: ReviewType
    decision: ReviewDecision
    reason_code: str | None
    comment: str | None
    review_metadata: dict[str, object]
    created_at: datetime


class DatasetVersionCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    semantic_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(default="", max_length=4000)
    feature_schema_version: str = Field(default="1.0.0", min_length=1, max_length=20)
    seed: int = Field(default=42, ge=0)


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    semantic_version: str
    status: DatasetVersionStatus
    description: str
    feature_schema_version: str
    sign_count: int
    recording_count: int
    contributor_count: int
    manifest_object_key: str | None
    statistics_object_key: str | None
    created_by: str
    created_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class DatasetItemResponse(BaseModel):
    recording_id: str
    split: DatasetSplit
    sign_code: str
    anonymous_contributor_id: str
    landmark_path: str
    video_path: str | None
    checksum_landmarks: str
    checksum_video: str | None
