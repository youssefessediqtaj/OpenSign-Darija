from pydantic import BaseModel, Field


class PredictMockRequest(BaseModel):
    frames_count: int = Field(default=0, ge=0, le=300)


class ModelInfo(BaseModel):
    name: str
    version: str


class PredictionItem(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)


class PredictionResponse(BaseModel):
    request_id: str
    model: ModelInfo
    status: str
    predictions: list[PredictionItem]
    unknown_probability: float = Field(ge=0, le=1)
    processing_time_ms: int = Field(ge=0)
