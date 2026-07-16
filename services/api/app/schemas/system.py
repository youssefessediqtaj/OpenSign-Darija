from pydantic import BaseModel


class VersionResponse(BaseModel):
    service: str
    version: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: dict[str, str]
