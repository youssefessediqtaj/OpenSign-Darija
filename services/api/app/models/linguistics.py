from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    LinguisticAssetStatus,
    LinguisticLanguage,
    LinguisticRegister,
    LinguisticScript,
    RiskLevel,
    SemanticConceptType,
)
from app.models.user import uuid_str


class SemanticConcept(Base):
    __tablename__ = "semantic_concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    concept_type: Mapped[SemanticConceptType] = mapped_column(
        Enum(SemanticConceptType), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    entries: Mapped[list["LinguisticEntry"]] = relationship(
        back_populates="semantic_concept", cascade="all, delete-orphan"
    )


class SignSemanticMapping(Base):
    __tablename__ = "sign_semantic_mappings"
    __table_args__ = (
        UniqueConstraint(
            "sign_id", "semantic_concept_id", "context", name="uq_sign_concept_context"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    sign_id: Mapped[str] = mapped_column(ForeignKey("signs.id"), nullable=False)
    semantic_concept_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_concepts.id"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    context: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    semantic_concept: Mapped[SemanticConcept] = relationship()


class LinguisticEntry(Base):
    __tablename__ = "linguistic_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    semantic_concept_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_concepts.id"), nullable=False
    )
    language: Mapped[LinguisticLanguage] = mapped_column(Enum(LinguisticLanguage), nullable=False)
    script: Mapped[LinguisticScript] = mapped_column(Enum(LinguisticScript), nullable=False)
    value: Mapped[str] = mapped_column(String(240), nullable=False)
    variant: Mapped[str] = mapped_column(String(80), default="default", nullable=False)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    register: Mapped[LinguisticRegister] = mapped_column(
        Enum(LinguisticRegister), default=LinguisticRegister.NEUTRAL, nullable=False
    )
    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    semantic_concept: Mapped[SemanticConcept] = relationship(back_populates="entries")


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(160), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
    template_structure: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.NORMAL)
    status: Mapped[LinguisticAssetStatus] = mapped_column(
        Enum(LinguisticAssetStatus), default=LinguisticAssetStatus.ACTIVE, nullable=False
    )
    version: Mapped[str] = mapped_column(String(40), default="1.0.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
