PYTHON ?= python3

.PHONY: install ml-install dev up down logs logs-api logs-inference logs-speech \
	test test-all test-backend test-inference test-ml speech-test test-frontend test-e2e \
	test-architecture lint format ml-dataset-scan ml-dataset-audit ml-preprocess-mosl \
	ml-validate-mosl-artifacts ml-train-v1 ml-validate-model benchmark-inference \
	benchmark-speech compose-check

install:
	cd apps/web && npm install
	cd services/api && $(PYTHON) -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
	cd services/inference && $(PYTHON) -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
	cd services/speech && $(PYTHON) -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"

ml-install:
	$(PYTHON) -m venv ml/.venv
	ml/.venv/bin/python -m pip install -r ml/requirements-train.txt

dev:
	docker compose up --build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-inference:
	docker compose logs -f inference

logs-speech:
	docker compose logs -f speech

test:
	$(MAKE) test-architecture
	$(MAKE) test-backend
	$(MAKE) test-inference
	$(MAKE) test-ml
	$(MAKE) speech-test
	$(MAKE) test-frontend

test-all: test
	$(MAKE) test-e2e

test-backend:
	cd services/api && .venv/bin/python -m pytest
	cd services/api && .venv/bin/python -m ruff check app tests
	cd services/api && .venv/bin/python -m mypy app

test-inference:
	cd services/inference && .venv/bin/python -m pytest
	cd services/inference && .venv/bin/python -m ruff check app tests
	cd services/inference && .venv/bin/python -m mypy app

test-ml:
	ml/.venv/bin/python -m pytest ml/tests
	ml/.venv/bin/python -m ruff check ml

speech-test:
	cd services/speech && .venv/bin/python -m pytest
	cd services/speech && .venv/bin/python -m ruff check app tests
	cd services/speech && .venv/bin/python -m mypy app

test-frontend:
	cd apps/web && npm test -- --run
	cd apps/web && npm run lint
	cd apps/web && npm run build

test-e2e:
	cd apps/web && npm run test:e2e

test-architecture:
	services/api/.venv/bin/python -m pytest tests/test_architecture_contracts.py

lint:
	cd apps/web && npm run lint
	cd services/api && .venv/bin/python -m ruff check app tests && .venv/bin/python -m mypy app
	cd services/inference && .venv/bin/python -m ruff check app tests && .venv/bin/python -m mypy app
	cd services/speech && .venv/bin/python -m ruff check app tests && .venv/bin/python -m mypy app
	ml/.venv/bin/python -m ruff check ml

format:
	cd apps/web && npm run format
	cd services/api && .venv/bin/python -m ruff format app tests
	cd services/inference && .venv/bin/python -m ruff format app tests
	cd services/speech && .venv/bin/python -m ruff format app tests
	ml/.venv/bin/python -m ruff format ml

ml-dataset-scan:
	services/inference/.venv/bin/python -m ml.datasets.mosl_video.scan

ml-dataset-audit:
	ml/.venv/bin/python -m ml.datasets.mosl_video.local_audit

ml-preprocess-mosl:
	services/inference/.venv/bin/python -m ml.datasets.mosl_video.preprocess

ml-validate-mosl-artifacts:
	services/inference/.venv/bin/python -m ml.datasets.mosl_video.validate_processed_artifacts

ml-train-v1:
	ml/.venv/bin/python -m ml.training.train_mosl_v1

ml-validate-model:
	ml/.venv/bin/python -m ml.export.validate_mosl_v1

benchmark-inference:
	ml/.venv/bin/python scripts/benchmark_inference.py

benchmark-speech:
	$(PYTHON) scripts/benchmark_speech.py

compose-check:
	docker compose config >/dev/null
	docker compose --profile ml config >/dev/null
