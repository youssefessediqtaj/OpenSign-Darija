from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RecognitionStatus
from app.models.user import User, uuid_str


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship()
    predictions: Mapped[list["RecognitionPrediction"]] = relationship(
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
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    recognition_session: Mapped[RecognitionSession] = relationship(back_populates="predictions")
