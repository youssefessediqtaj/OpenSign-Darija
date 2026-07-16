from pydantic import BaseModel, Field


class RecognitionMockRequest(BaseModel):
    source: str = Field(default="demo", max_length=40)
    frames_count: int = Field(default=0, ge=0, le=300)


class PredictionResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)


class RecognitionResponse(BaseModel):
    request_id: str
    status: str
    model_name: str
    model_version: str
    predictions: list[PredictionResponse]
    unknown_probability: float = Field(ge=0, le=1)
    processing_time_ms: int = Field(ge=0)
