# OpenSign Darija Continuity

## [PLANS]
- 2026-07-16T15:30Z [USER] Initialize OpenSign Darija phase 1 as a professional monorepo with React/Vite frontend, FastAPI API, FastAPI inference mock service, PostgreSQL, Redis, MinIO, Docker, tests, docs, and CI.

## [DECISIONS]
- 2026-07-16T15:30Z [ASSUMPTION] Current workspace is effectively empty; all project files will be created under `/Users/mac/Desktop/Project/OpenSigne-Darija` to avoid touching unrelated parent Git working tree changes.
- 2026-07-16T15:30Z [CODE] Inference and camera behavior are intentionally mocked for phase 1; frontend calls only the backend API, and the backend calls inference over HTTP.

## [PROGRESS]
- 2026-07-16T15:30Z [TOOL] Created required monorepo directory structure for apps, services, packages, ML, infrastructure, docs, and CI.
- 2026-07-16T15:50Z [CODE] Implemented React/Vite frontend, FastAPI API, FastAPI inference mock service, Docker Compose/Nginx infra, Alembic schema, seed data, tests, docs, CI, and open-source governance files.

## [DISCOVERIES]
- 2026-07-16T15:30Z [TOOL] `git status` from the workspace reports many changes in parent directories; these are unrelated to this project and must be ignored.
- 2026-07-16T15:50Z [TOOL] Docker daemon is not running in the environment, so `docker compose up --build -d` could not be executed; `docker compose config` succeeded.
- 2026-07-16T15:50Z [TOOL] Local API health is `degraded` without Redis outside Docker; database and inference dependencies were healthy in local endpoint verification.
- 2026-07-16T15:50Z [TOOL] npm audit initially flagged Vite/esbuild dev dependency vulnerabilities; upgraded Vite to 8.1.5, Vitest to 4.1.10, and @vitejs/plugin-react to 6.0.3, after which `npm audit --audit-level=moderate` found 0 vulnerabilities.

## [OUTCOMES]
- 2026-07-16T15:50Z [TOOL] Verified: frontend lint/build/Vitest/Playwright pass; API pytest/Ruff/MyPy pass; inference pytest/Ruff/MyPy pass; local API endpoints for version, health, register, login, auth/me, signs, and mock recognition work.
