# Professional Project Structure Report

## Before

The branch started from `main` at `701e496`, after the previous architecture
refactor had already been merged. The tracked tree was clean. Baseline validation
passed:

- Architecture/contract: 6 passed.
- API: 54 passed; Ruff and MyPy passed.
- Inference: 29 passed; Ruff and MyPy passed.
- ML: 31 passed; Ruff passed.
- Speech: 9 passed; Ruff and MyPy passed.
- Frontend: 30 Vitest tests passed; ESLint and production build passed.
- Playwright default: 4 passed, 1 intentional Docker/Y4M skip.
- Compose config, Docker build, Docker up, and health checks passed.

Protected baseline:

- ONNX SHA-256: `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`.
- Dataset manifest SHA-256: `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`.
- Dataset records verified: 2,216.
- Canonical accepted label: `احب`.

Remaining structure problems at the start of this pass:

- Root `.pytest_cache/` and `.ruff_cache/` existed locally.
- `OpenSigne-Darija-readme/` existed locally but contained only `.DS_Store` files.
- Root `data/` still had a tracked README for obsolete external download paths plus
  ignored duplicate generated artifacts.
- Required project-structure docs and ADRs were incomplete.
- Makefile lacked `help`, `verify`, and `architecture-check` public targets.

## After

Final root responsibilities:

- `.agent/`: continuity notes.
- `.github/`: CI workflows.
- `apps/web/`: public React recognition app.
- `artifacts/`: ignored generated reports and protected model packages.
- `docs/`: architecture, audits, operations, and reports.
- `infrastructure/`: Nginx public gateway config.
- `ml/`: offline dataset, preprocessing, training, evaluation, export, validation.
- `packages/contracts/`: shared JSON contracts used by root contract tests.
- `scripts/`: reproducible audits, benchmarks, and protected-asset checks.
- `services/api/`: public stateless FastAPI API.
- `services/inference/`: internal ONNX inference service.
- `services/speech/`: internal local speech service.
- `tests/`: architecture and contract tests.

Root `data/` was removed. ML data remains under `ml/data/`; generated reports and
model packages remain under `artifacts/`; small deterministic fixtures remain with
tests.

## Files

Created:

- `scripts/audit_project_structure.py`
- `docs/audits/pre-professional-architecture-baseline.md`
- `docs/audits/root-folder-audit.md`
- `docs/operations/configuration-reference.md`
- `docs/architecture/repository-map.md`
- `docs/architecture/runtime-flow.md`
- `docs/architecture/dependency-rules.md`
- `docs/architecture/recognition-state-machine.md`
- `docs/architecture/model-package.md`
- `docs/architecture/privacy-security.md`
- `docs/architecture/testing-strategy.md`
- `docs/architecture/adr/0001-browser-mediapipe.md`
- `docs/architecture/adr/0002-public-stateless-api.md`
- `docs/architecture/adr/0003-internal-onnx-inference.md`
- `docs/architecture/adr/0004-local-dataset-only.md`
- `docs/architecture/adr/0005-automatic-isolated-sign-flow.md`

Updated:

- `.gitignore`
- `Makefile`
- service README files
- `ml/README.md`
- `scripts/audit_repository_architecture.py`
- `scripts/verify_architecture_protected_assets.py`
- `docs/architecture/dependency-graph.md`

Deleted:

- `data/README.md`
- local `.pytest_cache/`
- local `.ruff_cache/`
- local `OpenSigne-Darija-readme/`
- ignored local root `data/` artifacts
- source-tree `.DS_Store` files

## OpenSigne-Darija-readme

The duplicate folder contained only local `.DS_Store` files during this pass. The
authoritative README and images had already been migrated to native root/doc paths
in earlier work. No runtime, test, Docker, Makefile, CI, or documentation command
requires the duplicate folder. The folder was removed.

Machine-readable evidence: `artifacts/reports/readme-duplicate-cleanup.json`.

## Data Folders

Root `data/` decision: removed. Its MediaPipe task copy matched the protected
`ml/assets/mediapipe/holistic_landmarker.task` checksum exactly, and the tracked
README pointed to obsolete external download paths.

`ml/data/` decision: kept. It owns the protected local MoSL dataset, manifests,
splits, processed landmark caches, and dataset reports. The 2,216-video dataset
was not moved, regenerated, or modified.

## Dependencies

No broad dependency upgrades were performed. The previous refactor had already
removed unused database/auth/admin/storage/runtime dependencies and inference
MediaPipe/OpenCV runtime dependencies. This pass added audit evidence and kept the
current dependency shape:

- API production image: 187,122,948 bytes.
- Inference production image: 303,138,593 bytes.
- Speech production image: 224,545,232 bytes.
- Web production image: 83,811,768 bytes.

Machine-readable evidence: `artifacts/reports/dependency-audit.json`.

## Documentation

Service READMEs now identify responsibilities, active routes where relevant,
entry points, environment variables, testing commands, failure behavior, and
dependency boundaries. Architecture docs now cover repository map, runtime flow,
dependency rules, recognition state machine, model package, privacy/security, and
testing strategy. ADRs record browser MediaPipe, stateless API, internal ONNX
inference, local dataset only, and automatic isolated-sign flow decisions.

## Tests

Final automated results:

- `make verify`: passed.
- Architecture/contract: 6 passed.
- API: 54 passed; Ruff and MyPy passed.
- Inference: 29 passed; Ruff and MyPy passed.
- ML: 31 passed; Ruff passed.
- Speech: 9 passed; Ruff and MyPy passed.
- Frontend: 30 Vitest tests passed; ESLint and production build passed.
- Default Playwright: 4 passed, 1 intentional Docker/Y4M skip.
- Strict real-Docker Playwright with a generated local Y4M and
  `PLAYWRIGHT_EXPECT_TWO_SIGNS=1`: failed because only one real Docker recognition
  was produced within the 25-second polling window.
- Real-Docker Playwright with the same local Y4M and one-sign expectation:
  5 passed, including the non-intercepted real API privacy gate.
- `docker compose build`: passed.
- `docker compose up -d`: passed.
- `docker compose ps`: API, inference, and speech healthy; web and Nginx running.
- Docker log scan: no traceback, exception, fatal, or error lines in the inspected
  tail.

Active public API paths:

- `/health`
- `/api/v1/health`
- `/api/v1/version`
- `/api/v1/recognitions/word`
- `/api/v1/speech/sign`

## Behavior Preservation

Protected after-check: true.

- ONNX SHA-256 unchanged:
  `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`.
- Dataset manifest SHA-256 unchanged:
  `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`.
- 2,216 raw records verified.
- Canonical known decision unchanged: `احب`, accepted.
- MediaPipe protected asset unchanged.
- No raw video, image, canvas, microphone audio, base64 camera payload, direct
  inference request, or direct speech request is allowed by contracts/tests.

## Remaining Limitations

- Active vocabulary remains limited to the current protected package labels.
- Evaluation remains small and OOV false-acceptance risk remains documented.
- Signer diversity is limited by the local dataset metadata.
- Physical-camera validation remains `UNCONFIRMED`.
- The generated local Y4M proved one real Docker recognition, but did not produce
  a reliable two-sign reset in strict mode.
- Historical provenance docs remain intentionally retained.
