# Pre Professional Architecture Baseline

Captured on branch `refactor/professional-project-structure` before the
project-structure cleanup edits.

## Git Baseline

- `git status --short`: clean.
- `git branch --show-current`: `refactor/professional-project-structure`.
- `git diff --stat`: empty.
- `git diff`: empty.
- Latest base commit: `701e496 docs: record refactor branch deletion`.

## Test Baseline

- Architecture/contract tests: 6 passed.
- API tests: 54 passed; Ruff passed; MyPy passed.
- Inference tests: 29 passed; Ruff passed; MyPy passed.
- ML tests: 31 passed; Ruff passed.
- Speech tests: 9 passed; Ruff passed; MyPy passed.
- Frontend unit tests: 30 passed; ESLint passed; production build passed.
- Playwright: 4 passed, 1 intentionally skipped because the real Docker fake-camera
  gate requires explicit Docker/Y4M configuration.

## Docker Baseline

- `make compose-check`: passed for normal and ML-profile Compose configs.
- `docker compose build`: passed for API, inference, speech, and web.
- `docker compose up -d`: passed.
- `docker compose ps`: API, inference, and speech healthy; web and Nginx running;
  Nginx published on host port `8081`.
- API version through Nginx: `{"service":"opensign-api","version":"1.0.0"}`.
- API health through Nginx: inference and speech healthy.

## Protected Assets Baseline

- ONNX SHA-256: `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`.
- Dataset manifest SHA-256: `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`.
- Dataset records verified: 2,216.
- Canonical top label: `احب`.
- Canonical decision: accepted known sign.

Machine-readable baseline: `artifacts/reports/pre-professional-architecture-baseline.json`.
