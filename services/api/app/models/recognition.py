from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ConfidenceLevel, CorrectionType, RecognitionDecision, RecognitionStatus
from app.models.user import User, uuid_str


def enum_values(
    enum_class: type[RecognitionDecision] | type[ConfidenceLevel] | type[CorrectionType],
) -> list[str]:
    return [member.value for member in enum_class]


class RecognitionSession(Base):
    __tablename__ = "recognition_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    model_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_versions.id"), nullable=True
    )
    status: Mapped[RecognitionStatus] = mapped_column(
        Enum(RecognitionStatus), default=RecognitionStatus.CREATED, nullable=False
    )
    feature_schema_version: Mapped[str] = mapped_column(String(40), default="1.0.0", nullable=False)
    inference_mode: Mapped[str] = mapped_column(String(20), default="mock", nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    decision: Mapped[RecognitionDecision | None] = mapped_column(
        Enum(RecognitionDecision, values_callable=enum_values), nullable=True
    )
    confidence_level: Mapped[ConfidenceLevel | None] = mapped_column(
        Enum(ConfidenceLevel, values_callable=enum_values), nullable=True
    )
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship()
    predictions: Mapped[list["RecognitionPrediction"]] = relationship(
        back_populates="recognition_session", cascade="all, delete-orphan"
    )
    corrections: Mapped[list["UserCorrection"]] = relationship(
        back_populates="recognition_session", cascade="all, delete-orphan"
    )


class RecognitionPrediction(Base):
    __tablename__ = "recognition_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    recognition_session_id: Mapped[str] = mapped_column(
        ForeignKey("recognition_sessions.id"), nullable=False
    )
    sign_id: Mapped[str | None] = mapped_column(ForeignKey("signs.id"), nullable=True)
    predicted_label: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    is_unknown: Mapped[bool] = mapped_column(default=False, nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    recognition_session: Mapped[RecognitionSession] = relationship(back_populates="predictions")


class UserCorrection(Base):
    __tablename__ = "user_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    recognition_session_id: Mapped[str] = mapped_column(
        ForeignKey("recognition_sessions.id"), nullable=False
    )
    selected_sign_id: Mapped[str | None] = mapped_column(ForeignKey("signs.id"), nullable=True)
    correction_type: Mapped[CorrectionType] = mapped_column(
        Enum(CorrectionType, values_callable=enum_values), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    recognition_session: Mapped[RecognitionSession] = relationship(back_populates="corrections")
