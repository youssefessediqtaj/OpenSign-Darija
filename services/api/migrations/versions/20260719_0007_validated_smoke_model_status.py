"""validated smoke model status

Revision ID: 20260719_0007
Revises: 20260717_0006
Create Date: 2026-07-19 03:15:00
"""

from alembic import op

revision = "20260719_0007"
down_revision = "20260717_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE modelstatus ADD VALUE IF NOT EXISTS 'VALIDATED_SMOKE'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the enum.
    pass
