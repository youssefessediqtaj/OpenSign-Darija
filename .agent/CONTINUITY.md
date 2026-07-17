# OpenSign Darija Continuity

## [PLANS]
- 2026-07-16T15:30Z [USER] Initialize OpenSign Darija phase 1 as a professional monorepo with React/Vite frontend, FastAPI API, FastAPI inference mock service, PostgreSQL, Redis, MinIO, Docker, tests, docs, and CI.
- 2026-07-16T16:32Z [USER] Phase 2 requires real browser camera capture, MediaPipe Holistic landmark extraction, local normalization, backend landmark-only recognition, simulated inference, tests, performance measurement, and documentation.
- 2026-07-16T20:47Z [USER] Phase 3 requires Moroccan dataset collection workflow: separate consent management, contributor profiles, campaigns, uploads to object storage, linguistic/ML review gates, admin dataset version/export tools, docs, tests, and Docker verification.
- 2026-07-16T23:07Z [USER] Phase 4 requires first real recognition-model infrastructure: training/evaluation/export/registry pipeline, signer-independent guards, unknown/calibration logic, ONNX inference integration, admin model activation, frontend uncertainty states, and honest blocking when the dataset is invalid.
- 2026-07-17T02:58Z [USER] Phase 5 requires a controlled Darija message builder from confirmed signs/manual items with semantic concepts, deterministic linguistic generation, editing, history/favorites, speech mock contract, docs, automated tests, Docker/browser/log verification, and no untraceable hallucinated content.
- 2026-07-17T16:43Z [USER] Phase 6 requires Darija speech synthesis architecture, browser playback controls, secure MinIO audio cache, signed URLs, retention cleanup, browser fallback, tests, Docker/browser/log verification, and honest limits.

## [DECISIONS]
- 2026-07-16T15:30Z [ASSUMPTION] Current workspace is effectively empty; all project files will be created under `/Users/mac/Desktop/Project/OpenSigne-Darija` to avoid touching unrelated parent Git working tree changes.
- 2026-07-16T15:30Z [CODE] Inference and camera behavior are intentionally mocked for phase 1; frontend calls only the backend API, and the backend calls inference over HTTP.
- 2026-07-16T16:32Z [CODE] Phase 2 uses `@mediapipe/tasks-vision` HolisticLandmarker in the browser, keeps MediaPipe behind `holistic.service.ts`, and preserves the network boundary `Frontend -> Backend API -> Inference`.
- 2026-07-16T16:32Z [CODE] Recognition payloads contain compact torso-normalized landmarks only; backend stores recognition session metadata and predictions, not video, images, audio, canvas exports, or complete landmark sequences.
- 2026-07-16T20:47Z [CODE] Phase 3 stores dataset artifacts in MinIO buckets and persists only metadata/checksums/object keys in PostgreSQL; exports use anonymous contributor public IDs and split by contributor.
- 2026-07-16T20:47Z [CODE] Dataset contribution frontend is MVP synthetic-landmark capture; real camera MediaPipe extraction remains implemented in `/app/recognition` and is not yet wired into dataset capture.
- 2026-07-16T23:07Z [CODE] Phase 4 does not train or activate a real model because `artifacts/datasets/manifest.json` has zero items and training validation reports dataset status `UNCONFIRMED`; mock mode remains explicit development/test behavior only.
- 2026-07-16T23:07Z [CODE] Real inference mode must fail closed when no ONNX model is available; the API no longer silently falls back to mock outside explicit mock mode.
- 2026-07-17T02:58Z [CODE] Phase 5 uses a deterministic backend linguistic engine and seeded/demo linguistic data; it never calls an external LLM or third-party translation service.
- 2026-07-17T02:58Z [CODE] Guest messages are keyed by `X-Anonymous-Session-Id` and frontend localStorage stores only `opensign.guestSessionId`; backend TTL cleanup for guest messages is still UNCONFIRMED.
- 2026-07-17T02:58Z [CODE] Speech is an explicit mock service returning `not_implemented`; no fake audio is generated.
- 2026-07-17T16:43Z [CODE] Supersedes prior speech mock: phase 6 uses internal `services/speech` with provider abstraction, deterministic local experimental waveform provider `local-darija`, Arabic fallback voice, Darija normalization, WAV validation, and no external TTS API or voice cloning.
- 2026-07-17T16:43Z [CODE] Speech audio is stored in private MinIO bucket `opensign-speech-audio` under UUID object paths; PostgreSQL stores hashes/metadata/object keys, not full text or audio bytes; Redis currently has no persisted audio/cache keys in MVP.

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
- 2026-07-16T23:07Z [CODE] Added ML configs, dataset integrity/split validation, baseline and GRU/LSTM training scaffolds, evaluation/calibration/unknown detection, ONNX export/parity/registration scripts, ML tests, `MODEL_CARD.md`, and model lifecycle docs.
- 2026-07-16T23:07Z [CODE] Added inference ONNX loader/model metadata/readiness endpoints, API model registry/admin routes and recognition persistence metadata, frontend uncertainty/unknown/mock indicators, active model admin page, and model artifact storage bucket config.
- 2026-07-17T02:58Z [CODE] Added message/linguistic SQLAlchemy models, Alembic migration `20260717_0004`, message and linguistic API routers, controlled generation service modules, seed concepts/mappings/entries/templates, and message API tests.
- 2026-07-17T02:58Z [CODE] Added React message builder/history/favorites/detail routes, message feature components/hooks/services/store/types/tests, recognition-to-message actions, guest route access, and read-only linguistics admin page.
- 2026-07-17T02:58Z [CODE] Added `services/speech` mock FastAPI service, Docker Compose wiring, Makefile targets, and docs for message builder, semantic concepts, linguistic engine, Darija conventions, privacy/history, speech contract, and manual checks.
- 2026-07-17T02:58Z [CODE] Browser inspection found and fixed a finalize race: finalization now saves current final fields before `/finalize`, and generation no longer performs a delayed GET that can overwrite immediate manual edits.
- 2026-07-17T16:43Z [CODE] Added speech SQLAlchemy models/migration, seeded voices, API speech endpoints, speech client, MinIO byte upload/signed URL support, expired-audio cleanup job, Docker `speech-worker`, Make targets, frontend speech feature/player/fallback/admin page, and speech documentation/model card.
- 2026-07-17T16:43Z [CODE] Removed remaining disabled “Parler — bientôt disponible” UI in message toolbar/detail and replaced detail playback with the real `SpeechButton`.

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
- 2026-07-16T23:07Z [TOOL] Docker build initially hit PyPI read timeouts on API/inference dependencies; Dockerfiles now set longer pip timeout/retries.
- 2026-07-16T23:07Z [TOOL] Postgres migration `20260716_0003` initially failed because enum types were created twice; migration now reuses existing Postgres enum types and SQLAlchemy stores lowercase recognition/confidence enum values.
- 2026-07-17T02:58Z [TOOL] In-app Browser backend `iab` was unavailable (`agent.browsers.list()` returned `[]`), so manual browser inspection used local Playwright Chromium against Docker Nginx on `localhost:8081`.
- 2026-07-17T02:58Z [TOOL] Final Chromium inspection after fixes: `/api/v1/messages`, `/items`, `/generate`, `PATCH /messages/{id}`, `/finalize`, and history list all returned 200; console/page errors were empty; localStorage only contained `opensign.guestSessionId`.
- 2026-07-17T02:58Z [TOOL] Docker logs after final inspection show message-builder API/Nginx requests in 200 and no message bodies; older 422 finalize entries in the same log window were from pre-fix diagnostic runs.
- 2026-07-17T16:43Z [TOOL] Speech migration initially failed in Docker because PostgreSQL enum `speechgenerationstatus` was created twice; fixed migration to create the enum once and use `create_type=False` for the table column.
- 2026-07-17T16:43Z [TOOL] MinIO signed URL validation initially used HEAD and returned 403; GET range returned `206 Partial Content` with `Content-Type: audio/wav`, matching browser audio behavior.
- 2026-07-17T16:43Z [TOOL] Browser Playwright inspection showed console/page errors empty, speech API calls 200, audio GET range 206, signed audio URL without Darija text, and localStorage only `opensign.guestSessionId`.

## [OUTCOMES]
- 2026-07-16T15:50Z [TOOL] Verified: frontend lint/build/Vitest/Playwright pass; API pytest/Ruff/MyPy pass; inference pytest/Ruff/MyPy pass; local API endpoints for version, health, register, login, auth/me, signs, and mock recognition work.
- 2026-07-16T16:32Z [TOOL] Phase 2 verified: frontend `npm test -- --run`, `npm run lint`, `npm run build`, Playwright camera mocks, and `npm audit --audit-level=moderate` pass; API `pytest`, `ruff`, `mypy` pass; inference `pytest`, `ruff`, `mypy` pass; local API-to-inference landmark recognition flow returned enriched Top 3 and did not echo frames.
- 2026-07-16T16:48Z [TOOL] Docker Compose now builds/starts successfully; `docker compose ps` reports API/Postgres/Redis/inference healthy, Nginx on `0.0.0.0:8081`, and HTTP checks pass for `/`, `/api/v1/version`, and `/api/v1/health`.
- 2026-07-16T16:51Z [TOOL] Rebuilt/recreated Docker `web` and `nginx`; `POST http://localhost:8081/api/v1/recognitions/mock` returns 200, served JS bundle contains no `/api/api`, and `/api/v1/version` still returns API version.
- 2026-07-16T20:47Z [TOOL] Phase 3 verified: API pytest/Ruff/MyPy pass; inference pytest/Ruff/MyPy pass; frontend Vitest/lint/build pass; Playwright e2e pass; dataset Make targets pass; Docker Compose rebuild/start healthy; Nginx checks pass for `/`, `/api/v1/version`, `/api/v1/health`, `/api/v1/contribution-campaigns`, contributor login, `/auth/me`, and `/consents/templates`.
- 2026-07-16T23:07Z [TOOL] Phase 4 infrastructure verified: API `17 passed` plus Ruff/MyPy; inference `9 passed` plus Ruff/MyPy; frontend Vitest `18 passed`, lint, build, and Playwright `7 passed`; ML tests `5 passed`; Docker Compose healthy with Nginx on `8081`.
- 2026-07-16T23:07Z [TOOL] Runtime checks passed for `/api/v1/version`, `/api/v1/health`, `/api/v1/models/active`, `/api/v1/recognitions/mock`, persisted `/api/v1/recognitions`, inference `/health`, `/ready`, `/model`, and `/predict`; API mock benchmark via Nginx p50 `12.62 ms`, p95 `18.72 ms`, max `39.64 ms`.
- 2026-07-16T23:07Z [TOOL] `make dataset-validate-training` intentionally exits nonzero with errors: status `UNCONFIRMED`, zero examples, no eligible pilot classes; real training/evaluation metrics remain UNCONFIRMED.
- 2026-07-17T02:58Z [TOOL] Phase 5 verified: API `24 passed` plus Ruff/MyPy; inference `9 passed` plus Ruff/MyPy; frontend Vitest `21 passed`, lint, build, and Playwright `8 passed`; Docker Compose healthy with Nginx on `8081`.
- 2026-07-17T02:58Z [TOOL] Runtime checks passed for `/api/v1/health`, `/api/v1/linguistics/version`, `/api/v1/linguistics/concepts`, speech `/health` and `/prepare`, and full guest message flow create/add/generate/edit/finalize/history through Nginx.
- 2026-07-17T16:43Z [TOOL] Phase 6 verified: API full pytest `29 passed` plus Ruff/MyPy; speech pytest `4 passed` plus Ruff/MyPy; inference pytest/Ruff/MyPy pass; frontend speech Vitest `2 passed`, lint, and build pass; Docker Compose healthy with API/Postgres/Redis/MinIO/inference/speech/speech-worker/web/Nginx.
- 2026-07-17T16:43Z [TOOL] Runtime speech flow through Nginx generated WAV audio for finalized guest message, uploaded to MinIO, returned signed URL, replayed in Chromium via `<audio>`, and cache hit worked on repeated generation; 20-call benchmark mean `123.78 ms`, median `78.5 ms`, p95 `303.77 ms`.
