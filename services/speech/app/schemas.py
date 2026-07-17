from pydantic import BaseModel, Field


class SpeechPrepareRequest(BaseModel):
    message_id: str
    text: str
    language: str = "ary-MA"
    voice: str = "default"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class SpeechPrepareResponse(BaseModel):
    status: str
    message: str
    contract: dict[str, object]
