from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SignSpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label_key: str = Field(min_length=1, max_length=240)


class SignSpeechAudioResponse(BaseModel):
    url: str
    mime_type: str
    duration_ms: int = Field(ge=0)
    file_size_bytes: int = Field(ge=0)


class SignSpeechResponse(BaseModel):
    generation_id: str
    status: Literal["completed"]
    label_key: str
    label_ar: str
    audio: SignSpeechAudioResponse
    fallback_used: bool = False
