from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExternalDatasetImportResponse(BaseModel):
    id: str
    source_id: str
    status: str
    archive_checksum: str | None
    file_count: int
    total_size_bytes: int
    report_path: str | None
    started_at: datetime
    completed_at: datetime | None
    error_code: str | None


class ExternalDatasetLabelResponse(BaseModel):
    id: str
    source_id: str
    original_label: str
    normalized_label: str
    canonical_sign_id: str | None
    semantic_concept_id: str | None
    class_code: str | None
    status: str
    sample_count: int
    signer_count: int | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ExternalDatasetLabelUpdateRequest(BaseModel):
    normalized_label: str | None = Field(default=None, max_length=240)
    canonical_sign_id: str | None = None
    semantic_concept_id: str | None = None
    class_code: str | None = Field(default=None, max_length=120)
    status: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ExternalDatasetSourceResponse(BaseModel):
    id: str
    code: str
    name: str
    provider: str
    version: str
    doi: str | None
    task_type: str
    modality: str
    license: str
    license_status: str
    source_metadata: dict[str, Any]
    checksum: str | None
    status: str
    imported_at: datetime | None
    validated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    label_count: int = 0
    latest_import: ExternalDatasetImportResponse | None = None


class ExternalDatasetActionResponse(BaseModel):
    source_id: str
    status: str
    message: str
    report_path: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
