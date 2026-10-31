# Public API service

The FastAPI service is the browser's only backend. Its protected core remains
stateless: health/version, strict isolated-sign recognition, and supported-sign
speech. A separately flagged contribution module adds lazy SQLite/private-object
storage without becoming a core-health or startup dependency.

Ownership:

- `api/v1/`: thin public route adapters;
- `schemas/`: strict public and internal response models;
- `services/`: quality/UNKNOWN decisions, request protection, supported-label
  verification, and speech orchestration;
- `clients/`: typed inference and speech HTTP boundaries;
- `core/`: runtime configuration and safe error rendering;
- `storage/`: optional private contribution metadata/video adapters;
- `cli/`: local-only contribution review, retention, rights, and export commands.

Active routes:

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/version`
- `POST /api/v1/recognitions/word`
- `POST /api/v1/speech/sign`
- `GET /api/v1/contributions/status`
- `GET /api/v1/contributions/signs`
- `GET /api/v1/contributions/notice`
- `POST /api/v1/contributions`
- `GET /api/v1/contributions/{uuid}/receipt`

Environment:

- `INFERENCE_SERVICE_URL`, `INFERENCE_TIMEOUT_SECONDS`: internal inference client.
- `SPEECH_SERVICE_URL`, `SPEECH_GENERATION_TIMEOUT_SECONDS`: internal speech client.
- `SUPPORTED_SIGNS_PATH`: optional supported-sign metadata override.
- `RECOGNITION_*`: payload, duration, rate, quality, and movement limits.
- `CONTRIBUTION_*`, `DATA_*`, `CNDP_*`, `CONSENT_NOTICE_VERSION`: optional
  fail-closed configuration documented in
  [the contribution index](../../docs/contributions/README.md).

The API validates the closed 60 × 75 × 3 request before calling internal
inference. It converts unusable or rejected predictions to the compact UNKNOWN
shape. Speech accepts only a key verified against the checksum-protected active
model package; arbitrary browser text is never proxied.

Contribution readiness frames stay in-browser until explicit save. Uploaded WebM
stays in private quarantine and never reaches recognition, inference, speech, or
ML automatically.

`requirements.lock` pins the tested production-container resolution; local
development tools remain in the `dev` optional dependency group.

From the repository root, use `make test-backend`.
