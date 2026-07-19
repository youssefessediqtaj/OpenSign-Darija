from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import ModelStatus, RecognitionTaskType
from app.models.sign import ModelVersion
from app.tools.register_mosl_word_smoke import MODEL_NAME, MODEL_VERSION, register_model


def activate_model(artifact_dir: Path) -> dict[str, Any]:
    settings = get_settings()
    if settings.app_env != "development" or not settings.allow_smoke_model_activation:
        raise RuntimeError(
            "MoSL smoke activation is allowed only with APP_ENV=development and "
            "ALLOW_SMOKE_MODEL_ACTIVATION=true"
        )

    registration = register_model(artifact_dir)
    with SessionLocal() as db:
        model = db.scalar(
            select(ModelVersion).where(
                ModelVersion.name == MODEL_NAME,
                ModelVersion.semantic_version == MODEL_VERSION,
                ModelVersion.task_type == RecognitionTaskType.WORD_ISOLATED,
            )
        )
        if model is None:
            raise RuntimeError("MoSL smoke model registration was not found after registration")
        if model.status != ModelStatus.VALIDATED_SMOKE:
            raise RuntimeError("MoSL smoke model must remain VALIDATED_SMOKE")

        deactivated: list[str] = []
        for active in db.scalars(
            select(ModelVersion).where(
                ModelVersion.task_type == RecognitionTaskType.WORD_ISOLATED,
                ModelVersion.is_active.is_(True),
                ModelVersion.id != model.id,
            )
        ):
            active.is_active = False
            active.archived_at = datetime.now(UTC)
            if active.status != ModelStatus.VALIDATED_SMOKE:
                active.status = ModelStatus.ARCHIVED
            deactivated.append(active.id)

        model.is_active = True
        model.activated_at = datetime.now(UTC)
        db.commit()
        db.refresh(model)
        return {
            "registration": registration,
            "activated": True,
            "id": model.id,
            "name": model.name,
            "semantic_version": model.semantic_version,
            "status": model.status.value,
            "task_type": model.task_type.value,
            "is_active": model.is_active,
            "deactivated_model_ids": deactivated,
            "production_ready": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Activate the MoSL WORD_ISOLATED smoke model in development only."
    )
    parser.add_argument(
        "--artifact-dir", type=Path, default=Path("artifacts/models/mosl-word-smoke-v1")
    )
    args = parser.parse_args()
    print(json.dumps(activate_model(args.artifact_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
