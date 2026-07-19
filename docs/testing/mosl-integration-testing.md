# MoSL Integration Testing

Date: 2026-07-19

## Data And ML Gates

- Source inventory: 68,058 nested files inventoried; 2,216 videos marked `MIGRATE`; 7 source components marked `REIMPLEMENT`.
- Migration verification: 2,216/2,216 checksums matched; zero missing/unexpected/mismatched files.
- Full preprocessing: 2,216/2,216 processed; zero failures; deterministic cache rerun hit 2,216 caches.
- Processed artifact validation: passed, 2,216 valid artifacts, 350 warnings.
- ML profile run: passed, generated a training manifest with 108 eligible labels and 372 eligible samples.
- Smoke package validation: passed for `artifacts/models/mosl-word-smoke-v1`.

## Automated Tests

- API: `35 passed`, Ruff passed, MyPy passed.
- Inference: `10 passed`, Ruff passed, MyPy passed.
- ML: `23 passed`, ML Ruff passed.
- Speech: `4 passed`, Ruff passed, MyPy passed.
- Frontend: `27 passed`, ESLint passed, build passed with the existing Vite chunk-size warning.
- Playwright: `9 passed`.

## Docker And Browser

- `docker compose config`: passed.
- `docker compose --profile ml config`: passed.
- `docker compose build`: passed.
- `docker compose --profile ml build`: passed.
- `docker compose up -d`: healthy through Nginx on `localhost:8081`.
- Docker runtime POST smoke:
  - `/api/v1/recognitions/word`: HTTP 200, schema `OPEN_SIGNE_LANDMARK_SCHEMA_V1`, Top-K 3.
  - `/api/v1/recognitions/alphabet`: HTTP 200, schema `1.0.0`, Top-K 3.
- Browser Chromium inspection against Docker with mocked camera: no console errors, page errors, failed requests or localStorage keys.

## Not Completed

Physical camera validation is `UNCONFIRMED`. This is the only remaining deletion gate blocker in `artifacts/reports/nested-mosl-final-deletion-verification.json`.
