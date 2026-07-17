"""external datasets and multi task recognition

Revision ID: 20260717_0006
Revises: 20260717_0005
Create Date: 2026-07-17 18:15:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260717_0006"
down_revision = "20260717_0005"
branch_labels = None
depends_on = None


def _enum(name: str, *values: str) -> sa.Enum:
    if op.get_bind().dialect.name == "postgresql":
        enum_type = postgresql.ENUM(*values, name=name)
        enum_type.create(op.get_bind(), checkfirst=True)
        return postgresql.ENUM(*values, name=name, create_type=False)
    return sa.Enum(*values, name=name)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE messageitemtype ADD VALUE IF NOT EXISTS 'FINGERSPELLED_LETTER'")
        op.execute("ALTER TYPE messageitemtype ADD VALUE IF NOT EXISTS 'FINGERSPELLED_WORD'")
        op.execute("ALTER TYPE messageitemsource ADD VALUE IF NOT EXISTS 'FINGERSPELLING'")

    task_type = _enum(
        "recognitiontasktype", "ALPHABET_STATIC", "WORD_ISOLATED", "CONTINUOUS_SIGNING"
    )
    modality = _enum("inputmodality", "LANDMARK_SEQUENCE", "IMAGE", "VIDEO")
    provider = _enum("externaldatasetprovider", "kaggle", "mendeley", "documentation")
    license_status = _enum(
        "externaldatasetlicensestatus", "VERIFIED", "TO_VERIFY", "INCOMPATIBLE", "UNKNOWN"
    )
    source_status = _enum(
        "externaldatasetsourcestatus",
        "REGISTERED",
        "LICENSE_PENDING",
        "DOWNLOAD_READY",
        "DOWNLOADING",
        "DOWNLOADED",
        "AUDITING",
        "AUDIT_FAILED",
        "REQUIRES_REVIEW",
        "VALIDATED",
        "PREPROCESSING",
        "READY",
        "DISABLED",
        "REJECTED",
    )
    label_status = _enum(
        "externaldatasetlabelstatus",
        "UNMAPPED",
        "AUTOMATIC_SUGGESTION",
        "PENDING_REVIEW",
        "APPROVED",
        "REJECTED",
        "AMBIGUOUS",
        "DUPLICATE",
    )

    with op.batch_alter_table("model_versions") as batch:
        batch.add_column(
            sa.Column("task_type", task_type, nullable=False, server_default="WORD_ISOLATED")
        )
        batch.add_column(
            sa.Column(
                "input_modality", modality, nullable=False, server_default="LANDMARK_SEQUENCE"
            )
        )
        batch.add_column(sa.Column("source_dataset_versions", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("supported_classes", sa.JSON(), nullable=False, server_default="[]"))

    op.create_table(
        "external_dataset_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("provider", provider, nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("doi", sa.String(length=120), nullable=True),
        sa.Column("task_type", task_type, nullable=False),
        sa.Column("modality", modality, nullable=False),
        sa.Column("license", sa.String(length=80), nullable=False),
        sa.Column("license_status", license_status, nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("status", source_status, nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_dataset_sources_code", "external_dataset_sources", ["code"], unique=True)

    op.create_table(
        "external_dataset_labels",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("original_label", sa.String(length=240), nullable=False),
        sa.Column("normalized_label", sa.String(length=240), nullable=False),
        sa.Column("canonical_sign_id", sa.String(length=36), nullable=True),
        sa.Column("semantic_concept_id", sa.String(length=36), nullable=True),
        sa.Column("class_code", sa.String(length=120), nullable=True),
        sa.Column("status", label_status, nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("signer_count", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["canonical_sign_id"], ["signs.id"]),
        sa.ForeignKeyConstraint(["semantic_concept_id"], ["semantic_concepts.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["external_dataset_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "original_label", name="uq_external_label_source_original"),
    )

    op.create_table(
        "external_dataset_imports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("archive_checksum", sa.String(length=64), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("total_size_bytes", sa.Integer(), nullable=False),
        sa.Column("report_path", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["external_dataset_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("external_dataset_imports")
    op.drop_table("external_dataset_labels")
    op.drop_index("ix_external_dataset_sources_code", table_name="external_dataset_sources")
    op.drop_table("external_dataset_sources")
    with op.batch_alter_table("model_versions") as batch:
        batch.drop_column("supported_classes")
        batch.drop_column("source_dataset_versions")
        batch.drop_column("input_modality")
        batch.drop_column("task_type")
