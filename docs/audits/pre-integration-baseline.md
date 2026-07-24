# Pre-Integration Baseline

Date: 2026-07-19

Branch created before integration edits:

```text
feat/integrate-mosl-video-dataset
```

## Git Status Before Integration

```text
## feat/integrate-mosl-video-dataset
 M .agent/CONTINUITY.md
?? Multimodal-Moroccan-Sign-Language-Generation/
```

The modified continuity file and untracked source folder existed before integration code changes in this turn.

## Docker Status

`docker compose ps` returned no running project services:

```text
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
```

`docker compose config --quiet` passed with exit code 0.

## Baseline Test Results

Frontend unit and lint:

```text
make test-frontend
Vitest: 16 files passed, 25 tests passed.
ESLint: passed.
```

Frontend production build:

```text
cd apps/web && npm run build
TypeScript build: passed.
Vite build: passed.
Warning: generated JS chunk is larger than 500 kB after minification.
```

API through Makefile:

```text
make test-backend
Failed before running tests: /bin/sh: pytest: command not found
```

API through existing virtualenv:

```text
cd services/api && .venv/bin/pytest && .venv/bin/ruff check app tests && .venv/bin/mypy app
pytest: 33 passed, 15 warnings.
Ruff: passed.
MyPy: passed, 63 source files.
```

Inference service:

```text
make test-inference
pytest: 10 passed, 1 warning.
Ruff: passed.
MyPy: passed, 13 source files.
```

Speech service:

```text
make speech-test
pytest: 4 passed.
Ruff: passed.
MyPy: passed, 15 source files.
```

ML tests:

```text
make test-ml
pytest: 11 passed.
```

## Baseline Environment Notes

- `ffprobe` and `ffmpeg` are available at `/opt/homebrew/bin`.
- In `services/inference/.venv`, OpenCV reports version `5.0.0` and MediaPipe reports version `0.10.35`.
- PyTorch is not installed in `services/inference/.venv`; training/export commands that require PyTorch are expected to fail until optional ML dependencies are installed.

## Pre-Existing Issues

- `make test-backend` depends on a bare `pytest` executable and fails when the API virtualenv is not activated. The API test suite itself passes when run with `services/api/.venv/bin/pytest`.
- No Docker project services were running at baseline.
- Frontend production build emits the existing Vite chunk-size warning.
