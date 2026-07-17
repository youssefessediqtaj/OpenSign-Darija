from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SpeechGenerationStatus
from app.models.speech import SpeechGeneration
from app.services.object_storage import ObjectStorage


def cleanup_expired_audio(dry_run: bool = False) -> dict[str, int]:
    matched = 0
    deleted = 0
    now = datetime.now(UTC)
    with SessionLocal() as db:
        try:
            generations = db.scalars(
                select(SpeechGeneration).where(
                    SpeechGeneration.expires_at <= now,
                    SpeechGeneration.deleted_at.is_(None),
                    SpeechGeneration.status == SpeechGenerationStatus.COMPLETED,
                )
            ).all()
        except ProgrammingError:
            return {"matched": 0, "deleted": 0}
        for generation in generations:
            matched += 1
            if not dry_run:
                if generation.audio_object_key:
                    ObjectStorage().delete_object(
                        get_settings().speech_audio_bucket, generation.audio_object_key
                    )
                generation.status = SpeechGenerationStatus.EXPIRED
                generation.deleted_at = now
                deleted += 1
        if not dry_run:
            db.commit()
    return {"matched": matched, "deleted": deleted}


if __name__ == "__main__":
    print(cleanup_expired_audio())
