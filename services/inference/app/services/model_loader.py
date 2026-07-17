from __future__ import annotations

from app.core.config import get_settings
from app.models.onnx_model import OnnxModel


class ModelLoader:
    def __init__(self) -> None:
        self.model: OnnxModel | None = None
        self.state = "STARTING"
        self.error: str | None = None
        self.reload()

    def reload(self) -> None:
        settings = get_settings()
        if settings.inference_mode == "mock":
            self.state = "READY"
            self.error = None
            self.model = None
            return
        self.state = "MODEL_LOADING"
        try:
            self.model = OnnxModel()
            self.state = "READY"
            self.error = None
        except Exception as exc:
            self.model = None
            self.state = "MODEL_NOT_FOUND"
            self.error = str(exc)


model_loader = ModelLoader()
