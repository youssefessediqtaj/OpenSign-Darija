from datetime import UTC, datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.enums import (
    MessageItemSource,
    MessageItemType,
    MessageRevisionChangeType,
    MessageStatus,
    SpeechGenerationStatus,
)
from app.models.linguistics import SemanticConcept, SignSemanticMapping
from app.models.message import Message, MessageItem, MessageRevision
from app.models.recognition import RecognitionSession, UserCorrection
from app.models.sign import Sign
from app.models.speech import SpeechGeneration
from app.models.user import User
from app.schemas.messages import (
    AddMessageItemRequest,
    CreateMessageRequest,
    GenerateMessageRequest,
    GenerationResponse,
    MessageItemResponse,
    MessageListResponse,
    MessageResponse,
    MessageRevisionResponse,
    ReorderMessageItemsRequest,
    SpeechPrepareRequest,
    SpeechPrepareResponse,
    UpdateMessageItemRequest,
    UpdateMessageRequest,
)
from app.services.linguistics import LinguisticEngine
from app.services.linguistics.engine import GenerationInput
from app.services.linguistics.validation import validate_text_length
from app.services.object_storage import ObjectStorage

router = APIRouter(prefix="/messages", tags=["messages"])


def anonymous_id(
    explicit: str | None = None,
    header: str | None = None,
    query: str | None = None,
) -> str | None:
    return explicit or header or query


def list_of_strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def list_of_dicts(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def snapshot(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "status": message.status.value,
        "sequence": message.raw_semantic_sequence,
        "generated_darija_arabic": message.generated_darija_arabic,
        "final_darija_arabic": message.final_darija_arabic,
        "items": [
            {
                "id": item.id,
                "position": item.position,
                "display_label": item.display_label,
                "source": item.source.value,
            }
            for item in sorted(message.items, key=lambda entry: entry.position)
        ],
    }


def next_revision_number(message: Message) -> int:
    if not message.revisions:
        return 1
    return max(revision.revision_number for revision in message.revisions) + 1


def add_revision(
    db: Session,
    message: Message,
    change_type: MessageRevisionChangeType,
    before: dict[str, Any],
    created_by: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    if idempotency_key:
        existing = db.scalar(
            select(MessageRevision).where(
                MessageRevision.message_id == message.id,
                MessageRevision.idempotency_key == idempotency_key,
            )
        )
        if existing:
            return
    db.add(
        MessageRevision(
            message_id=message.id,
            revision_number=next_revision_number(message),
            change_type=change_type,
            before_snapshot=before,
            after_snapshot=snapshot(message),
            created_by=created_by,
            idempotency_key=idempotency_key,
        )
    )


def load_message(db: Session, message_id: str) -> Message:
    message = db.scalar(
        select(Message)
        .options(selectinload(Message.items), selectinload(Message.revisions))
        .where(Message.id == message_id, Message.deleted_at.is_(None))
    )
    if message is None:
        raise ApiError("NOT_FOUND", "Message introuvable.", 404)
    return message


def assert_message_access(
    message: Message,
    current_user: User | None,
    anon: str | None,
    write: bool = False,
) -> None:
    if message.user_id:
        if current_user is None or current_user.id != message.user_id:
            raise ApiError("FORBIDDEN", "Acces refuse a ce message.", 403)
        return
    if message.anonymous_session_id and anon != message.anonymous_session_id:
        raise ApiError("FORBIDDEN", "Session invite invalide pour ce message.", 403)
    if write and message.status == MessageStatus.DELETED:
        raise ApiError("INVALID_STATUS", "Ce message est supprime.", 409)


def concept_for_sign(db: Session, sign_id: str) -> SemanticConcept:
    mapping = db.scalar(
        select(SignSemanticMapping)
        .where(SignSemanticMapping.sign_id == sign_id, SignSemanticMapping.is_default.is_(True))
        .order_by(SignSemanticMapping.priority.asc())
    )
    if mapping is None:
        raise ApiError("NO_CONCEPT_MAPPING", "Aucun concept valide pour ce signe.", 422)
    concept = db.get(SemanticConcept, mapping.semantic_concept_id)
    if concept is None or not concept.is_active:
        raise ApiError("INACTIVE_CONCEPT", "Le concept associe est indisponible.", 422)
    return concept


def message_risk_level(items: list[MessageItem], concepts_by_id: dict[str, SemanticConcept]) -> str:
    for item in items:
        concept = concepts_by_id.get(item.semantic_concept_id or "")
        if concept and concept.concept_type.value == "EMERGENCY":
            return "EMERGENCY"
    for item in items:
        concept = concepts_by_id.get(item.semantic_concept_id or "")
        if concept and concept.concept_type.value == "HEALTH":
            return "MEDICAL"
    return "NORMAL"


def item_response(
    item: MessageItem, concepts_by_id: dict[str, SemanticConcept]
) -> MessageItemResponse:
    concept = concepts_by_id.get(item.semantic_concept_id or "")
    return MessageItemResponse(
        id=item.id,
        position=item.position,
        item_type=item.item_type.value,
        sign_id=item.sign_id,
        semantic_concept_id=item.semantic_concept_id,
        semantic_concept_code=concept.code if concept else None,
        recognition_session_id=item.recognition_session_id,
        source=item.source.value,
        display_label=item.display_label,
        metadata=item.metadata_json,
        created_at=item.created_at,
    )


def message_response(db: Session, message: Message, include_items: bool = True) -> MessageResponse:
    concepts = db.scalars(select(SemanticConcept)).all()
    concepts_by_id = {concept.id: concept for concept in concepts}
    items = sorted(message.items, key=lambda item: item.position)
    return MessageResponse(
        id=message.id,
        user_id=message.user_id,
        anonymous_session_id=message.anonymous_session_id,
        status=message.status.value,
        title=message.title,
        raw_semantic_sequence=message.raw_semantic_sequence,
        generated_darija_arabic=message.generated_darija_arabic,
        generated_darija_latin=message.generated_darija_latin,
        generated_french=message.generated_french,
        generated_english=message.generated_english,
        final_darija_arabic=message.final_darija_arabic,
        final_darija_latin=message.final_darija_latin,
        final_french=message.final_french,
        final_english=message.final_english,
        generation_strategy=message.generation_strategy,
        generation_version=message.generation_version,
        generation_metadata=message.generation_metadata,
        is_favorite=message.is_favorite,
        item_count=len(items),
        risk_level=message_risk_level(items, concepts_by_id),
        items=[item_response(item, concepts_by_id) for item in items] if include_items else [],
        created_at=message.created_at,
        updated_at=message.updated_at,
        completed_at=message.completed_at,
    )


@router.post("", response_model=MessageResponse)
def create_message(
    payload: CreateMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    anon = (
        None if current_user else anonymous_id(payload.anonymous_session_id, x_anonymous_session_id)
    )
    if current_user is None and not anon:
        raise ApiError("ANONYMOUS_SESSION_REQUIRED", "Session invite requise.", 400)
    message = Message(
        user_id=current_user.id if current_user else None,
        anonymous_session_id=anon,
        title=payload.title,
    )
    db.add(message)
    db.flush()
    add_revision(
        db,
        message,
        MessageRevisionChangeType.ITEM_ADDED,
        {},
        current_user.id if current_user else None,
    )
    db.commit()
    db.refresh(message)
    return message_response(db, message)


@router.get("", response_model=MessageListResponse)
def list_messages(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
    anonymous_session_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    favorite: Annotated[bool | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessageListResponse:
    anon = anonymous_id(header=x_anonymous_session_id, query=anonymous_session_id)
    query = select(Message).options(selectinload(Message.items)).where(Message.deleted_at.is_(None))
    if current_user:
        query = query.where(Message.user_id == current_user.id)
    elif anon:
        query = query.where(Message.user_id.is_(None), Message.anonymous_session_id == anon)
    else:
        return MessageListResponse(items=[], total=0, limit=limit, offset=offset)
    if status:
        query = query.where(Message.status == MessageStatus(status))
    if favorite is not None:
        query = query.where(Message.is_favorite.is_(favorite))
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                Message.title.ilike(pattern),
                Message.final_darija_arabic.ilike(pattern),
                Message.generated_darija_arabic.ilike(pattern),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    messages = db.scalars(
        query.order_by(Message.updated_at.desc()).limit(limit).offset(offset)
    ).all()
    return MessageListResponse(
        items=[message_response(db, message, include_items=False) for message in messages],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
    anonymous_session_id: Annotated[str | None, Query()] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(
        message,
        current_user,
        anonymous_id(header=x_anonymous_session_id, query=anonymous_session_id),
    )
    return message_response(db, message)


@router.patch("/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: str,
    payload: UpdateMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    validate_text_length(
        payload.final_darija_arabic,
        payload.final_darija_latin,
        payload.final_french,
        payload.final_english,
    )
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    before = snapshot(message)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(message, key, value)
    message.status = (
        MessageStatus.READY if message.status == MessageStatus.DRAFT else message.status
    )
    add_revision(
        db,
        message,
        MessageRevisionChangeType.TEXT_EDITED,
        before,
        current_user.id if current_user else None,
    )
    db.commit()
    return message_response(db, message)


@router.delete("/{message_id}")
def delete_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> dict[str, str]:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    message.status = MessageStatus.DELETED
    message.deleted_at = datetime.now(UTC)
    for generation in db.scalars(
        select(SpeechGeneration).where(SpeechGeneration.message_id == message.id)
    ).all():
        if generation.audio_object_key:
            ObjectStorage().delete_object(
                get_settings().speech_audio_bucket, generation.audio_object_key
            )
        generation.status = SpeechGenerationStatus.DELETED
        generation.deleted_at = datetime.now(UTC)
    db.commit()
    return {"status": "deleted", "message_id": message_id}


@router.post("/{message_id}/archive", response_model=MessageResponse)
def archive_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    message.status = MessageStatus.ARCHIVED
    db.commit()
    return message_response(db, message)


@router.post("/{message_id}/duplicate", response_model=MessageResponse)
def duplicate_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    duplicate = Message(
        user_id=message.user_id,
        anonymous_session_id=message.anonymous_session_id,
        title=f"Copie - {message.title or 'message'}",
        raw_semantic_sequence=message.raw_semantic_sequence,
        generated_darija_arabic=message.generated_darija_arabic,
        generated_darija_latin=message.generated_darija_latin,
        generated_french=message.generated_french,
        generated_english=message.generated_english,
        final_darija_arabic=message.final_darija_arabic,
        final_darija_latin=message.final_darija_latin,
        final_french=message.final_french,
        final_english=message.final_english,
        generation_metadata=message.generation_metadata,
    )
    db.add(duplicate)
    db.flush()
    for item in sorted(message.items, key=lambda entry: entry.position):
        db.add(
            MessageItem(
                message_id=duplicate.id,
                position=item.position,
                item_type=item.item_type,
                sign_id=item.sign_id,
                semantic_concept_id=item.semantic_concept_id,
                recognition_session_id=None,
                source=item.source,
                display_label=item.display_label,
                metadata_json=item.metadata_json,
            )
        )
    db.commit()
    db.refresh(duplicate)
    return message_response(db, duplicate)


@router.post("/{message_id}/favorite", response_model=MessageResponse)
def favorite_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    message.is_favorite = True
    db.commit()
    return message_response(db, message)


@router.delete("/{message_id}/favorite", response_model=MessageResponse)
def unfavorite_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    message.is_favorite = False
    db.commit()
    return message_response(db, message)


@router.post("/{message_id}/items", response_model=MessageResponse)
def add_item(
    message_id: str,
    payload: AddMessageItemRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    if len(message.items) >= get_settings().message_max_items:
        raise ApiError("TOO_MANY_ITEMS", "Le message contient trop d'elements.", 413)
    if payload.idempotency_key:
        existing = next(
            (
                item
                for item in message.items
                if item.metadata_json.get("idempotency_key") == payload.idempotency_key
            ),
            None,
        )
        if existing:
            return message_response(db, message)
    before = snapshot(message)
    sign_id = payload.sign_id
    source = MessageItemSource(payload.source)
    item_type = MessageItemType(payload.item_type)
    metadata: dict[str, object] = (
        {"idempotency_key": payload.idempotency_key} if payload.idempotency_key else {}
    )
    concept_id = payload.semantic_concept_id
    label = payload.display_label or payload.manual_text or ""

    if payload.recognition_session_id:
        session = db.scalar(
            select(RecognitionSession)
            .options(selectinload(RecognitionSession.corrections))
            .where(RecognitionSession.id == payload.recognition_session_id)
        )
        if session is None:
            raise ApiError("RECOGNITION_NOT_FOUND", "Reconnaissance introuvable.", 404)
        if session.user_id and (current_user is None or current_user.id != session.user_id):
            raise ApiError("FORBIDDEN", "Reconnaissance inaccessible.", 403)
        correction = db.scalar(
            select(UserCorrection)
            .where(
                UserCorrection.recognition_session_id == session.id,
                UserCorrection.selected_sign_id.is_not(None),
            )
            .order_by(UserCorrection.created_at.desc())
        )
        if correction is None or correction.selected_sign_id is None:
            raise ApiError(
                "RECOGNITION_NOT_CONFIRMED", "Confirmez le signe avant de l'ajouter.", 422
            )
        sign_id = correction.selected_sign_id
        source = (
            MessageItemSource.RECOGNITION_TOP_1
            if correction.correction_type.value == "CONFIRMED_TOP_1"
            else MessageItemSource.USER_CORRECTION
        )
        metadata["recognition_confirmed_at"] = correction.created_at.isoformat()

    if item_type == MessageItemType.CONFIRMED_SIGN:
        if not sign_id:
            raise ApiError("SIGN_REQUIRED", "Un signe est requis pour cet item.", 422)
        sign = db.get(Sign, sign_id)
        if sign is None or not sign.is_active:
            raise ApiError("SIGN_NOT_FOUND", "Signe introuvable ou inactif.", 404)
        concept = concept_for_sign(db, sign.id)
        concept_id = concept.id
        label = label or sign.french_translation
    elif item_type == MessageItemType.MANUAL_WORD:
        source = MessageItemSource.MANUAL_INPUT
        if not label:
            raise ApiError("MANUAL_TEXT_REQUIRED", "Texte manuel requis.", 422)
    elif item_type == MessageItemType.PUNCTUATION:
        source = MessageItemSource.MANUAL_INPUT
        label = label or "."

    position = max((item.position for item in message.items), default=0) + 1
    item = MessageItem(
        message_id=message.id,
        position=position,
        item_type=item_type,
        sign_id=sign_id,
        semantic_concept_id=concept_id,
        recognition_session_id=payload.recognition_session_id,
        source=source,
        display_label=label,
        metadata_json=metadata,
    )
    db.add(item)
    db.flush()
    message.raw_semantic_sequence = cast(list[object], semantic_sequence(db, message))
    message.status = MessageStatus.DRAFT
    add_revision(
        db,
        message,
        MessageRevisionChangeType.ITEM_ADDED,
        before,
        current_user.id if current_user else None,
        payload.idempotency_key,
    )
    db.commit()
    return message_response(db, message)


def semantic_sequence(db: Session, message: Message) -> list[str]:
    codes: list[str] = []
    for item in sorted(message.items, key=lambda entry: entry.position):
        if item.semantic_concept_id:
            concept = db.get(SemanticConcept, item.semantic_concept_id)
            if concept and concept.is_active:
                codes.append(concept.code)
    return codes


@router.patch("/{message_id}/items/{item_id}", response_model=MessageResponse)
def update_item(
    message_id: str,
    item_id: str,
    payload: UpdateMessageItemRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    item = next((entry for entry in message.items if entry.id == item_id), None)
    if item is None:
        raise ApiError("ITEM_NOT_FOUND", "Element introuvable.", 404)
    before = snapshot(message)
    if payload.display_label is not None:
        item.display_label = payload.display_label
    if payload.sign_id is not None:
        sign = db.get(Sign, payload.sign_id)
        if sign is None:
            raise ApiError("SIGN_NOT_FOUND", "Signe introuvable.", 404)
        item.sign_id = sign.id
        item.semantic_concept_id = concept_for_sign(db, sign.id).id
        item.source = MessageItemSource.USER_CORRECTION
    if payload.semantic_concept_id is not None:
        concept = db.get(SemanticConcept, payload.semantic_concept_id)
        if concept is None or not concept.is_active:
            raise ApiError("CONCEPT_NOT_FOUND", "Concept introuvable.", 404)
        item.semantic_concept_id = concept.id
    message.raw_semantic_sequence = cast(list[object], semantic_sequence(db, message))
    add_revision(
        db,
        message,
        MessageRevisionChangeType.ITEM_REPLACED,
        before,
        current_user.id if current_user else None,
    )
    db.commit()
    return message_response(db, message)


@router.delete("/{message_id}/items/{item_id}", response_model=MessageResponse)
def delete_item(
    message_id: str,
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    item = next((entry for entry in message.items if entry.id == item_id), None)
    if item is None:
        raise ApiError("ITEM_NOT_FOUND", "Element introuvable.", 404)
    before = snapshot(message)
    db.delete(item)
    db.flush()
    for index, remaining in enumerate(
        sorted(message.items, key=lambda entry: entry.position), start=1
    ):
        remaining.position = index
    message.raw_semantic_sequence = cast(list[object], semantic_sequence(db, message))
    add_revision(
        db,
        message,
        MessageRevisionChangeType.ITEM_REMOVED,
        before,
        current_user.id if current_user else None,
    )
    db.commit()
    return message_response(db, message)


@router.post("/{message_id}/items/reorder", response_model=MessageResponse)
def reorder_items(
    message_id: str,
    payload: ReorderMessageItemsRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    by_id = {item.id: item for item in message.items}
    if set(payload.item_ids) != set(by_id):
        raise ApiError("INVALID_ORDER", "La liste des elements est incomplete.", 422)
    before = snapshot(message)
    for index, item_id in enumerate(payload.item_ids, start=1):
        by_id[item_id].position = -index
    db.flush()
    for index, item_id in enumerate(payload.item_ids, start=1):
        by_id[item_id].position = index
    message.raw_semantic_sequence = cast(list[object], semantic_sequence(db, message))
    add_revision(
        db,
        message,
        MessageRevisionChangeType.ITEM_MOVED,
        before,
        current_user.id if current_user else None,
        payload.idempotency_key,
    )
    db.commit()
    return message_response(db, message)


@router.post("/{message_id}/generate", response_model=GenerationResponse)
def generate_message(
    message_id: str,
    payload: GenerateMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> GenerationResponse:
    if payload.generation_mode != "controlled":
        raise ApiError(
            "GENERATION_MODE_UNSUPPORTED", "Seule la generation controlee est active.", 422
        )
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    before = snapshot(message)
    concepts = [
        db.get(SemanticConcept, item.semantic_concept_id)
        for item in sorted(message.items, key=lambda entry: entry.position)
        if item.semantic_concept_id
    ]
    active_concepts = [concept for concept in concepts if concept is not None and concept.is_active]
    engine = LinguisticEngine()
    result = engine.generate(
        db,
        active_concepts,
        GenerationInput(
            concept_codes=[concept.code for concept in active_concepts],
            target_languages=payload.target_languages,
            politeness=payload.politeness,
            latin_variant=payload.latin_variant,
        ),
    )
    generated = result["result"]
    assert isinstance(generated, dict)
    message.generated_darija_arabic = str(generated.get("darija_arabic") or "")
    message.generated_darija_latin = str(generated.get("darija_latin") or "")
    message.generated_french = str(generated.get("french") or "")
    message.generated_english = str(generated.get("english") or "")
    raw_sequence = result["semantic_sequence"]
    message.raw_semantic_sequence = (
        cast(list[object], raw_sequence) if isinstance(raw_sequence, list) else []
    )
    message.generation_version = str(result["generation_version"])
    message.generation_strategy = str(result["strategy"])
    message.generation_metadata = {
        "template": result["template"],
        "linguistic_status": result["linguistic_status"],
        "warnings": result["warnings"],
        "system_insertions": result["system_insertions"],
        "dictionary_version": result["dictionary_version"],
        "template_version": result["template_version"],
        "alternatives": result.get("alternatives", []),
    }
    if not message.final_darija_arabic:
        message.final_darija_arabic = message.generated_darija_arabic
    if not message.final_darija_latin:
        message.final_darija_latin = message.generated_darija_latin
    if not message.final_french:
        message.final_french = message.generated_french
    if not message.final_english:
        message.final_english = message.generated_english
    message.status = MessageStatus.READY
    add_revision(
        db,
        message,
        MessageRevisionChangeType.GENERATED,
        before,
        current_user.id if current_user else None,
        payload.idempotency_key,
    )
    db.commit()
    return GenerationResponse(message_id=message.id, **result)


@router.get("/{message_id}/generation", response_model=GenerationResponse)
def get_generation(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> GenerationResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    return GenerationResponse(
        message_id=message.id,
        generation_version=message.generation_version,
        strategy=message.generation_strategy,
        semantic_sequence=[str(item) for item in message.raw_semantic_sequence],
        result={
            "darija_arabic": message.generated_darija_arabic or "",
            "darija_latin": message.generated_darija_latin or "",
            "french": message.generated_french or "",
            "english": message.generated_english or "",
        },
        template=str(message.generation_metadata.get("template") or "") or None,
        linguistic_status=str(message.generation_metadata.get("linguistic_status") or "LOW"),
        system_insertions=list_of_strings(
            message.generation_metadata.get("system_insertions", [])
        ),
        warnings=list_of_strings(message.generation_metadata.get("warnings", [])),
        alternatives=list_of_dicts(message.generation_metadata.get("alternatives", [])),
    )


@router.post("/{message_id}/regenerate", response_model=GenerationResponse)
def regenerate_message(
    message_id: str,
    payload: GenerateMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> GenerationResponse:
    return generate_message(message_id, payload, db, current_user, x_anonymous_session_id)


@router.post("/{message_id}/finalize", response_model=MessageResponse)
def finalize_message(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    if not (message.final_darija_arabic or message.generated_darija_arabic):
        raise ApiError("EMPTY_MESSAGE", "Le message est vide.", 422)
    before = snapshot(message)
    message.status = MessageStatus.COMPLETED
    message.completed_at = datetime.now(UTC)
    add_revision(
        db,
        message,
        MessageRevisionChangeType.FINALIZED,
        before,
        current_user.id if current_user else None,
    )
    db.commit()
    return message_response(db, message)


@router.get("/{message_id}/revisions", response_model=list[MessageRevisionResponse])
def list_revisions(
    message_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> list[MessageRevisionResponse]:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    return [
        MessageRevisionResponse(
            id=revision.id,
            revision_number=revision.revision_number,
            change_type=revision.change_type.value,
            before_snapshot=revision.before_snapshot,
            after_snapshot=revision.after_snapshot,
            created_at=revision.created_at,
        )
        for revision in message.revisions
    ]


@router.post("/{message_id}/revisions/{revision_id}/restore", response_model=MessageResponse)
def restore_revision(
    message_id: str,
    revision_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> MessageResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id, write=True)
    revision = next((item for item in message.revisions if item.id == revision_id), None)
    if revision is None:
        raise ApiError("REVISION_NOT_FOUND", "Revision introuvable.", 404)
    before = snapshot(message)
    after = revision.after_snapshot
    message.status = MessageStatus(str(after.get("status", message.status.value)))
    restored_sequence = after.get("sequence", message.raw_semantic_sequence)
    message.raw_semantic_sequence = (
        cast(list[object], restored_sequence) if isinstance(restored_sequence, list) else []
    )
    message.final_darija_arabic = str(after.get("final_darija_arabic") or "") or None
    add_revision(
        db,
        message,
        MessageRevisionChangeType.RESTORED,
        before,
        current_user.id if current_user else None,
    )
    db.commit()
    return message_response(db, message)


@router.post("/{message_id}/speech/prepare", response_model=SpeechPrepareResponse)
def prepare_speech(
    message_id: str,
    payload: SpeechPrepareRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    x_anonymous_session_id: Annotated[str | None, Header(alias="X-Anonymous-Session-Id")] = None,
) -> SpeechPrepareResponse:
    message = load_message(db, message_id)
    assert_message_access(message, current_user, x_anonymous_session_id)
    text = message.final_darija_arabic or message.generated_darija_arabic or ""
    return SpeechPrepareResponse(
        status="not_implemented",
        message="La synthese vocale sera integree dans une phase ulterieure.",
        contract={
            "message_id": message.id,
            "text": text,
            "language": payload.language,
            "voice": payload.voice,
            "speed": payload.speed,
        },
    )
