from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.storage.contribution_repository import ContributionRepository
from app.storage.video_storage import build_video_storage

ROOT = Path(__file__).resolve().parents[4]
REPORT_ROOT = ROOT / "artifacts" / "reports"
RELEASE_ROOT = ROOT / "ml" / "data" / "contributions" / "releases"


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _runtime() -> tuple[ContributionRepository, Any]:
    settings = get_settings()
    return (
        ContributionRepository(settings.contribution_database_file),
        build_video_storage(settings),
    )


def _valid_uuid(value: str) -> str:
    return str(UUID(value))


def command_list(_: argparse.Namespace) -> int:
    repository, _ = _runtime()
    _json({"pending": repository.list_pending()})
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    repository, storage = _runtime()
    contribution_id = _valid_uuid(args.contribution_id)
    record = repository.get_for_review(contribution_id)
    if not record:
        print("Contribution not found", file=sys.stderr)
        return 2
    path = storage.local_path(str(record["private_object_key"]))
    record["private_video_location"] = str(path) if path else "private-object-storage"
    _json(record)
    return 0


def command_approve(args: argparse.Namespace) -> int:
    if not args.confirm_all_review_checks:
        print(
            "Approval requires --confirm-all-review-checks after completing the documented review.",
            file=sys.stderr,
        )
        return 2
    repository, _ = _runtime()
    changed = repository.transition_review(
        _valid_uuid(args.contribution_id),
        "APPROVED_FOR_DATASET",
        actor=args.reviewer,
        reason="All documented review checks confirmed",
    )
    _json({"updated": changed, "review_status": "APPROVED_FOR_DATASET"})
    return 0 if changed else 2


def command_reject(args: argparse.Namespace) -> int:
    repository, _ = _runtime()
    changed = repository.transition_review(
        _valid_uuid(args.contribution_id),
        "REJECTED",
        actor=args.reviewer,
        reason=args.reason,
    )
    _json({"updated": changed, "review_status": "REJECTED"})
    return 0 if changed else 2


def command_request_withdrawal(args: argparse.Namespace) -> int:
    repository, _ = _runtime()
    changed = repository.request_withdrawal(
        _valid_uuid(args.contribution_id),
        actor=args.actor,
    )
    _json({"updated": changed, "deletion_status": "WITHDRAWAL_REQUESTED"})
    return 0 if changed else 2


def command_delete(args: argparse.Namespace) -> int:
    if not args.confirm_irreversible_delete:
        print("Deletion requires --confirm-irreversible-delete.", file=sys.stderr)
        return 2
    repository, storage = _runtime()
    contribution_id = _valid_uuid(args.contribution_id)
    record = repository.get_for_review(contribution_id)
    if not record:
        print("Contribution not found", file=sys.stderr)
        return 2
    storage.delete(str(record["private_object_key"]))
    changed = repository.mark_deleted(
        contribution_id,
        actor=args.actor,
        reason=args.reason,
    )
    _json({"updated": changed, "deletion_status": "DELETED", "video_deleted": True})
    return 0 if changed else 2


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_export(args: argparse.Namespace) -> int:
    if not args.confirm_dataset_release:
        print("Export requires --confirm-dataset-release.", file=sys.stderr)
        return 2
    if not args.release_version or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for character in args.release_version
    ):
        print("A safe release version is required.", file=sys.stderr)
        return 2
    repository, storage = _runtime()
    records = repository.list_exportable()
    destination = RELEASE_ROOT / args.release_version
    if destination.exists():
        print("Release already exists; releases are immutable.", file=sys.stderr)
        return 2
    RELEASE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{args.release_version}-", dir=RELEASE_ROOT))
    try:
        videos_root = staging / "videos"
        videos_root.mkdir(mode=0o700)
        manifest: list[dict[str, Any]] = []
        checksums: dict[str, str] = {}
        for record in records:
            relative = f"videos/{record['contribution_id']}.webm"
            target = staging / relative
            storage.copy_to(str(record["private_object_key"]), target)
            digest = _sha256(target)
            if digest != record["sha256"]:
                raise RuntimeError("Stored video checksum mismatch")
            checksums[relative] = digest
            manifest.append(
                {
                    "contribution_id": record["contribution_id"],
                    "sign_key": record["sign_key"],
                    "video_relative_path": relative,
                    "sha256": digest,
                    "mime_type": record["mime_type"],
                    "file_size_bytes": record["file_size_bytes"],
                    "duration_seconds": record["duration_seconds"],
                    "width": record["width"],
                    "height": record["height"],
                    "frame_rate": record["frame_rate"],
                    "consent_notice_version": record["consent_version"],
                    "consent_status": "ACTIVE",
                    "review_status": record["review_status"],
                    "source": "OpenSigne Darija voluntary contribution quarantine",
                }
            )
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (staging / "checksums.json").write_text(
            json.dumps(checksums, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        provenance = {
            "release_version": args.release_version,
            "created_at": datetime.now(UTC).isoformat(),
            "record_count": len(records),
            "boundary": (
                "Staging release only. It does not trigger preprocessing, training, "
                "evaluation, model replacement, or model activation."
            ),
            "contains_direct_identifiers": False,
        }
        (staging / "provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n",
            encoding="utf-8",
        )
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_ROOT / f"contributions-export-{args.release_version}.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "created",
                "release": str(destination.relative_to(ROOT)),
                "record_count": len(records),
                "created_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _json({"release": str(destination), "record_count": len(records)})
    return 0


def command_retention(args: argparse.Namespace) -> int:
    settings = get_settings()
    timestamp = datetime.now(UTC)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if settings.data_retention_days is None or settings.data_retention_days <= 0:
        report: dict[str, object] = {
            "generated_at": timestamp.isoformat(),
            "status": "BLOCKED_CONFIGURATION_REQUIRED",
            "retention_days": None,
            "mode": "report-only",
            "candidate_count": 0,
            "candidates": [],
            "executed_contribution_ids": [],
            "message": (
                "DATA_RETENTION_DAYS is UNCONFIRMED. No repository was opened "
                "and no deletion was attempted."
            ),
        }
        path = REPORT_ROOT / f"contributions-retention-{timestamp:%Y%m%dT%H%M%SZ}.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        _json({"report": str(path), **report})
        return 0
    repository, storage = _runtime()
    candidates = repository.retention_candidates(settings.data_retention_days)
    report_candidates = [
        {key: value for key, value in record.items() if key != "private_object_key"}
        for record in candidates
    ]
    executed: list[str] = []
    if args.execute:
        if not args.approved_execution:
            print("--execute also requires --approved-execution.", file=sys.stderr)
            return 2
        for record in candidates:
            contribution_id = str(record["contribution_id"])
            storage.delete(str(record["private_object_key"]))
            repository.mark_deleted(
                contribution_id,
                actor=args.actor,
                reason="Approved retention execution",
            )
            executed.append(contribution_id)
    report = {
        "generated_at": timestamp.isoformat(),
        "retention_days": settings.data_retention_days,
        "mode": "execute" if args.execute else "report-only",
        "candidate_count": len(candidates),
        "candidates": report_candidates,
        "executed_contribution_ids": executed,
        "approved_dataset_release_handling": (
            "Approved releases are excluded from automatic retention deletion and "
            "require controller-approved release policy."
        ),
    }
    path = REPORT_ROOT / f"contributions-retention-{timestamp:%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _json({"report": str(path), **report})
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Private contribution maintenance")
    subparsers = result.add_subparsers(dest="command", required=True)

    pending = subparsers.add_parser("list-pending")
    pending.set_defaults(handler=command_list)

    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("contribution_id")
    inspect.set_defaults(handler=command_inspect)

    approve = subparsers.add_parser("approve")
    approve.add_argument("contribution_id")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--confirm-all-review-checks", action="store_true")
    approve.set_defaults(handler=command_approve)

    reject = subparsers.add_parser("reject")
    reject.add_argument("contribution_id")
    reject.add_argument("--reviewer", required=True)
    reject.add_argument("--reason", required=True)
    reject.set_defaults(handler=command_reject)

    withdrawal = subparsers.add_parser("request-withdrawal")
    withdrawal.add_argument("contribution_id")
    withdrawal.add_argument("--actor", required=True)
    withdrawal.set_defaults(handler=command_request_withdrawal)

    delete = subparsers.add_parser("delete")
    delete.add_argument("contribution_id")
    delete.add_argument("--actor", required=True)
    delete.add_argument("--reason", required=True)
    delete.add_argument("--confirm-irreversible-delete", action="store_true")
    delete.set_defaults(handler=command_delete)

    export = subparsers.add_parser("export-approved")
    export.add_argument("--release-version", required=True)
    export.add_argument("--confirm-dataset-release", action="store_true")
    export.set_defaults(handler=command_export)

    retention = subparsers.add_parser("retention-check")
    retention.add_argument("--execute", action="store_true")
    retention.add_argument("--approved-execution", action="store_true")
    retention.add_argument("--actor", default="local-retention-operator")
    retention.set_defaults(handler=command_retention)
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
