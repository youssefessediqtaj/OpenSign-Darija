PYTHON ?= python3

.PHONY: help install ml-install dev up down logs logs-api logs-inference logs-speech \
	test test-all test-backend test-inference test-ml speech-test test-frontend test-e2e \
	test-architecture architecture-check lint format ml-dataset-scan ml-dataset-audit ml-preprocess-mosl \
	ml-validate-mosl-artifacts ml-train-v1 ml-validate-model benchmark-inference \
	benchmark-speech compose-check verify

help:
	@printf "%s\n" \
		"OpenSign Darija developer targets:" \
		"  make install                 Install web/API/inference/speech development dependencies." \
		"  make ml-install              Install offline ML development dependencies." \
		"  make dev                     Start Docker Compose with rebuild in the foreground." \
		"  make up                      Build and start the runtime stack in the background." \
		"  make down                    Stop the Docker Compose stack." \
		"  make logs                    Follow all Docker Compose logs." \
		"  make logs-api                Follow API logs." \
		"  make logs-inference          Follow inference logs." \
		"  make logs-speech             Follow speech logs." \
		"  make test                    Run architecture, backend, inference, ML, speech, and frontend tests." \
		"  make test-all                Run make test plus Playwright e2e." \
		"  make test-backend            Run API pytest, Ruff, and MyPy." \
		"  make test-inference          Run inference pytest, Ruff, and MyPy." \
		"  make test-ml                 Run offline ML pytest and Ruff." \
		"  make speech-test             Run speech pytest, Ruff, and MyPy." \
		"  make test-frontend           Run frontend unit tests, ESLint, and production build." \
		"  make test-e2e                Run Playwright browser tests." \
		"  make test-architecture       Run architecture and contract tests." \
		"  make architecture-check      Alias for make test-architecture." \
		"  make lint                    Run all lint/type checks." \
		"  make format                  Format code with repo tooling." \
		"  make ml-dataset-scan         Scan the local MoSL dataset manifest inputs." \
		"  make ml-dataset-audit        Audit the local MoSL dataset." \
		"  make ml-preprocess-mosl      Build protected MoSL landmark caches." \
		"  make ml-validate-mosl-artifacts Validate protected MoSL processed artifacts." \
		"  make ml-train-v1             Train the local V1 isolated-sign model." \
		"  make ml-validate-model       Validate the exported local V1 model package." \
		"  make benchmark-inference     Benchmark local inference behavior." \
		"  make benchmark-speech        Benchmark local speech behavior." \
		"  make compose-check           Validate normal and ML-profile Compose configs." \
		"  make verify                  Run complete non-destructive validation."

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
	services/api/.venv/bin/python -m pytest tests/architecture tests/contracts tests/privacy

architecture-check: test-architecture

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
	ml/.venv/bin/python scripts/benchmarking/benchmark_inference.py

benchmark-speech:
	$(PYTHON) scripts/benchmarking/benchmark_speech.py

compose-check:
	docker compose config >/dev/null
	docker compose --profile ml config >/dev/null

verify:
	$(MAKE) test-all
	$(MAKE) compose-check
