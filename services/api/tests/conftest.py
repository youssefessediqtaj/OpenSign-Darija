import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_opensign.sqlite3"
os.environ["REDIS_URL"] = "redis://localhost:6399/0"
os.environ["INFERENCE_SERVICE_URL"] = "http://localhost:8999"

from app.db.base import Base  # noqa: E402
from app.db.seed import seed  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
