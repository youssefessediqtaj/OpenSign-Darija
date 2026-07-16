from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.dataset import AuditLog, DatasetContribution
from app.models.enums import ContributionStatus

STALE_UPLOAD_STATUSES = {
    ContributionStatus.DRAFT,
    ContributionStatus.CAPTURING,
    ContributionStatus.UPLOADING,
    ContributionStatus.AUTOMATIC_CHECK_FAILED,
}


def cleanup_orphan_uploads(*, dry_run: bool) -> dict[str, object]:
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.dataset_cleanup_draft_days)
    with SessionLocal() as db:
        contributions = list(
            db.scalars(
                select(DatasetContribution).where(
                    DatasetContribution.status.in_(STALE_UPLOAD_STATUSES),
                    DatasetContribution.created_at < cutoff,
                    DatasetContribution.revoked_at.is_(None),
                )
            )
        )
        ids = [contribution.id for contribution in contributions]
        if not dry_run:
            for contribution in contributions:
                previous_status = contribution.status
                contribution.status = ContributionStatus.REVOKED
                contribution.revoked_at = datetime.now(UTC)
                db.add(
                    AuditLog(
                        action="CLEANUP_ORPHAN_UPLOAD",
                        target_type="DatasetContribution",
                        target_id=contribution.id,
                        details={
                            "previous_status": previous_status.value,
                            "cutoff": cutoff.isoformat(),
                        },
                    )
                )
            db.commit()
        return {
            "dry_run": dry_run,
            "cutoff": cutoff.isoformat(),
            "matched": len(ids),
            "contribution_ids": ids,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mark stale draft/upload contributions as revoked."
    )
    parser.add_argument("--execute", action="store_true", help="Apply changes. Default is dry-run.")
    args = parser.parse_args()
    print(json.dumps(cleanup_orphan_uploads(dry_run=not args.execute), indent=2))


if __name__ == "__main__":
    main()
