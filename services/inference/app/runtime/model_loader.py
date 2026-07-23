from __future__ import annotations

from app.core.config import get_settings
from app.model_package.onnx_model import OnnxModel


class ModelLoader:
    def __init__(self) -> None:
        self.model: OnnxModel | None = None
        self.state = "STARTING"
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        self.state = "MODEL_LOADING"
        try:
            self.model = OnnxModel()
            if get_settings().model_warmup_enabled:
                self.model.warmup()
            self.state = "READY"
            self.error = None
        except Exception as exc:
            self.model = None
            self.state = "MODEL_NOT_FOUND"
            self.error = str(exc)


model_loader = ModelLoader()
