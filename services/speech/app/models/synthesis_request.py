from pydantic import BaseModel, Field


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = "ary-MA"
    voice_id: str = "darija-default"
    speed: float = Field(default=1.0, ge=0.75, le=1.5)
    output_format: str = "wav"
    number_reading: str = "natural"


class LegacySpeechPrepareRequest(BaseModel):
    message_id: str
    text: str
    language: str = "ary-MA"
    voice: str = "default"
    speed: float = Field(default=1.0, ge=0.75, le=1.5)
