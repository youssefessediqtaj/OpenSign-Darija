import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "postgresql+psycopg://unused:unused@127.0.0.1:1/unused"
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
os.environ["MINIO_ENDPOINT"] = "127.0.0.1:1"
os.environ["INFERENCE_SERVICE_URL"] = "http://127.0.0.1:8999"
os.environ["SPEECH_SERVICE_URL"] = "http://127.0.0.1:8998"

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_recognition_rate_limits() -> Iterator[None]:
    from app.api.v1.recognitions import rate_limit_bucket

    rate_limit_bucket.clear()
    yield
    rate_limit_bucket.clear()
