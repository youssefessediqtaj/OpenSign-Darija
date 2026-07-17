"""messages and controlled linguistics

Revision ID: 20260717_0004
Revises: 20260716_0003
Create Date: 2026-07-17 03:25:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260717_0004"
down_revision = "20260716_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    risk_level = (
        postgresql.ENUM(
            "NORMAL",
            "SENSITIVE",
            "MEDICAL",
            "LEGAL",
            "FINANCIAL",
            "EMERGENCY",
            name="risklevel",
            create_type=False,
        )
        if op.get_bind().dialect.name == "postgresql"
        else sa.Enum(
            "NORMAL", "SENSITIVE", "MEDICAL", "LEGAL", "FINANCIAL", "EMERGENCY", name="risklevel"
        )
    )
    op.create_table(
        "semantic_concepts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name_fr", sa.String(length=160), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "concept_type",
            sa.Enum(
                "PRONOUN",
                "ACTION",
                "OBJECT",
                "LOCATION",
                "QUESTION",
                "NEGATION",
                "AFFIRMATION",
                "POLITENESS",
                "TIME",
                "QUANTITY",
                "HEALTH",
                "EMERGENCY",
                "PERSON",
                "PUNCTUATION",
                "OTHER",
                name="semanticconcepttype",
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_semantic_concepts_code", "semantic_concepts", ["code"], unique=True)

    op.create_table(
        "linguistic_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("semantic_concept_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.Enum("DARIJA", "FRENCH", "ENGLISH", name="linguisticlanguage"), nullable=False),
        sa.Column("script", sa.Enum("ARABIC", "LATIN", "LATIN_ARABIZI", name="linguisticscript"), nullable=False),
        sa.Column("value", sa.String(length=240), nullable=False),
        sa.Column("variant", sa.String(length=80), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column(
            "register",
            sa.Enum("NEUTRAL", "POLITE", "INFORMAL", "FORMAL", "MEDICAL", "EMERGENCY", name="linguisticregister"),
            nullable=False,
        ),
        sa.Column("gender", sa.String(length=40), nullable=True),
        sa.Column("number", sa.String(length=40), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["semantic_concept_id"], ["semantic_concepts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sign_semantic_mappings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sign_id", sa.String(length=36), nullable=False),
        sa.Column("semantic_concept_id", sa.String(length=36), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("context", sa.String(length=120), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["semantic_concept_id"], ["semantic_concepts.id"]),
        sa.ForeignKeyConstraint(["sign_id"], ["signs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sign_id", "semantic_concept_id", "context", name="uq_sign_concept_context"),
    )

    op.create_table(
        "message_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name_fr", sa.String(length=160), nullable=False),
        sa.Column("name_ar", sa.String(length=160), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("template_structure", sa.JSON(), nullable=False),
        sa.Column("risk_level", risk_level, nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "VALIDATING", "ACTIVE", "DEPRECATED", name="linguisticassetstatus"), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_templates_code", "message_templates", ["code"], unique=True)

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("anonymous_session_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "GENERATING", "READY", "COMPLETED", "ARCHIVED", "DELETED", name="messagestatus"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("raw_semantic_sequence", sa.JSON(), nullable=False),
        sa.Column("generated_darija_arabic", sa.Text(), nullable=True),
        sa.Column("generated_darija_latin", sa.Text(), nullable=True),
        sa.Column("generated_french", sa.Text(), nullable=True),
        sa.Column("generated_english", sa.Text(), nullable=True),
        sa.Column("final_darija_arabic", sa.Text(), nullable=True),
        sa.Column("final_darija_latin", sa.Text(), nullable=True),
        sa.Column("final_french", sa.Text(), nullable=True),
        sa.Column("final_english", sa.Text(), nullable=True),
        sa.Column("generation_strategy", sa.String(length=80), nullable=False),
        sa.Column("generation_version", sa.String(length=40), nullable=False),
        sa.Column("generation_metadata", sa.JSON(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_anonymous_session_id", "messages", ["anonymous_session_id"])

    op.create_table(
        "message_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.Enum("CONFIRMED_SIGN", "MANUAL_WORD", "PUNCTUATION", "TEMPLATE_ELEMENT", "SYSTEM_INSERTED", name="messageitemtype"), nullable=False),
        sa.Column("sign_id", sa.String(length=36), nullable=True),
        sa.Column("semantic_concept_id", sa.String(length=36), nullable=True),
        sa.Column("recognition_session_id", sa.String(length=36), nullable=True),
        sa.Column("source", sa.Enum("RECOGNITION_TOP_1", "RECOGNITION_ALTERNATIVE", "USER_CORRECTION", "MANUAL_INPUT", "LINGUISTIC_RULE", "TEMPLATE", name="messageitemsource"), nullable=False),
        sa.Column("display_label", sa.String(length=240), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["recognition_session_id"], ["recognition_sessions.id"]),
        sa.ForeignKeyConstraint(["semantic_concept_id"], ["semantic_concepts.id"]),
        sa.ForeignKeyConstraint(["sign_id"], ["signs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "position", name="uq_message_item_position"),
        sa.UniqueConstraint("message_id", "recognition_session_id", name="uq_message_recognition_item"),
    )

    op.create_table(
        "message_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.Enum("ITEM_ADDED", "ITEM_REMOVED", "ITEM_MOVED", "ITEM_REPLACED", "TEXT_EDITED", "GENERATED", "REGENERATED", "RESTORED", "FINALIZED", name="messagerevisionchangetype"), nullable=False),
        sa.Column("before_snapshot", sa.JSON(), nullable=False),
        sa.Column("after_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "revision_number", name="uq_message_revision_number"),
    )
    op.create_index("ix_message_revisions_idempotency_key", "message_revisions", ["idempotency_key"])


def downgrade() -> None:
    op.drop_index("ix_message_revisions_idempotency_key", table_name="message_revisions")
    op.drop_table("message_revisions")
    op.drop_table("message_items")
    op.drop_index("ix_messages_anonymous_session_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_message_templates_code", table_name="message_templates")
    op.drop_table("message_templates")
    op.drop_table("sign_semantic_mappings")
    op.drop_table("linguistic_entries")
    op.drop_index("ix_semantic_concepts_code", table_name="semantic_concepts")
    op.drop_table("semantic_concepts")
