from pydantic import BaseModel, Field


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = "ar-MA"
    voice_id: str = "darija-default"
    speed: float = Field(default=1.0, ge=0.75, le=1.5)
    output_format: str = "wav"
    number_reading: str = "natural"
