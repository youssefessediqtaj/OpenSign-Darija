from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContributionStatusResponse(BaseModel):
    collection_enabled: bool
    compliance_configured: bool
    public_submission_allowed: bool
    collection_available: bool
    storage_status: Literal["not_checked", "available", "unavailable"]
    message: str
    missing_configuration: list[str]
    invalid_configuration: list[str]
    readiness_dwell_ms: int


class ContributionSignResponse(BaseModel):
    key: str
    label_ar: str
    darija_transliteration: str | None
    reference_video_identifier: str
    reference_video_url: str | None
    poster_url: str
    reference_video_approved: bool
    recording_instructions: str
    active: bool
    expected_min_duration_seconds: float
    expected_max_duration_seconds: float


class NoticeField(BaseModel):
    name: str
    required: bool


class ContributionNoticeResponse(BaseModel):
    language: Literal["fr"]
    arabic_translation_status: Literal["structure_ready_translation_pending"]
    title: str
    summary: str
    controller_name: str
    controller_address: str
    controller_contact: str
    purpose: str
    collected_data: list[NoticeField]
    refusal_consequence: str
    recipient_categories: list[str]
    model_collaborator_sharing: str
    storage_location_category: str
    retention_days: int | None
    rights: list[str]
    rights_request_method: str
    cndp_procedure_type: str
    cndp_reference: str
    notice_version: str
    consent_timestamp_source: str
    consent_checkbox_text: str
    complete_notice: list[str]


class ContributionSubmissionFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=0, le=120)
    city: str = Field(min_length=2, max_length=80)
    sign_key: str = Field(min_length=1, max_length=32)
    consent_accepted: bool
    consent_notice_version: str = Field(min_length=1, max_length=80)

    @field_validator("full_name", "city")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(character) < 32 for character in value):
            raise ValueError("control characters are not allowed")
        return value


class ContributionReceiptResponse(BaseModel):
    status: Literal["received"]
    contribution_id: UUID
    sign_key: str
    created_at: datetime
    consent_notice_version: str
    review_status: Literal["pending"]
    deletion_request_instructions: str


class StoredContributionReceipt(BaseModel):
    status: Literal["received"]
    contribution_id: UUID
    sign_key: str
    created_at: datetime
    consent_notice_version: str
    review_status: str
    deletion_request_instructions: str


class VideoMetadata(BaseModel):
    sha256: str
    mime_type: str
    file_size_bytes: int
    duration_seconds: float
    width: int
    height: int
    frame_rate: float | None
