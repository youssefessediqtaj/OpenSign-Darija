# Pre-simplification test baseline

Captured on 2026-07-19 before application-code changes for the automatic core-recognition work.

## Source-control state

| Command | Result |
|---|---|
| `git status --short` | Clean; no entries |
| `git branch --show-current` | `main` |
| `git diff --stat` | Clean; no entries |

The pre-existing tree was therefore clean. The required continuity record was updated only after this snapshot; it is workspace briefing metadata, not an application-code baseline change.

## Required test commands

| Command | Baseline result |
|---|---|
| `make test-backend` | PASS — 50 tests; Ruff pass; MyPy pass. Pytest reported 17 existing warnings (Starlette/httpx deprecation, short development JWT key, and Alembic path-separator deprecation). |
| `make test-inference` | PASS — 10 tests; Ruff pass; MyPy pass. One existing Starlette/httpx deprecation warning. |
| `make test-ml` | PASS — 23 tests. This target did not run ML Ruff/MyPy. |
| `make speech-test` | PASS — 4 tests; Ruff pass; MyPy pass. |
| `npm test -- --run` | PASS — 18 files, 35 tests. |
| `npm run lint` | PASS when run alone. An initial parallel baseline run raced Playwright's deletion/creation of `test-results` and ESLint received `ENOENT`; the required standalone rerun passed with exit 0. This was an orchestration race, not a source lint failure. |
| `npm run build` | PASS — 1,755 modules; production bundle built. Existing warning: the main minified JavaScript chunk was 606.84 kB, above 500 kB. |
| `npm run test:e2e` | FAIL — 9 passed, 1 failed. The existing test `mock camera word capture reaches the real Docker API with V1 payload` expected HTTP 200 and received 502 because the Docker stack was stopped. The remaining tests also logged expected local proxy `ECONNREFUSED` messages. This is a pre-existing environment failure, not a regression. |

## Docker baseline

| Command | Result |
|---|---|
| `docker compose config` | PASS |
| `docker compose --profile ml config` | PASS |
| `docker compose ps` | PASS; no containers were running |

The rendered configuration confirmed the pre-simplification runtime defaults:

- API and inference `INFERENCE_MODE=mock`.
- Inference `MODEL_NAME=opensign-darija-landmark-mock` and no model/label/calibration paths.
- Browser MediaPipe model and WASM defaults pointed at Google Storage and jsDelivr.
- The normal profile contained web, API, inference, speech, speech worker, PostgreSQL, Redis, MinIO, and Nginx; `ml-trainer` appeared only under the `ml` profile.

## Baseline interpretation

The source suites were green except for the one Docker-dependent Playwright case run while Docker was stopped. Later validation must compare against this distinction and must not report that environment failure as a newly introduced regression.
