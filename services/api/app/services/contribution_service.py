from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from starlette.datastructures import UploadFile

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.contributions import (
    ContributionReceiptResponse,
    ContributionSubmissionFields,
)
from app.services import contribution_validation
from app.services.contribution_catalog import get_active_contribution_sign
from app.storage.contribution_repository import (
    ContributionRepository,
    ContributionRepositoryError,
    DuplicateContributionError,
)
from app.storage.video_storage import VideoStorage, VideoStorageError, build_video_storage

logger = logging.getLogger("opensign.security.contributions")


class ContributionService:
    def __init__(
        self,
        settings: Settings,
        repository: ContributionRepository | None = None,
        storage: VideoStorage | None = None,
    ):
        self.settings = settings
        self.repository = repository or ContributionRepository(settings.contribution_database_file)
        self.storage = storage or build_video_storage(settings)

    def health_check(self) -> bool:
        return self.repository.health_check() and self.storage.health_check()

    async def create(
        self,
        fields: ContributionSubmissionFields,
        video: UploadFile,
    ) -> ContributionReceiptResponse:
        if fields.age < 18:
            raise ApiError(
                "ADULTS_ONLY",
                "Le programme initial de contribution est réservé aux personnes majeures.",
                422,
            )
        if not fields.consent_accepted:
            raise ApiError("CONSENT_REQUIRED", "Le consentement explicite est requis.", 422)
        if fields.consent_notice_version != self.settings.consent_notice_version:
            raise ApiError(
                "OBSOLETE_NOTICE_VERSION",
                "La notice a été mise à jour. Veuillez la relire avant de continuer.",
                409,
            )
        sign = get_active_contribution_sign(fields.sign_key)
        if sign is None:
            raise ApiError("UNKNOWN_SIGN", "Le signe sélectionné n’est pas autorisé.", 422)
        if not video.content_type:
            raise ApiError("MISSING_VIDEO_TYPE", "Le type de la vidéo est requis.", 422)

        contribution_id = uuid4()
        staged_path: Path | None = None
        promoted = False
        object_key = f"pending/{contribution_id}/{contribution_id}.webm"
        try:
            staged_path = self.storage.create_staging_path(str(contribution_id))
            await self._copy_upload(video, staged_path)
            metadata = contribution_validation.validate_staged_video(
                staged_path,
                declared_mime_type=video.content_type,
                settings=self.settings,
                expected_min_duration_seconds=sign.expected_min_duration_seconds,
                expected_max_duration_seconds=sign.expected_max_duration_seconds,
            )
            now = datetime.now(UTC)
            timestamp = now.isoformat()
            with self.repository.transaction() as connection:
                self.repository.insert(
                    connection,
                    contribution_id=str(contribution_id),
                    full_name=fields.full_name,
                    age=fields.age,
                    city=fields.city,
                    consent_version=fields.consent_notice_version,
                    consent_timestamp=timestamp,
                    sign_key=fields.sign_key,
                    private_object_key=object_key,
                    sha256=metadata.sha256,
                    mime_type=metadata.mime_type,
                    file_size_bytes=metadata.file_size_bytes,
                    duration_seconds=metadata.duration_seconds,
                    width=metadata.width,
                    height=metadata.height,
                    frame_rate=metadata.frame_rate,
                    created_at=timestamp,
                )
                self.storage.promote(staged_path, object_key)
                promoted = True
            logger.info(
                "contribution_received",
                extra={"event": "contribution_received", "contribution_id": str(contribution_id)},
            )
            return ContributionReceiptResponse(
                status="received",
                contribution_id=contribution_id,
                sign_key=fields.sign_key,
                created_at=now,
                consent_notice_version=fields.consent_notice_version,
                review_status="pending",
                deletion_request_instructions=(
                    f"Conservez cette référence et contactez "
                    f"{self.settings.data_rights_contact} pour exercer vos droits."
                ),
            )
        except DuplicateContributionError as error:
            raise ApiError(
                "DUPLICATE_CONTRIBUTION",
                "Cette vidéo a déjà été reçue.",
                409,
            ) from error
        except (ContributionRepositoryError, VideoStorageError) as error:
            raise ApiError(
                "CONTRIBUTION_STORAGE_UNAVAILABLE",
                "Le stockage des contributions est momentanément indisponible.",
                503,
            ) from error
        finally:
            if promoted:
                # The database transaction may still have failed during commit. Verify
                # consistency; if no receipt exists, remove the otherwise orphaned video.
                try:
                    if self.repository.get_receipt(str(contribution_id)) is None:
                        self.storage.delete(object_key)
                except (ContributionRepositoryError, VideoStorageError):
                    logger.error(
                        "contribution_consistency_cleanup_failed",
                        extra={
                            "event": "contribution_consistency_cleanup_failed",
                            "contribution_id": str(contribution_id),
                        },
                    )
            if staged_path is not None:
                staged_path.unlink(missing_ok=True)
            await video.close()

    async def _copy_upload(self, video: UploadFile, destination: Path) -> None:
        maximum = self.settings.contribution_max_video_bytes
        received = 0
        try:
            with destination.open("wb") as stream:
                while chunk := await video.read(1024 * 1024):
                    received += len(chunk)
                    if received > maximum:
                        raise ApiError(
                            "VIDEO_TOO_LARGE",
                            "La vidéo dépasse la taille maximale autorisée.",
                            413,
                            {"max_bytes": maximum},
                        )
                    stream.write(chunk)
                stream.flush()
                stream.close()
            destination.chmod(0o600)
        except OSError as error:
            raise VideoStorageError("Private upload staging is unavailable") from error

    def receipt(self, contribution_id: UUID) -> ContributionReceiptResponse:
        try:
            stored = self.repository.get_receipt(str(contribution_id))
        except ContributionRepositoryError as error:
            raise ApiError(
                "CONTRIBUTION_STORAGE_UNAVAILABLE",
                "Le stockage des contributions est momentanément indisponible.",
                503,
            ) from error
        if stored is None:
            raise ApiError("CONTRIBUTION_NOT_FOUND", "Contribution introuvable.", 404)
        return ContributionReceiptResponse(
            status="received",
            contribution_id=contribution_id,
            sign_key=str(stored["sign_key"]),
            created_at=datetime.fromisoformat(str(stored["created_at"])),
            consent_notice_version=str(stored["consent_version"]),
            review_status="pending",
            deletion_request_instructions=(
                f"Conservez cette référence et contactez "
                f"{self.settings.data_rights_contact} pour exercer vos droits."
            ),
        )
