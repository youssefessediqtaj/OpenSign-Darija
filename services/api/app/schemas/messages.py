from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConceptResponse(BaseModel):
    id: str
    code: str
    name_fr: str
    name_en: str
    concept_type: str
    is_active: bool


class LinguisticTemplateResponse(BaseModel):
    id: str
    code: str
    name_fr: str
    name_ar: str
    name_en: str
    category: str
    risk_level: str
    version: str
    is_active: bool


class CreateMessageRequest(BaseModel):
    anonymous_session_id: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=160)


class UpdateMessageRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    final_darija_arabic: str | None = None
    final_darija_latin: str | None = None
    final_french: str | None = None
    final_english: str | None = None


class AddMessageItemRequest(BaseModel):
    recognition_session_id: str | None = None
    sign_id: str | None = None
    semantic_concept_id: str | None = None
    item_type: str = "CONFIRMED_SIGN"
    source: str = "USER_CORRECTION"
    display_label: str | None = Field(default=None, max_length=240)
    manual_text: str | None = Field(default=None, max_length=240)
    idempotency_key: str | None = Field(default=None, max_length=120)


class UpdateMessageItemRequest(BaseModel):
    display_label: str | None = Field(default=None, max_length=240)
    semantic_concept_id: str | None = None
    sign_id: str | None = None


class ReorderMessageItemsRequest(BaseModel):
    item_ids: list[str]
    idempotency_key: str | None = Field(default=None, max_length=120)


class GenerateMessageRequest(BaseModel):
    generation_mode: str = "controlled"
    target_languages: list[str] = Field(
        default_factory=lambda: ["darija_arabic", "darija_latin", "french", "english"]
    )
    politeness: str = "neutral"
    latin_variant: str = "standard"
    idempotency_key: str | None = Field(default=None, max_length=120)


class MessageItemResponse(BaseModel):
    id: str
    position: int
    item_type: str
    sign_id: str | None
    semantic_concept_id: str | None
    semantic_concept_code: str | None = None
    recognition_session_id: str | None
    source: str
    display_label: str
    metadata: dict[str, Any]
    created_at: datetime


class GenerationResponse(BaseModel):
    message_id: str
    generation_version: str
    strategy: str
    semantic_sequence: list[str]
    result: dict[str, str]
    template: str | None
    linguistic_status: str
    system_insertions: list[str]
    warnings: list[str]
    alternatives: list[dict[str, str]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    id: str
    user_id: str | None
    anonymous_session_id: str | None
    status: str
    title: str | None
    raw_semantic_sequence: list[Any]
    generated_darija_arabic: str | None
    generated_darija_latin: str | None
    generated_french: str | None
    generated_english: str | None
    final_darija_arabic: str | None
    final_darija_latin: str | None
    final_french: str | None
    final_english: str | None
    generation_strategy: str
    generation_version: str
    generation_metadata: dict[str, Any]
    is_favorite: bool
    item_count: int
    risk_level: str
    items: list[MessageItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int


class MessageRevisionResponse(BaseModel):
    id: str
    revision_number: int
    change_type: str
    before_snapshot: dict[str, Any]
    after_snapshot: dict[str, Any]
    created_at: datetime


class SpeechPrepareRequest(BaseModel):
    language: str = "ary-MA"
    voice: str = "default"
    speed: float = 1.0


class SpeechPrepareResponse(BaseModel):
    status: str
    message: str
    contract: dict[str, Any]
