from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InputModality, ModelStatus, RecognitionTaskType, RiskLevel, SignStatus
from app.models.user import uuid_str


class SignCategory(Base):
    __tablename__ = "sign_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(120), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    signs: Mapped[list["Sign"]] = relationship(back_populates="category")


class Sign(Base):
    __tablename__ = "signs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    canonical_meaning: Mapped[str] = mapped_column(String(120), nullable=False)
    darija_arabic: Mapped[str] = mapped_column(String(120), nullable=False)
    darija_latin: Mapped[str] = mapped_column(String(120), nullable=False)
    french_translation: Mapped[str] = mapped_column(String(120), nullable=False)
    english_translation: Mapped[str] = mapped_column(String(120), nullable=False)
    category_id: Mapped[str] = mapped_column(ForeignKey("sign_categories.id"), nullable=False)
    status: Mapped[SignStatus] = mapped_column(Enum(SignStatus), default=SignStatus.EXPERIMENTAL)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.NORMAL)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    category: Mapped[SignCategory] = relationship(back_populates="signs")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    semantic_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.DRAFT)
    task_type: Mapped[RecognitionTaskType] = mapped_column(
        Enum(RecognitionTaskType),
        default=RecognitionTaskType.WORD_ISOLATED,
        nullable=False,
    )
    input_modality: Mapped[InputModality] = mapped_column(
        Enum(InputModality),
        default=InputModality.LANDMARK_SEQUENCE,
        nullable=False,
    )
    architecture: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.id"), nullable=True
    )
    feature_schema_version: Mapped[str] = mapped_column(String(40), default="1.0.0", nullable=False)
    source_dataset_versions: Mapped[list[object]] = mapped_column(
        JSON, default=list, nullable=False
    )
    supported_classes: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)
    vocabulary_size: Mapped[int] = mapped_column(default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    labels_json: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    thresholds_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    calibration_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
