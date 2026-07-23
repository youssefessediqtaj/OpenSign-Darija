# Public API service

The stateless FastAPI service is the browser's only backend. Its active routes are
health/version, strict isolated-sign recognition, and supported-sign speech. It
has no authentication, SQLAlchemy, Alembic, database, Redis, MinIO, storage,
message, contribution, admin, model-registry, or background-job layer.

Ownership:

- `api/v1/`: thin public route adapters;
- `schemas/`: strict public and internal response models;
- `services/`: quality/UNKNOWN decisions, request protection, supported-label
  verification, and speech orchestration;
- `clients/`: typed inference and speech HTTP boundaries;
- `core/`: runtime configuration and safe error rendering.

Active routes:

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/version`
- `POST /api/v1/recognitions/word`
- `POST /api/v1/speech/sign`

Environment:

- `INFERENCE_SERVICE_URL`, `INFERENCE_TIMEOUT_SECONDS`: internal inference client.
- `SPEECH_SERVICE_URL`, `SPEECH_GENERATION_TIMEOUT_SECONDS`: internal speech client.
- `SUPPORTED_SIGNS_PATH`: optional supported-sign metadata override.
- `RECOGNITION_*`: payload, duration, rate, quality, and movement limits.

The API validates the closed 60 × 75 × 3 request before calling internal
inference. It converts unusable or rejected predictions to the compact UNKNOWN
shape. Speech accepts only a key verified against the checksum-protected active
model package; arbitrary browser text is never proxied.

`requirements.lock` pins the tested production-container resolution; local
development tools remain in the `dev` optional dependency group.

From the repository root, use `make test-backend`.
