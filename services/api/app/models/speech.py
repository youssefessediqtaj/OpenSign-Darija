from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SpeechGenerationStatus
from app.models.message import Message
from app.models.user import User, uuid_str


class SpeechVoice(Base):
    __tablename__ = "speech_voices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    voice_code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    locale: Mapped[str] = mapped_column(String(20), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    license_info: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class SpeechGeneration(Base):
    __tablename__ = "speech_generations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    anonymous_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    voice_id: Mapped[str] = mapped_column(ForeignKey("speech_voices.id"), nullable=False)
    status: Mapped[SpeechGenerationStatus] = mapped_column(
        Enum(SpeechGenerationStatus), default=SpeechGenerationStatus.CREATED, nullable=False
    )
    requested_language: Mapped[str] = mapped_column(String(20), nullable=False)
    synthesis_language: Mapped[str] = mapped_column(String(20), nullable=False)
    original_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text_length: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    normalization_version: Mapped[str] = mapped_column(String(80), nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cache_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    audio_object_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    audio_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    message: Mapped[Message] = relationship()
    user: Mapped[User | None] = relationship()
    voice: Mapped[SpeechVoice] = relationship()
