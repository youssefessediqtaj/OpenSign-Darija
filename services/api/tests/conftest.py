import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["INFERENCE_SERVICE_URL"] = "http://127.0.0.1:8999"
os.environ["SPEECH_SERVICE_URL"] = "http://127.0.0.1:8998"

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_recognition_rate_limits() -> Iterator[None]:
    from app.services.request_protection import clear_rate_limit_state

    clear_rate_limit_state()
    yield
    clear_rate_limit_state()
