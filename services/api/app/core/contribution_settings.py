from dataclasses import dataclass

from app.core.config import Settings

PROCEDURE_TYPES = {"declaration", "prior_authorization"}

REQUIRED_COMPLIANCE_FIELDS: tuple[tuple[str, str], ...] = (
    ("DATA_CONTROLLER_NAME", "data_controller_name"),
    ("DATA_CONTROLLER_ADDRESS", "data_controller_address"),
    ("DATA_CONTROLLER_CONTACT", "data_controller_contact"),
    ("DATA_PROCESSING_PURPOSE", "data_processing_purpose"),
    ("DATA_RECIPIENT_CATEGORIES", "data_recipient_categories"),
    ("DATA_MODEL_COLLABORATOR_SHARING", "data_model_collaborator_sharing"),
    ("DATA_STORAGE_LOCATION_CATEGORY", "data_storage_location_category"),
    ("DATA_RETENTION_DAYS", "data_retention_days"),
    ("DATA_RIGHTS_CONTACT", "data_rights_contact"),
    ("CNDP_PROCEDURE_TYPE", "cndp_procedure_type"),
    (
        "CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE",
        "cndp_receipt_or_authorization_reference",
    ),
    ("CONSENT_NOTICE_VERSION", "consent_notice_version"),
)


@dataclass(frozen=True)
class ContributionReadiness:
    configured: bool
    public_submission_allowed: bool
    missing_configuration: tuple[str, ...]
    invalid_configuration: tuple[str, ...]
    message: str


def contribution_readiness(settings: Settings) -> ContributionReadiness:
    missing = [
        env_name
        for env_name, attribute in REQUIRED_COMPLIANCE_FIELDS
        if getattr(settings, attribute) in ("", None)
    ]
    invalid: list[str] = []
    if settings.cndp_procedure_type and settings.cndp_procedure_type not in PROCEDURE_TYPES:
        invalid.append("CNDP_PROCEDURE_TYPE")
    if settings.data_retention_days is not None and settings.data_retention_days <= 0:
        invalid.append("DATA_RETENTION_DAYS")
    if not settings.contribution_reference_videos_approved:
        missing.append("CONTRIBUTION_REFERENCE_VIDEOS_APPROVED")

    configured = not missing and not invalid
    allowed = settings.contribution_collection_enabled and configured
    if not settings.contribution_collection_enabled:
        message = "La collecte des contributions n’est pas encore ouverte."
    elif not configured:
        message = "La collecte reste fermée tant que la préparation juridique est incomplète."
    else:
        message = "La collecte des contributions est ouverte."
    return ContributionReadiness(
        configured=configured,
        public_submission_allowed=allowed,
        missing_configuration=tuple(missing),
        invalid_configuration=tuple(invalid),
        message=message,
    )
