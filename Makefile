.PHONY: install dev up down logs test lint format migrate seed clean

install:
	cd apps/web && npm install
	cd services/api && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd services/inference && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev:
	docker compose up postgres redis minio inference api web

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	cd apps/web && npm test -- --run
	cd services/api && pytest
	cd services/inference && pytest

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
	cd services/api && python -m app.db.seed

clean:
	rm -rf apps/web/dist apps/web/coverage services/api/.pytest_cache services/inference/.pytest_cache
