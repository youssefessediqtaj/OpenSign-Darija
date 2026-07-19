# MoSL Native Integration Final Cleanup Report

Date: 2026-07-19

## Outcome

OpenSigne Darija now contains one application. The obsolete nested source project
`Multimodal-Moroccan-Sign-Language-Generation/` was deleted after native data,
checksum, preprocessing, model-package, dependency, automated test, Docker, and
route checks passed.

Physical-camera validation remains `UNCONFIRMED` as a manual QA follow-up. It is
not a source-folder deletion blocker because the camera workflow uses the native
OpenSigne frontend, API, and inference services.

## Final Results

- Nested folder deleted: yes
- Deleted path:
  `/Users/mac/Desktop/Project/OpenSigne-Darija/Multimodal-Moroccan-Sign-Language-Generation`
- Deleted files: 68,058
- Deleted bytes: 3,742,182,096
- Native dataset path: `ml/data/external/mosl-video-dataset/`
- Native video count: 2,216
- Matching checksum count: 2,216
- Missing video count: 0
- Unexpected video count: 0
- Checksum mismatch count: 0
- Active dependency count: 0
- Preprocessing result: 2,216 successful, 0 failed, 0 unreadable
- Processed artifact validation: passed
- Model package result: `artifacts/models/mosl-word-smoke-v1/` valid, smoke-only,
  not production-ready
- Backend result: 35 tests passed, Ruff passed, MyPy passed
- Inference result: 10 tests passed, Ruff passed, MyPy passed
- ML result: 23 tests passed
- Speech result: 4 tests passed, Ruff passed, MyPy passed
- Frontend result: 27 Vitest tests passed, ESLint passed, production build passed
  with the existing Vite chunk-size warning
- Playwright result: 9 tests passed
- Docker config result: `docker compose config` and `docker compose --profile ml config`
  passed
- Docker build result: `docker compose build` and
  `docker compose --profile ml build` passed
- Docker health result: API, inference, speech, PostgreSQL, Redis, and MinIO healthy;
  web available through Nginx on `http://localhost:8081`
- Word-route result: HTTP 200, schema `OPEN_SIGNE_LANDMARK_SCHEMA_V1`, 60 frames,
  75 landmarks, 3 coordinates, 3 mock predictions
- Alphabet-route result: HTTP 200, schema `1.0.0`, 63 features, 3 mock predictions

## Files Retained

- Native videos and data artifacts under `ml/data/external/mosl-video-dataset/`
- Native MediaPipe asset under `ml/assets/mediapipe/`
- Smoke model package under `artifacts/models/mosl-word-smoke-v1/`
- Audit, validation, and deletion reports under `artifacts/reports/`
- Application source under `apps/`, `services/`, `packages/`, `ml/`, `tests/`,
  `docs/`, and `infrastructure/`

## Archive Evidence

- Source inventory:
  `artifacts/reports/nested-mosl-source-inventory.json`
- Source inventory CSV:
  `artifacts/reports/nested-mosl-source-inventory.csv`
- Migration verification:
  `ml/data/external/mosl-video-dataset/reports/migration-verification.json`
- Runtime/test validation summary:
  `artifacts/reports/mosl-validation-summary.json`
- Final deletion verification:
  `artifacts/reports/nested-mosl-final-deletion-verification.json`

## Provenance Record

- Original repository name: `Multimodal-Moroccan-Sign-Language-Generation`
- Original GitHub repository:
  `https://github.com/abdouaittissghit/Multimodal-Moroccan-Sign-Language-Generation`
- Source commit SHA: `bfae9b378cdf6eaed7f2f20b16297b281e9f7eca`
- Source code license status: `UNCONFIRMED`
- Dataset license status: `UNCONFIRMED/RESTRICTED`
- Components migrated: MoSL video files, native manifests/splits/reports,
  preprocessing outputs, MediaPipe asset, and smoke-model artifacts
- Components reimplemented: scanning, label normalization, migration verification,
  landmark preprocessing/validation, training manifest generation, smoke training
  and export, API/inference/frontend route handling, and guarded model activation
- Components deliberately excluded: nested app runtime, nested Docker files,
  nested virtual environments, unlicensed source-code reuse, and non-native caches

## Remaining Limitations

- Physical-camera manual QA is still `UNCONFIRMED`.
- The MoSL word model is a development smoke model only and must not be presented
  as production recognition.
- Full production MoSL training, calibration, signer-independent evaluation, and
  promotion remain future work.
