"""model registry and recognition metadata

Revision ID: 20260716_0003
Revises: 20260716_0002
Create Date: 2026-07-16 22:20:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260716_0003"
down_revision = "20260716_0002"
branch_labels = None
depends_on = None


def _existing_enum(*values: str, name: str) -> sa.Enum:
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.ENUM(*values, name=name, create_type=False)
    return sa.Enum(*values, name=name)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE modelstatus ADD VALUE IF NOT EXISTS 'TRAINING'")
        op.execute("ALTER TYPE modelstatus ADD VALUE IF NOT EXISTS 'EVALUATING'")
        op.execute("ALTER TYPE modelstatus ADD VALUE IF NOT EXISTS 'READY'")
        op.execute("ALTER TYPE modelstatus ADD VALUE IF NOT EXISTS 'REJECTED'")
    recognition_decision_type = sa.Enum("known", "uncertain", "unknown", name="recognitiondecision")
    confidence_level_type = sa.Enum("high", "medium", "low", name="confidencelevel")
    correction_type_type = sa.Enum(
        "CONFIRMED_TOP_1",
        "SELECTED_ALTERNATIVE",
        "SELECTED_OTHER_SIGN",
        "MARKED_UNKNOWN",
        "MANUAL_TEXT",
        name="correctiontype",
    )
    recognition_decision_type.create(bind, checkfirst=True)
    confidence_level_type.create(bind, checkfirst=True)
    correction_type_type.create(bind, checkfirst=True)
    recognition_decision = _existing_enum("known", "uncertain", "unknown", name="recognitiondecision")
    confidence_level = _existing_enum("high", "medium", "low", name="confidencelevel")
    correction_type = _existing_enum(
        "CONFIRMED_TOP_1",
        "SELECTED_ALTERNATIVE",
        "SELECTED_OTHER_SIGN",
        "MARKED_UNKNOWN",
        "MANUAL_TEXT",
        name="correctiontype",
    )

    with op.batch_alter_table("model_versions") as batch:
        batch.add_column(sa.Column("architecture", sa.String(length=80), nullable=False, server_default=""))
        batch.add_column(sa.Column("dataset_version_id", sa.String(length=36), nullable=True))
        batch.add_column(
            sa.Column("feature_schema_version", sa.String(length=40), nullable=False, server_default="1.0.0")
        )
        batch.add_column(sa.Column("labels_json", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("thresholds_json", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("calibration_json", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("checksum", sa.String(length=64), nullable=False, server_default=""))
        batch.add_column(sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        if op.get_bind().dialect.name != "sqlite":
            batch.create_foreign_key(
                "fk_model_versions_dataset_version_id",
                "dataset_versions",
                ["dataset_version_id"],
                ["id"],
            )

    with op.batch_alter_table("recognition_sessions") as batch:
        batch.add_column(
            sa.Column("feature_schema_version", sa.String(length=40), nullable=False, server_default="1.0.0")
        )
        batch.add_column(sa.Column("inference_mode", sa.String(length=20), nullable=False, server_default="mock"))
        batch.add_column(sa.Column("model_name", sa.String(length=120), nullable=False, server_default=""))
        batch.add_column(sa.Column("model_version", sa.String(length=40), nullable=False, server_default=""))
        batch.add_column(sa.Column("decision", recognition_decision, nullable=True))
        batch.add_column(sa.Column("confidence_level", confidence_level, nullable=True))
        batch.add_column(sa.Column("processing_time_ms", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("quality_score", sa.Float(), nullable=True))
        batch.add_column(sa.Column("error_code", sa.String(length=80), nullable=True))

    with op.batch_alter_table("recognition_predictions") as batch:
        batch.add_column(sa.Column("is_unknown", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "user_corrections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recognition_session_id", sa.String(length=36), nullable=False),
        sa.Column("selected_sign_id", sa.String(length=36), nullable=True),
        sa.Column("correction_type", correction_type, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recognition_session_id"], ["recognition_sessions.id"]),
        sa.ForeignKeyConstraint(["selected_sign_id"], ["signs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_corrections")
    with op.batch_alter_table("recognition_predictions") as batch:
        batch.drop_column("is_unknown")
    with op.batch_alter_table("recognition_sessions") as batch:
        for column in [
            "error_code",
            "quality_score",
            "processing_time_ms",
            "confidence_level",
            "decision",
            "model_version",
            "model_name",
            "inference_mode",
            "feature_schema_version",
        ]:
            batch.drop_column(column)
    with op.batch_alter_table("model_versions") as batch:
        if op.get_bind().dialect.name != "sqlite":
            batch.drop_constraint("fk_model_versions_dataset_version_id", type_="foreignkey")
        for column in [
            "archived_at",
            "validated_at",
            "size_bytes",
            "checksum",
            "calibration_json",
            "thresholds_json",
            "labels_json",
            "feature_schema_version",
            "dataset_version_id",
            "architecture",
        ]:
            batch.drop_column(column)
