PYTHON ?= python3

.PHONY: install dev up down logs logs-api logs-worker logs-storage test test-backend test-frontend test-dataset test-e2e test-browser lint format migrate seed seed-dataset dataset-build dataset-validate dataset-stats dataset-prepare cleanup-uploads clean

install:
	cd apps/web && npm install
	cd services/api && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd services/inference && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev:
	docker compose up postgres redis minio inference api web

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	@echo "No worker service is configured yet; cleanup jobs run through the API image."

logs-storage:
	docker compose logs -f minio

test:
	$(MAKE) test-frontend
	$(MAKE) test-backend
	cd services/inference && pytest

test-backend:
	cd services/api && pytest
	cd services/api && ruff check app tests
	cd services/api && mypy app

test-frontend:
	cd apps/web && npm test -- --run
	cd apps/web && npm run lint

test-dataset: test-backend

test-e2e:
	cd apps/web && npm run test:e2e

test-browser: test-e2e

lint:
	cd apps/web && npm run lint
	cd services/api && ruff check app tests && mypy app
	cd services/inference && ruff check app tests && mypy app

format:
	cd apps/web && npm run format
	cd services/api && ruff format app tests
	cd services/inference && ruff format app tests

migrate:
	cd services/api && alembic upgrade head

seed:
	cd services/api && .venv/bin/python -m app.db.seed

seed-dataset: seed

dataset-build:
	$(PYTHON) -m ml.datasets.build_manifest

dataset-validate:
	$(PYTHON) -m ml.datasets.validate_dataset

dataset-stats:
	$(PYTHON) -m ml.datasets.generate_statistics

dataset-prepare:
	$(PYTHON) -m ml.preprocessing.prepare_sequences

cleanup-uploads:
	docker compose exec -T api python -m app.jobs.cleanup_orphan_uploads

clean:
	rm -rf apps/web/dist apps/web/coverage services/api/.pytest_cache services/inference/.pytest_cache
