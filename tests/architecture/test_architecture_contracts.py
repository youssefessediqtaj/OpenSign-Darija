from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads(
    (ROOT / "packages/contracts/recognition-v1.schema.json").read_text(encoding="utf-8")
)
FIXTURE_PATH = ROOT / "tests/fixtures/recognition/word-recognition-v1-valid.json"
EXPECTED_REQUEST_FIELDS = set(CONTRACT["$defs"]["WordRecognitionRequest"]["required"])


def source_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and not any(part in {".venv", "node_modules", "dist", "__pycache__"} for part in path.parts)
    )


def python_imports(root: Path) -> list[tuple[Path, str]]:
    imports: list[tuple[Path, str]] = []
    for path in source_files(root, (".py",)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend((path, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append((path, node.module))
    return imports


def service_python(service: str) -> str:
    local = ROOT / "services" / service / ".venv" / "bin" / "python"
    return str(local) if local.is_file() else sys.executable


def assert_pydantic_contract(service: str, model_import: str, model_name: str) -> None:
    script = f"""
import copy
import json
from pathlib import Path
from pydantic import ValidationError
from {model_import} import {model_name}
fixture = json.loads(Path({str(FIXTURE_PATH)!r}).read_text(encoding='utf-8'))
expected = {sorted(EXPECTED_REQUEST_FIELDS)!r}
assert sorted({model_name}.model_fields) == expected
validated = {model_name}(**fixture)
assert len(validated.frames) == 60
assert all(len(frame.landmarks) == 75 for frame in validated.frames)
assert all(len(point) == 3 for frame in validated.frames for point in frame.landmarks)
for forbidden in ('raw_video', 'image', 'audio', 'canvas', 'screenshot', 'base64_camera', 'microphone_audio', 'anonymous_session_id'):
    candidate = copy.deepcopy(fixture)
    candidate[forbidden] = 'forbidden'
    try:
        {model_name}(**candidate)
    except ValidationError:
        pass
    else:
        raise AssertionError(forbidden)
"""
    result = subprocess.run(
        [service_python(service), "-c", script],
        cwd=ROOT / "services" / service,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_language_neutral_contract_and_shared_frontend_fixture_are_exact() -> None:
    request = CONTRACT["$defs"]["WordRecognitionRequest"]
    frame = CONTRACT["$defs"]["Frame"]
    landmark = CONTRACT["$defs"]["Landmark"]
    response = CONTRACT["$defs"]["PublicRecognitionResponse"]
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert request["additionalProperties"] is False
    assert request["properties"]["recognition_mode"]["const"] == "WORD_ISOLATED"
    assert request["properties"]["feature_schema_version"]["const"] == (
        "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
    )
    assert request["properties"]["frames"]["minItems"] == 60
    assert request["properties"]["frames"]["maxItems"] == 60
    assert frame["properties"]["landmarks"]["minItems"] == 75
    assert frame["properties"]["landmarks"]["maxItems"] == 75
    assert landmark["minItems"] == landmark["maxItems"] == 3
    assert len(response["oneOf"]) == 2
    assert set(fixture) == EXPECTED_REQUEST_FIELDS
    assert len(fixture["frames"]) == 60
    assert all(len(item["landmarks"]) == 75 for item in fixture["frames"])
    assert all(
        len(point) == 3
        and all(isinstance(value, int | float) and abs(value) <= 20 for value in point)
        for item in fixture["frames"]
        for point in item["landmarks"]
    )
    frontend_fixture = (
        ROOT
        / "apps/web/src/features/recognition/test-fixtures/word-recognition-v1-valid.json"
    )
    assert frontend_fixture.read_bytes() == FIXTURE_PATH.read_bytes()


def test_api_and_inference_pydantic_models_match_the_contract() -> None:
    assert_pydantic_contract(
        "api",
        "app.schemas.recognition",
        "WordLandmarkRecognitionRequest",
    )
    assert_pydantic_contract(
        "inference",
        "app.schemas.prediction",
        "WordLandmarkSequenceRequest",
    )


def test_typescript_builder_and_playwright_pin_privacy_and_shape() -> None:
    contract_types = (
        ROOT / "apps/web/src/features/recognition/domain/recognition-contract.ts"
    ).read_text(encoding="utf-8")
    builder = (
        ROOT / "apps/web/src/features/recognition/domain/build-recognition-payload.ts"
    ).read_text(encoding="utf-8")
    playwright = (ROOT / "apps/web/tests/e2e/recognition-camera.spec.ts").read_text(
        encoding="utf-8"
    )
    for literal in (
        "WORD_ISOLATED",
        "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "shoulder_centered_v1",
    ):
        assert literal in contract_types or literal in builder
        assert literal in playwright
    for value in ("60", "75", "3"):
        assert value in builder
        assert value in playwright
    assert "anonymous_session_id" not in contract_types
    assert "anonymous_session_id" not in builder
    for forbidden in (
        "video",
        "image",
        "audio",
        "anonymous_session_id",
        "base64",
    ):
        assert f"not.toHaveProperty('{forbidden}')" in playwright or (
            forbidden == "base64" and "not.toContain('base64')" in playwright
        )
    assert "Number.isFinite" in playwright


def test_forbidden_import_and_http_boundaries() -> None:
    web_sources = source_files(ROOT / "apps/web/src", (".ts", ".tsx"))
    web_text = "\n".join(path.read_text(encoding="utf-8") for path in web_sources)
    assert not re.search(r"https?://(?:inference|speech)(?::\d+)?", web_text)
    assert "services/api/" not in web_text
    assert "services/inference/" not in web_text
    assert "services/speech/" not in web_text
    assert "/predict/word" not in web_text
    assert "/synthesize" not in web_text

    for path, imported in python_imports(ROOT / "services/api/app"):
        assert imported.split(".", 1)[0] not in {
            "alembic",
            "argon2",
            "cv2",
            "jwt",
            "mediapipe",
            "minio",
            "onnxruntime",
            "psycopg",
            "redis",
            "sqlalchemy",
            "torch",
        }, (path, imported)
        assert not imported.startswith("ml."), (path, imported)

    for path, imported in python_imports(ROOT / "services/inference/app"):
        assert imported.split(".", 1)[0] not in {"cv2", "mediapipe", "torch"}, (
            path,
            imported,
        )
        assert not imported.startswith(("ml.", "app.api.v1", "app.speech")), (
            path,
            imported,
        )

    for path, imported in python_imports(ROOT / "services/speech/app"):
        assert not imported.startswith(("ml.", "app.api.v1", "app.inference")), (
            path,
            imported,
        )


def test_dependencies_and_docker_match_the_stateless_runtime() -> None:
    expected_runtime = {
        "api": {"fastapi", "httpx", "pydantic", "pydantic-settings", "uvicorn"},
        "inference": {
            "fastapi",
            "numpy",
            "onnxruntime",
            "pydantic",
            "pydantic-settings",
            "uvicorn",
        },
        "speech": {"fastapi", "pydantic", "pydantic-settings", "uvicorn"},
    }
    for service, expected in expected_runtime.items():
        pyproject = tomllib.loads(
            (ROOT / f"services/{service}/pyproject.toml").read_text(encoding="utf-8")
        )
        declared = {
            re.split(r"[<>=!~;\[]", item, maxsplit=1)[0].strip().lower()
            for item in pyproject["project"]["dependencies"]
        }
        assert declared == expected
        dockerfile = (ROOT / f"services/{service}/Dockerfile").read_text(
            encoding="utf-8"
        )
        assert "COPY pyproject.toml requirements.lock ./" in dockerfile
        assert "--constraint requirements.lock -e ." in dockerfile
        locked = {
            re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip().lower()
            for line in (
                ROOT / f"services/{service}/requirements.lock"
            ).read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        }
        assert expected <= locked

    inference_dockerfile = (ROOT / "services/inference/Dockerfile").read_text(
        encoding="utf-8"
    )
    api_dockerfile = (ROOT / "services/api/Dockerfile").read_text(encoding="utf-8")
    assert "apt-get" not in inference_dockerfile
    assert ".[dev]" not in inference_dockerfile
    assert ".[dev]" not in api_dockerfile
    assert "alembic" not in api_dockerfile
    assert "migrations" not in api_dockerfile

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert compose.count("\n    ports:") == 1
    assert 'profiles: ["ml"]' in compose
    assert "http://inference:8001" in compose
    assert "http://speech:8010" in compose


def test_public_routes_and_gateway_contract_remain_minimal() -> None:
    routes = (ROOT / "apps/web/src/app/routes.tsx").read_text(encoding="utf-8")
    assert "<Route index" in routes
    assert 'path="app/recognition"' in routes
    assert len(re.findall(r"<Route(?:\s|>)", routes)) == 3

    nginx = (ROOT / "infrastructure/nginx/default.conf").read_text(encoding="utf-8")
    assert "location /api/" in nginx
    assert "proxy_pass http://api:8000/api/" in nginx
    assert "inference" not in nginx
    assert "speech" not in nginx
    assert 'microphone=()' in nginx
