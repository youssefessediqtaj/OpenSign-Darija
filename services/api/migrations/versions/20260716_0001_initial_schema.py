"""initial schema

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16 15:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sign_status = sa.Enum("DRAFT", "EXPERIMENTAL", "ACTIVE", "DEPRECATED", name="signstatus")
    risk_level = sa.Enum("NORMAL", "SENSITIVE", "MEDICAL", "LEGAL", "FINANCIAL", "EMERGENCY", name="risklevel")
    model_status = sa.Enum("DRAFT", "VALIDATING", "ACTIVE", "ARCHIVED", "FAILED", name="modelstatus")
    recognition_status = sa.Enum("CREATED", "PROCESSING", "COMPLETED", "UNCERTAIN", "FAILED", name="recognitionstatus")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "sign_categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name_fr", sa.String(length=120), nullable=False),
        sa.Column("name_ar", sa.String(length=120), nullable=False),
        sa.Column("name_en", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sign_categories_slug"), "sign_categories", ["slug"], unique=True)
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("semantic_version", sa.String(length=40), nullable=False),
        sa.Column("status", model_status, nullable=False),
        sa.Column("vocabulary_size", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("artifact_path", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_table(
        "signs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("canonical_meaning", sa.String(length=120), nullable=False),
        sa.Column("darija_arabic", sa.String(length=120), nullable=False),
        sa.Column("darija_latin", sa.String(length=120), nullable=False),
        sa.Column("french_translation", sa.String(length=120), nullable=False),
        sa.Column("english_translation", sa.String(length=120), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=False),
        sa.Column("status", sign_status, nullable=False),
        sa.Column("risk_level", risk_level, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["sign_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_signs_slug"), "signs", ["slug"], unique=True)
    op.create_table(
        "recognition_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("model_version_id", sa.String(length=36), nullable=True),
        sa.Column("status", recognition_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recognition_predictions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recognition_session_id", sa.String(length=36), nullable=False),
        sa.Column("sign_id", sa.String(length=36), nullable=True),
        sa.Column("predicted_label", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recognition_session_id"], ["recognition_sessions.id"]),
        sa.ForeignKeyConstraint(["sign_id"], ["signs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("recognition_predictions")
    op.drop_table("recognition_sessions")
    op.drop_index(op.f("ix_signs_slug"), table_name="signs")
    op.drop_table("signs")
    op.drop_table("user_roles")
    op.drop_table("model_versions")
    op.drop_index(op.f("ix_sign_categories_slug"), table_name="sign_categories")
    op.drop_table("sign_categories")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
