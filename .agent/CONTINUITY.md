# OpenSign Darija Continuity

## [PLANS]
- 2026-07-16T15:30Z [USER] Initialize OpenSign Darija phase 1 as a professional monorepo with React/Vite frontend, FastAPI API, FastAPI inference mock service, PostgreSQL, Redis, MinIO, Docker, tests, docs, and CI.
- 2026-07-16T16:32Z [USER] Phase 2 requires real browser camera capture, MediaPipe Holistic landmark extraction, local normalization, backend landmark-only recognition, simulated inference, tests, performance measurement, and documentation.
- 2026-07-16T20:47Z [USER] Phase 3 requires Moroccan dataset collection workflow: separate consent management, contributor profiles, campaigns, uploads to object storage, linguistic/ML review gates, admin dataset version/export tools, docs, tests, and Docker verification.

## [DECISIONS]
- 2026-07-16T15:30Z [ASSUMPTION] Current workspace is effectively empty; all project files will be created under `/Users/mac/Desktop/Project/OpenSigne-Darija` to avoid touching unrelated parent Git working tree changes.
- 2026-07-16T15:30Z [CODE] Inference and camera behavior are intentionally mocked for phase 1; frontend calls only the backend API, and the backend calls inference over HTTP.
- 2026-07-16T16:32Z [CODE] Phase 2 uses `@mediapipe/tasks-vision` HolisticLandmarker in the browser, keeps MediaPipe behind `holistic.service.ts`, and preserves the network boundary `Frontend -> Backend API -> Inference`.
- 2026-07-16T16:32Z [CODE] Recognition payloads contain compact torso-normalized landmarks only; backend stores recognition session metadata and predictions, not video, images, audio, canvas exports, or complete landmark sequences.
- 2026-07-16T20:47Z [CODE] Phase 3 stores dataset artifacts in MinIO buckets and persists only metadata/checksums/object keys in PostgreSQL; exports use anonymous contributor public IDs and split by contributor.
- 2026-07-16T20:47Z [CODE] Dataset contribution frontend is MVP synthetic-landmark capture; real camera MediaPipe extraction remains implemented in `/app/recognition` and is not yet wired into dataset capture.

## [PROGRESS]
- 2026-07-16T15:30Z [TOOL] Created required monorepo directory structure for apps, services, packages, ML, infrastructure, docs, and CI.
- 2026-07-16T15:50Z [CODE] Implemented React/Vite frontend, FastAPI API, FastAPI inference mock service, Docker Compose/Nginx infra, Alembic schema, seed data, tests, docs, CI, and open-source governance files.
- 2026-07-16T16:32Z [CODE] Implemented real camera recognition workspace under `apps/web/src/features/recognition`, `/app/recognition`, `/app/settings`, landmark schema config, backend `POST /api/v1/recognitions`, confirmation/correction endpoints, and inference `POST /predict`.
- 2026-07-16T16:32Z [CODE] Added phase 2 docs for camera, MediaPipe, landmark schema, recognition flow, privacy, performance, and camera testing; README/API/architecture docs updated.
- 2026-07-16T16:48Z [CODE] Made Docker Nginx host port configurable via `NGINX_HOST_PORT`, defaulting to `8081`, and updated README/docker docs to avoid a local Docker Desktop conflict on `8080`.
- 2026-07-16T16:51Z [CODE] Fixed Docker frontend API base URL by building with empty `VITE_API_BASE_URL`; frontend service paths already include `/api/v1`, so this prevents `/api/api/v1/...` requests through Nginx.
- 2026-07-16T20:47Z [CODE] Added dataset SQLAlchemy models, Alembic migration `20260716_0002`, consent/contributor/campaign/contribution/review/admin dataset routers, MinIO storage helper, cleanup job, seed data, API tests, and route docs.
- 2026-07-16T20:47Z [CODE] Added contribution/review/admin frontend pages, auth token injection, seeded user role loading on login, dataset API client, consent unit test, and Playwright consent smoke test.
- 2026-07-16T20:47Z [CODE] Added ML dataset scripts (`build_manifest`, `validate_dataset`, `prepare_sequences`, `generate_statistics`), Makefile targets, dataset docs, and `DATASET_CARD.md`.

## [DISCOVERIES]
- 2026-07-16T15:30Z [TOOL] `git status` from the workspace reports many changes in parent directories; these are unrelated to this project and must be ignored.
- 2026-07-16T15:50Z [TOOL] Docker daemon is not running in the environment, so `docker compose up --build -d` could not be executed; `docker compose config` succeeded.
- 2026-07-16T15:50Z [TOOL] Local API health is `degraded` without Redis outside Docker; database and inference dependencies were healthy in local endpoint verification.
- 2026-07-16T15:50Z [TOOL] npm audit initially flagged Vite/esbuild dev dependency vulnerabilities; upgraded Vite to 8.1.5, Vitest to 4.1.10, and @vitejs/plugin-react to 6.0.3, after which `npm audit --audit-level=moderate` found 0 vulnerabilities.
- 2026-07-16T16:32Z [TOOL] Docker daemon remains unavailable; `docker compose config` passes but container startup/build verification is blocked by `Cannot connect to the Docker daemon`.
- 2026-07-16T16:32Z [TOOL] Synthetic recognition performance measurement: 30 target frames, 63 features per frame, JSON payload 21,351 bytes, synthetic build 1.427 ms; real MediaPipe FPS/load/latency remains UNCONFIRMED without device testing.
- 2026-07-16T16:32Z [TOOL] `apps/web/tsconfig.tsbuildinfo` is tracked and was updated by TypeScript build state; `.gitignore` now ignores future `*.tsbuildinfo`, but the tracked file still appears modified.
- 2026-07-16T16:48Z [TOOL] Docker daemon became available after launching Docker Desktop with `open -a Docker`; `8080` was occupied by a `com.docker` listener, so Compose failed until Nginx was moved to host port `8081`.
- 2026-07-16T20:47Z [TOOL] Host `python` is unavailable (`command not found`), so Makefile root dataset targets now default to `PYTHON ?= python3`; generated `artifacts/` are ignored.
- 2026-07-16T20:47Z [TOOL] Host Postgres on localhost did not match Docker credentials for cleanup dry-run; cleanup target now executes inside the API container and returned `matched: 0`.

## [OUTCOMES]
- 2026-07-16T15:50Z [TOOL] Verified: frontend lint/build/Vitest/Playwright pass; API pytest/Ruff/MyPy pass; inference pytest/Ruff/MyPy pass; local API endpoints for version, health, register, login, auth/me, signs, and mock recognition work.
- 2026-07-16T16:32Z [TOOL] Phase 2 verified: frontend `npm test -- --run`, `npm run lint`, `npm run build`, Playwright camera mocks, and `npm audit --audit-level=moderate` pass; API `pytest`, `ruff`, `mypy` pass; inference `pytest`, `ruff`, `mypy` pass; local API-to-inference landmark recognition flow returned enriched Top 3 and did not echo frames.
- 2026-07-16T16:48Z [TOOL] Docker Compose now builds/starts successfully; `docker compose ps` reports API/Postgres/Redis/inference healthy, Nginx on `0.0.0.0:8081`, and HTTP checks pass for `/`, `/api/v1/version`, and `/api/v1/health`.
- 2026-07-16T16:51Z [TOOL] Rebuilt/recreated Docker `web` and `nginx`; `POST http://localhost:8081/api/v1/recognitions/mock` returns 200, served JS bundle contains no `/api/api`, and `/api/v1/version` still returns API version.
- 2026-07-16T20:47Z [TOOL] Phase 3 verified: API pytest/Ruff/MyPy pass; inference pytest/Ruff/MyPy pass; frontend Vitest/lint/build pass; Playwright e2e pass; dataset Make targets pass; Docker Compose rebuild/start healthy; Nginx checks pass for `/`, `/api/v1/version`, `/api/v1/health`, `/api/v1/contribution-campaigns`, contributor login, `/auth/me`, and `/consents/templates`.
