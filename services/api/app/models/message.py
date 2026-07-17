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
    MessageItemSource,
    MessageItemType,
    MessageRevisionChangeType,
    MessageStatus,
)
from app.models.user import User, uuid_str


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    anonymous_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus), default=MessageStatus.DRAFT, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    raw_semantic_sequence: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)
    generated_darija_arabic: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_darija_latin: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_french: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_english: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_darija_arabic: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_darija_latin: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_french: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_english: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_strategy: Mapped[str] = mapped_column(
        String(80), default="template_rules", nullable=False
    )
    generation_version: Mapped[str] = mapped_column(String(40), default="1.0.0", nullable=False)
    generation_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship()
    items: Mapped[list["MessageItem"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", order_by="MessageItem.position"
    )
    revisions: Mapped[list["MessageRevision"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageRevision.revision_number",
    )


class MessageItem(Base):
    __tablename__ = "message_items"
    __table_args__ = (
        UniqueConstraint("message_id", "position", name="uq_message_item_position"),
        UniqueConstraint(
            "message_id", "recognition_session_id", name="uq_message_recognition_item"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[MessageItemType] = mapped_column(Enum(MessageItemType), nullable=False)
    sign_id: Mapped[str | None] = mapped_column(ForeignKey("signs.id"), nullable=True)
    semantic_concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("semantic_concepts.id"), nullable=True
    )
    recognition_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("recognition_sessions.id"), nullable=True
    )
    source: Mapped[MessageItemSource] = mapped_column(Enum(MessageItemSource), nullable=False)
    display_label: Mapped[str] = mapped_column(String(240), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    message: Mapped[Message] = relationship(back_populates="items")


class MessageRevision(Base):
    __tablename__ = "message_revisions"
    __table_args__ = (
        UniqueConstraint("message_id", "revision_number", name="uq_message_revision_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    change_type: Mapped[MessageRevisionChangeType] = mapped_column(
        Enum(MessageRevisionChangeType), nullable=False
    )
    before_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    after_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    message: Mapped[Message] = relationship(back_populates="revisions")
