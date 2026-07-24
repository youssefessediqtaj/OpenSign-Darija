# Testing Strategy

Validation is split by ownership:

- `make test-architecture` checks cross-service boundaries, contract parity, privacy
  invariants, and repository-local documentation links under `tests/architecture/`,
  `tests/contracts/`, and `tests/privacy/`.
- `make test-backend` checks public API schemas, recognition decisions, speech
  orchestration, Ruff, and MyPy.
- `make test-inference` checks fail-closed package loading, ONNX shape validation,
  UNKNOWN calibration, Ruff, and MyPy.
- `make speech-test` checks local synthesis bounds, fallback behavior, WAV validity,
  Ruff, and MyPy.
- `make test-ml` checks offline dataset/model utilities without requiring CI to
  download the full protected dataset.
- `make test-frontend` checks domain algorithms, React flow, lint, and production
  build.
- `make test-e2e` checks anonymous browser flow with deterministic camera fixtures.
- `make verify` runs the complete non-destructive validation path.

Docker validation uses `make compose-check`, `docker compose build`,
`docker compose up -d`, and `docker compose ps`.
