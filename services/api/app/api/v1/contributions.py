from __future__ import annotations

from collections import Counter
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from app.core.config import get_settings
from app.core.contribution_settings import contribution_readiness
from app.core.errors import ApiError
from app.schemas.contributions import (
    ContributionNoticeResponse,
    ContributionReceiptResponse,
    ContributionSignResponse,
    ContributionStatusResponse,
    ContributionSubmissionFields,
    NoticeField,
)
from app.services.contribution_catalog import CONTRIBUTION_SIGNS
from app.services.contribution_request_protection import enforce_contribution_rate_limit
from app.services.contribution_service import ContributionService
from app.storage.contribution_repository import ContributionRepositoryError
from app.storage.video_storage import VideoStorageError

router = APIRouter(prefix="/contributions", tags=["contributions"])
FORM_FIELDS = {
    "full_name",
    "age",
    "city",
    "sign_key",
    "consent_accepted",
    "consent_notice_version",
    "video",
}


def _service() -> ContributionService:
    settings = get_settings()
    try:
        return ContributionService(settings)
    except (ContributionRepositoryError, VideoStorageError) as error:
        raise ApiError(
            "CONTRIBUTION_STORAGE_UNAVAILABLE",
            "Le stockage des contributions est momentanément indisponible.",
            503,
        ) from error


def _require_collection_open() -> None:
    readiness = contribution_readiness(get_settings())
    if not readiness.public_submission_allowed:
        raise ApiError("CONTRIBUTION_COLLECTION_CLOSED", readiness.message, 503)


def _require_safe_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        return
    settings = get_settings()
    split = urlsplit(origin)
    origin_normalized = f"{split.scheme}://{split.netloc}"
    request_origin = f"{request.url.scheme}://{request.headers.get('host', request.url.netloc)}"
    allowed = {item.rstrip("/") for item in settings.cors_origins}
    if origin_normalized != request_origin.rstrip("/") and origin_normalized not in allowed:
        raise ApiError("ORIGIN_NOT_ALLOWED", "L’origine de la requête n’est pas autorisée.", 403)


@router.get("/status", response_model=ContributionStatusResponse)
def status() -> ContributionStatusResponse:
    settings = get_settings()
    readiness = contribution_readiness(settings)
    storage_status: Literal["not_checked", "available", "unavailable"] = "not_checked"
    available = False
    if readiness.public_submission_allowed:
        try:
            available = _service().health_check()
            storage_status = "available" if available else "unavailable"
        except ApiError:
            storage_status = "unavailable"
    return ContributionStatusResponse(
        collection_enabled=settings.contribution_collection_enabled,
        compliance_configured=readiness.configured,
        public_submission_allowed=readiness.public_submission_allowed,
        collection_available=readiness.public_submission_allowed and available,
        storage_status=storage_status,
        message=(
            readiness.message
            if storage_status != "unavailable"
            else "La collecte est temporairement indisponible."
        ),
        missing_configuration=list(readiness.missing_configuration),
        invalid_configuration=list(readiness.invalid_configuration),
        readiness_dwell_ms=settings.contribution_readiness_dwell_ms,
    )


@router.get("/signs", response_model=list[ContributionSignResponse])
def signs() -> list[ContributionSignResponse]:
    approved = get_settings().contribution_reference_videos_approved
    return [
        ContributionSignResponse(
            key=sign.key,
            label_ar=sign.label_ar,
            darija_transliteration=sign.darija_transliteration,
            reference_video_identifier=sign.reference_video_identifier,
            reference_video_url=sign.reference_video_path if approved else None,
            poster_url=sign.poster_path,
            reference_video_approved=approved,
            recording_instructions=sign.recording_instructions,
            active=sign.active,
            expected_min_duration_seconds=sign.expected_min_duration_seconds,
            expected_max_duration_seconds=sign.expected_max_duration_seconds,
        )
        for sign in CONTRIBUTION_SIGNS
    ]


@router.get("/notice", response_model=ContributionNoticeResponse)
def notice() -> ContributionNoticeResponse:
    settings = get_settings()
    readiness = contribution_readiness(settings)
    recipients = [
        item.strip()
        for item in settings.data_recipient_categories.replace(";", ",").split(",")
        if item.strip()
    ]
    purpose = settings.data_processing_purpose
    if readiness.configured:
        summary = (
            f"Vos données sont recueillies par {settings.data_controller_name} pour {purpose}. "
            "Le refus empêche uniquement l’envoi d’une contribution et ne change pas "
            "l’accès à la reconnaissance normale."
        )
    else:
        summary = (
            "Aucune donnée de contribution n’est recueillie tant que la préparation "
            "juridique reste incomplète. Cette notice est affichée en aperçu et ses "
            "champs doivent être finalisés par le responsable du traitement."
        )
    return ContributionNoticeResponse(
        language="fr",
        arabic_translation_status="structure_ready_translation_pending",
        title="Notice d’information — contribution vidéo",
        summary=summary,
        controller_name=settings.data_controller_name,
        controller_address=settings.data_controller_address,
        controller_contact=settings.data_controller_contact,
        purpose=purpose,
        collected_data=[
            NoticeField(name="nom complet", required=True),
            NoticeField(name="âge", required=True),
            NoticeField(name="ville", required=True),
            NoticeField(name="signe sélectionné", required=True),
            NoticeField(name="vidéo", required=True),
            NoticeField(name="métadonnées de consentement", required=True),
            NoticeField(name="métadonnées techniques d’envoi", required=True),
        ],
        refusal_consequence=(
            "Aucune contribution ne sera envoyée, sans effet sur l’utilisation "
            "du service normal de reconnaissance."
        ),
        recipient_categories=recipients,
        model_collaborator_sharing=settings.data_model_collaborator_sharing,
        storage_location_category=settings.data_storage_location_category,
        retention_days=settings.data_retention_days,
        rights=["accès", "rectification", "opposition", "retrait", "suppression"],
        rights_request_method=settings.data_rights_contact,
        cndp_procedure_type=settings.cndp_procedure_type,
        cndp_reference=settings.cndp_receipt_or_authorization_reference,
        notice_version=settings.consent_notice_version,
        consent_timestamp_source="Horodatage UTC généré par le serveur lors de l’envoi.",
        consent_checkbox_text=(
            "J’ai lu la notice d’information et j’accepte que mon nom, mon âge, "
            "ma ville et ma vidéo soient utilisés pour développer et évaluer les "
            "modèles OpenSigne Darija, selon les finalités et la durée indiquées."
        ),
        complete_notice=[
            "La contribution est volontaire et réservée aux adultes dans cette phase.",
            "La vidéo est conservée dans une zone privée de quarantaine et soumise à une revue.",
            "Elle n’est ni publiée, ni ajoutée automatiquement à un jeu de données ou à un modèle.",
            (
                "Le responsable de traitement définit la vérification d’identité "
                "applicable aux demandes de droits."
            ),
        ],
    )


@router.post("", response_model=ContributionReceiptResponse, status_code=201)
async def submit(request: Request) -> ContributionReceiptResponse:
    _require_collection_open()
    _require_safe_origin(request)
    enforce_contribution_rate_limit(request)
    settings = get_settings()
    try:
        form = await request.form(
            max_files=1,
            max_fields=6,
            max_part_size=settings.contribution_max_video_bytes,
        )
    except Exception as error:
        raise ApiError("INVALID_MULTIPART", "Le formulaire envoyé est invalide.", 422) from error
    keys = [key for key, _ in form.multi_items()]
    counts = Counter(keys)
    unexpected = sorted(set(keys) - FORM_FIELDS)
    missing = sorted(FORM_FIELDS - set(keys))
    duplicates = sorted(key for key, count in counts.items() if count != 1)
    if unexpected or missing or duplicates:
        raise ApiError(
            "INVALID_FORM_FIELDS",
            "Les champs du formulaire ne correspondent pas au contrat attendu.",
            422,
            {"unexpected": unexpected, "missing": missing, "duplicates": duplicates},
        )
    upload = form["video"]
    if not isinstance(upload, UploadFile):
        raise ApiError("MISSING_VIDEO", "Une vidéo est requise.", 422)
    try:
        fields = ContributionSubmissionFields.model_validate(
            {
                "full_name": form["full_name"],
                "age": form["age"],
                "city": form["city"],
                "sign_key": form["sign_key"],
                "consent_accepted": form["consent_accepted"],
                "consent_notice_version": form["consent_notice_version"],
            }
        )
    except ValidationError as error:
        raise ApiError(
            "INVALID_CONTRIBUTION_FIELDS",
            "Les informations de contribution sont invalides.",
            422,
        ) from error
    return await _service().create(fields, upload)


@router.get("/{contribution_id}/receipt", response_model=ContributionReceiptResponse)
def receipt(contribution_id: UUID) -> ContributionReceiptResponse:
    _require_collection_open()
    return _service().receipt(contribution_id)
