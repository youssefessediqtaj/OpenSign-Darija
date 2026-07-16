"""dataset collection workflow

Revision ID: 20260716_0002
Revises: 20260716_0001
Create Date: 2026-07-16 21:20:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260716_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None


def enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    dominant_hand = enum("dominanthand", "LEFT", "RIGHT", "AMBIDEXTROUS", "UNDISCLOSED")
    experience = enum(
        "signingexperiencelevel",
        "NATIVE_SIGNER",
        "FLUENT_SIGNER",
        "LEARNER",
        "INTERPRETER",
        "UNDISCLOSED",
    )
    consent_type = enum(
        "consenttype",
        "LANDMARK_PROCESSING",
        "LANDMARK_STORAGE",
        "VIDEO_RECORDING",
        "VIDEO_STORAGE",
        "RESEARCH_USE",
        "MODEL_TRAINING",
        "PUBLIC_DATASET_RELEASE",
        "COMMERCIAL_USE",
        "CONTACT_FOR_FUTURE_STUDIES",
    )
    campaign_status = enum(
        "campaignstatus", "DRAFT", "SCHEDULED", "ACTIVE", "PAUSED", "COMPLETED", "ARCHIVED"
    )
    contribution_status = enum(
        "contributionstatus",
        "DRAFT",
        "CAPTURING",
        "READY_TO_SUBMIT",
        "UPLOADING",
        "SUBMITTED",
        "AUTOMATIC_CHECK_FAILED",
        "PENDING_LINGUIST_REVIEW",
        "LINGUIST_REJECTED",
        "PENDING_ML_REVIEW",
        "ML_REJECTED",
        "APPROVED",
        "REVISION_REQUESTED",
        "REVOKED",
        "ARCHIVED",
    )
    quality_status = enum("automaticqualitystatus", "PASSED", "WARNING", "FAILED")
    review_type = enum("reviewtype", "LINGUISTIC", "TECHNICAL", "PRIVACY", "ADMINISTRATIVE")
    review_decision = enum("reviewdecision", "APPROVED", "REJECTED", "REVISION_REQUESTED", "FLAGGED")
    dataset_status = enum(
        "datasetversionstatus", "DRAFT", "BUILDING", "VALIDATING", "READY", "PUBLISHED", "FAILED", "ARCHIVED"
    )
    dataset_split = enum("datasetsplit", "TRAIN", "VALIDATION", "TEST", "HOLDOUT")

    op.create_table(
        "contributor_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("preferred_interface_language", sa.String(length=10), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("dominant_hand", dominant_hand, nullable=True),
        sa.Column("experience_level", experience, nullable=True),
        sa.Column("accessibility_preferences", sa.JSON(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_contributor_profiles_public_id"), "contributor_profiles", ["public_id"], unique=True)

    op.create_table(
        "consent_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "version", "language", name="uq_consent_template_version"),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("consent_template_id", sa.String(length=36), nullable=False),
        sa.Column("consent_type", consent_type, nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=128), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["consent_template_id"], ["consent_templates.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consent_records_user_id"), "consent_records", ["user_id"], unique=False)

    op.create_table(
        "collection_campaigns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", campaign_status, nullable=False),
        sa.Column("target_language", sa.String(length=80), nullable=False),
        sa.Column("target_sign_count", sa.Integer(), nullable=False),
        sa.Column("target_repetitions_per_sign", sa.Integer(), nullable=False),
        sa.Column("minimum_repetitions_per_submission", sa.Integer(), nullable=False),
        sa.Column("maximum_repetitions_per_submission", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_collection_campaigns_slug"), "collection_campaigns", ["slug"], unique=True)

    op.create_table(
        "campaign_signs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=False),
        sa.Column("sign_id", sa.String(length=36), nullable=False),
        sa.Column("target_repetitions", sa.Integer(), nullable=False),
        sa.Column("minimum_duration_ms", sa.Integer(), nullable=False),
        sa.Column("maximum_duration_ms", sa.Integer(), nullable=False),
        sa.Column("requires_left_hand", sa.Boolean(), nullable=False),
        sa.Column("requires_right_hand", sa.Boolean(), nullable=False),
        sa.Column("requires_face", sa.Boolean(), nullable=False),
        sa.Column("requires_pose", sa.Boolean(), nullable=False),
        sa.Column("instruction_text", sa.Text(), nullable=False),
        sa.Column("instruction_video_path", sa.String(length=255), nullable=True),
        sa.Column("reference_landmark_path", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["campaign_id"], ["collection_campaigns.id"]),
        sa.ForeignKeyConstraint(["sign_id"], ["signs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "sign_id", name="uq_campaign_sign"),
    )

    op.create_table(
        "dataset_contributions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contributor_id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=False),
        sa.Column("campaign_sign_id", sa.String(length=36), nullable=False),
        sa.Column("status", contribution_status, nullable=False),
        sa.Column("consent_snapshot", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["campaign_id"], ["collection_campaigns.id"]),
        sa.ForeignKeyConstraint(["campaign_sign_id"], ["campaign_signs.id"]),
        sa.ForeignKeyConstraint(["contributor_id"], ["contributor_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contribution_recordings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contribution_id", sa.String(length=36), nullable=False),
        sa.Column("repetition_index", sa.Integer(), nullable=False),
        sa.Column("video_object_key", sa.String(length=500), nullable=True),
        sa.Column("landmark_object_key", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_object_key", sa.String(length=500), nullable=True),
        sa.Column("feature_schema_version", sa.String(length=20), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("source_fps", sa.Float(), nullable=False),
        sa.Column("target_frame_count", sa.Integer(), nullable=False),
        sa.Column("video_width", sa.Integer(), nullable=True),
        sa.Column("video_height", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("landmark_size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_video", sa.String(length=128), nullable=True),
        sa.Column("checksum_landmarks", sa.String(length=128), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("automatic_quality_status", quality_status, nullable=False),
        sa.Column("upload_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["contribution_id"], ["dataset_contributions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recording_quality_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recording_id", sa.String(length=36), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("threshold_min", sa.Float(), nullable=True),
        sa.Column("threshold_max", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recording_id"], ["contribution_recordings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contribution_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contribution_id", sa.String(length=36), nullable=False),
        sa.Column("recording_id", sa.String(length=36), nullable=True),
        sa.Column("reviewer_id", sa.String(length=36), nullable=False),
        sa.Column("review_type", review_type, nullable=False),
        sa.Column("decision", review_decision, nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["contribution_id"], ["dataset_contributions.id"]),
        sa.ForeignKeyConstraint(["recording_id"], ["contribution_recordings.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("semantic_version", sa.String(length=40), nullable=False),
        sa.Column("status", dataset_status, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=20), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("recording_count", sa.Integer(), nullable=False),
        sa.Column("contributor_count", sa.Integer(), nullable=False),
        sa.Column("manifest_object_key", sa.String(length=500), nullable=True),
        sa.Column("statistics_object_key", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dataset_version_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("recording_id", sa.String(length=36), nullable=False),
        sa.Column("split", dataset_split, nullable=False),
        sa.Column("included_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exclusion_reason", sa.String(length=160), nullable=True),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"]),
        sa.ForeignKeyConstraint(["recording_id"], ["contribution_recordings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_version_id", "recording_id", name="uq_dataset_recording"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("dataset_version_items")
    op.drop_table("dataset_versions")
    op.drop_table("contribution_reviews")
    op.drop_table("recording_quality_metrics")
    op.drop_table("contribution_recordings")
    op.drop_table("dataset_contributions")
    op.drop_table("campaign_signs")
    op.drop_index(op.f("ix_collection_campaigns_slug"), table_name="collection_campaigns")
    op.drop_table("collection_campaigns")
    op.drop_index(op.f("ix_consent_records_user_id"), table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_table("consent_templates")
    op.drop_index(op.f("ix_contributor_profiles_public_id"), table_name="contributor_profiles")
    op.drop_table("contributor_profiles")
