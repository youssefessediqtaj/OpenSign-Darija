from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    AutomaticQualityStatus,
    CampaignStatus,
    ConsentType,
    ContributionStatus,
    DatasetSplit,
    DatasetVersionStatus,
    DominantHand,
    ExternalDatasetLabelStatus,
    ExternalDatasetLicenseStatus,
    ExternalDatasetProvider,
    ExternalDatasetSourceStatus,
    InputModality,
    RecognitionTaskType,
    ReviewDecision,
    ReviewType,
    SigningExperienceLevel,
)
from app.models.sign import Sign
from app.models.user import uuid_str


def utc_now() -> datetime:
    return datetime.now(UTC)


def enum_values(enum_class: type[ExternalDatasetProvider]) -> list[str]:
    return [member.value for member in enum_class]


class ContributorProfile(Base):
    __tablename__ = "contributor_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    preferred_interface_language: Mapped[str] = mapped_column(
        String(10), default="fr", nullable=False
    )
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    dominant_hand: Mapped[DominantHand | None] = mapped_column(Enum(DominantHand), nullable=True)
    experience_level: Mapped[SigningExperienceLevel | None] = mapped_column(
        Enum(SigningExperienceLevel), nullable=True
    )
    accessibility_preferences: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    contributions: Mapped[list["DatasetContribution"]] = relationship(back_populates="contributor")


class ConsentTemplate(Base):
    __tablename__ = "consent_templates"
    __table_args__ = (
        UniqueConstraint("code", "version", "language", name="uq_consent_template_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="fr", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    consent_template_id: Mapped[str] = mapped_column(
        ForeignKey("consent_templates.id"), nullable=False
    )
    consent_type: Mapped[ConsentType] = mapped_column(Enum(ConsentType), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    template: Mapped[ConsentTemplate] = relationship()


class CollectionCampaign(Base):
    __tablename__ = "collection_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT
    )
    target_language: Mapped[str] = mapped_column(
        String(80), default="Langue des Signes Marocaine", nullable=False
    )
    target_sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_repetitions_per_sign: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    minimum_repetitions_per_submission: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )
    maximum_repetitions_per_submission: Mapped[int] = mapped_column(
        Integer, default=8, nullable=False
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    signs: Mapped[list["CampaignSign"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignSign(Base):
    __tablename__ = "campaign_signs"
    __table_args__ = (UniqueConstraint("campaign_id", "sign_id", name="uq_campaign_sign"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("collection_campaigns.id"), nullable=False)
    sign_id: Mapped[str] = mapped_column(ForeignKey("signs.id"), nullable=False)
    target_repetitions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    minimum_duration_ms: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    maximum_duration_ms: Mapped[int] = mapped_column(Integer, default=8000, nullable=False)
    requires_left_hand: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_right_hand: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_face: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_pose: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    instruction_text: Mapped[str] = mapped_column(Text, nullable=False)
    instruction_video_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_landmark_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    campaign: Mapped[CollectionCampaign] = relationship(back_populates="signs")
    sign: Mapped["Sign"] = relationship()


class DatasetContribution(Base):
    __tablename__ = "dataset_contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    contributor_id: Mapped[str] = mapped_column(
        ForeignKey("contributor_profiles.id"), nullable=False
    )
    campaign_id: Mapped[str] = mapped_column(ForeignKey("collection_campaigns.id"), nullable=False)
    campaign_sign_id: Mapped[str] = mapped_column(ForeignKey("campaign_signs.id"), nullable=False)
    status: Mapped[ContributionStatus] = mapped_column(
        Enum(ContributionStatus), default=ContributionStatus.DRAFT
    )
    consent_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    contributor: Mapped[ContributorProfile] = relationship(back_populates="contributions")
    campaign: Mapped[CollectionCampaign] = relationship()
    campaign_sign: Mapped[CampaignSign] = relationship()
    recordings: Mapped[list["ContributionRecording"]] = relationship(
        back_populates="contribution", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ContributionReview"]] = relationship(
        back_populates="contribution", cascade="all, delete-orphan"
    )


class ContributionRecording(Base):
    __tablename__ = "contribution_recordings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    contribution_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_contributions.id"), nullable=False
    )
    repetition_index: Mapped[int] = mapped_column(Integer, nullable=False)
    video_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    landmark_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feature_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    source_fps: Mapped[float] = mapped_column(Float, nullable=False)
    target_frame_count: Mapped[int] = mapped_column(Integer, nullable=False)
    video_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    landmark_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_video: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum_landmarks: Mapped[str] = mapped_column(String(128), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    automatic_quality_status: Mapped[AutomaticQualityStatus] = mapped_column(
        Enum(AutomaticQualityStatus), default=AutomaticQualityStatus.WARNING
    )
    upload_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    contribution: Mapped[DatasetContribution] = relationship(back_populates="recordings")
    metrics: Mapped[list["RecordingQualityMetric"]] = relationship(
        back_populates="recording", cascade="all, delete-orphan"
    )


class RecordingQualityMetric(Base):
    __tablename__ = "recording_quality_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    recording_id: Mapped[str] = mapped_column(
        ForeignKey("contribution_recordings.id"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    recording: Mapped[ContributionRecording] = relationship(back_populates="metrics")


class ContributionReview(Base):
    __tablename__ = "contribution_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    contribution_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_contributions.id"), nullable=False
    )
    recording_id: Mapped[str | None] = mapped_column(
        ForeignKey("contribution_recordings.id"), nullable=True
    )
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    review_type: Mapped[ReviewType] = mapped_column(Enum(ReviewType), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    contribution: Mapped[DatasetContribution] = relationship(back_populates="reviews")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    semantic_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[DatasetVersionStatus] = mapped_column(
        Enum(DatasetVersionStatus), default=DatasetVersionStatus.DRAFT
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recording_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contributor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manifest_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    statistics_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["DatasetVersionItem"]] = relationship(
        back_populates="dataset_version", cascade="all, delete-orphan"
    )


class DatasetVersionItem(Base):
    __tablename__ = "dataset_version_items"
    __table_args__ = (
        UniqueConstraint("dataset_version_id", "recording_id", name="uq_dataset_recording"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.id"), nullable=False
    )
    recording_id: Mapped[str] = mapped_column(
        ForeignKey("contribution_recordings.id"), nullable=False
    )
    split: Mapped[DatasetSplit] = mapped_column(Enum(DatasetSplit), nullable=False)
    included_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    exclusion_reason: Mapped[str | None] = mapped_column(String(160), nullable=True)

    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="items")
    recording: Mapped[ContributionRecording] = relationship()


class ExternalDatasetSource(Base):
    __tablename__ = "external_dataset_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    provider: Mapped[ExternalDatasetProvider] = mapped_column(
        Enum(ExternalDatasetProvider, values_callable=enum_values), nullable=False
    )
    version: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    doi: Mapped[str | None] = mapped_column(String(120), nullable=True)
    task_type: Mapped[RecognitionTaskType] = mapped_column(
        Enum(RecognitionTaskType), nullable=False
    )
    modality: Mapped[InputModality] = mapped_column(Enum(InputModality), nullable=False)
    license: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    license_status: Mapped[ExternalDatasetLicenseStatus] = mapped_column(
        Enum(ExternalDatasetLicenseStatus),
        default=ExternalDatasetLicenseStatus.TO_VERIFY,
        nullable=False,
    )
    source_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ExternalDatasetSourceStatus] = mapped_column(
        Enum(ExternalDatasetSourceStatus),
        default=ExternalDatasetSourceStatus.REGISTERED,
        nullable=False,
    )
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    labels: Mapped[list["ExternalDatasetLabel"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    imports: Mapped[list["ExternalDatasetImport"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class ExternalDatasetLabel(Base):
    __tablename__ = "external_dataset_labels"
    __table_args__ = (
        UniqueConstraint("source_id", "original_label", name="uq_external_label_source_original"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("external_dataset_sources.id"), nullable=False
    )
    original_label: Mapped[str] = mapped_column(String(240), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    canonical_sign_id: Mapped[str | None] = mapped_column(ForeignKey("signs.id"), nullable=True)
    semantic_concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("semantic_concepts.id"), nullable=True
    )
    class_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[ExternalDatasetLabelStatus] = mapped_column(
        Enum(ExternalDatasetLabelStatus),
        default=ExternalDatasetLabelStatus.UNMAPPED,
        nullable=False,
    )
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signer_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    source: Mapped[ExternalDatasetSource] = relationship(back_populates="labels")
    canonical_sign: Mapped[Sign | None] = relationship(foreign_keys=[canonical_sign_id])


class ExternalDatasetImport(Base):
    __tablename__ = "external_dataset_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("external_dataset_sources.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    archive_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)

    source: Mapped[ExternalDatasetSource] = relationship(back_populates="imports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
