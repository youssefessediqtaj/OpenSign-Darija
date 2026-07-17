"""speech audio generation

Revision ID: 20260717_0005
Revises: 20260717_0004
Create Date: 2026-07-17 17:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0005"
down_revision: str | None = "20260717_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


STATUS_VALUES = (
    "CREATED",
    "QUEUED",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "EXPIRED",
    "DELETED",
)


def speech_status_enum(create_type: bool = True) -> postgresql.ENUM:
    return postgresql.ENUM(*STATUS_VALUES, name="speechgenerationstatus", create_type=create_type)


def upgrade() -> None:
    bind = op.get_bind()
    status_type: sa.TypeEngine[str] = sa.String(length=20)
    if bind.dialect.name == "postgresql":
        speech_status_enum().create(bind, checkfirst=True)
        status_type = speech_status_enum(create_type=False)
    op.create_table(
        "speech_voices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("voice_code", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("license_info", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_experimental", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voice_code"),
    )
    op.create_table(
        "speech_generations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("anonymous_session_id", sa.String(length=120), nullable=True),
        sa.Column("voice_id", sa.String(length=36), nullable=False),
        sa.Column("status", status_type, nullable=False),
        sa.Column("requested_language", sa.String(length=20), nullable=False),
        sa.Column("synthesis_language", sa.String(length=20), nullable=False),
        sa.Column("original_text_hash", sa.String(length=64), nullable=False),
        sa.Column("normalized_text_hash", sa.String(length=64), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("normalization_version", sa.String(length=80), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("cache_key", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("audio_object_key", sa.String(length=300), nullable=True),
        sa.Column("audio_checksum", sa.String(length=64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["voice_id"], ["speech_voices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "message_id",
        "user_id",
        "anonymous_session_id",
        "original_text_hash",
        "normalized_text_hash",
        "cache_key",
        "idempotency_key",
    ]:
        op.create_index(f"ix_speech_generations_{column}", "speech_generations", [column])


def downgrade() -> None:
    op.drop_table("speech_generations")
    op.drop_table("speech_voices")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        speech_status_enum().drop(bind, checkfirst=True)
