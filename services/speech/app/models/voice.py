from pydantic import BaseModel


class Voice(BaseModel):
    id: str
    provider: str
    voice_code: str
    display_name: str
    language: str
    locale: str
    gender_label: str | None = None
    description: str
    model_version: str
    license: str
    is_default: bool = False
    is_active: bool = True
    is_experimental: bool = True
    supports_speed: bool = True
