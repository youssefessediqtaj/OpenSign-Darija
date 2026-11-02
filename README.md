# OpenSign Darija

OpenSign Darija is a local research prototype for anonymous Moroccan Sign Language
isolated-sign experimentation. The local development interface uses one browser camera
loop and the experimental COLORS_V1 ONNX model for diagnostic color candidates.

It is not a certified interpreter and is not production-ready.

## User flow

```text
Activate camera
→ browser MediaPipe
→ automatic sign start/end detection
→ 60 × 75 × 3 landmark sequence
→ public FastAPI API through /api
→ internal ONNX inference
→ experimental color candidate, UNKNOWN, or MODEL_NOT_READY
→ no automatic speech
→ cooldown
→ wait for the next sign
```

There are no login screens, admin panels, public dataset imports, manual capture
controls, model selectors, PostgreSQL, Redis, or MinIO in the active runtime.

## Privacy model

For recognition, camera pixels stay in the browser. The browser sends only finite normalized landmarks,
presence masks, segmentation metadata, and aggregate quality values to the public API.

The recognition flow does not send raw video, images, screenshots, canvas exports, base64
camera payloads, microphone audio, or arbitrary text-to-speech input. It calls only same-origin
`/api` routes; inference and speech services are private Docker-network services.

## Optional community contributions

A separate `/contribute` page offers an adult video contribution workflow. Submission is
**closed by default** pending controller/CNDP configuration, approved reference media,
and storage readiness. When enabled, explicit submissions upload identifiable video to
private quarantine; they do not enter recognition or training automatically. See the
[contribution guide](docs/contributions/README.md) and its readiness checklist.

## COLORS_V1 research direction

The local development interface displays diagnostic candidates for nine colors:
black, blue, brown, green, orange, pink, red, white, and yellow. Both blue variants
map to blue. The one-epoch GRU smoke model is uncalibrated and scientifically
unvalidated. Its candidates are never spoken or presented as accepted recognition.
Legacy model weights remain archived; the local color runtime does not load or fall
back to them. The source videos and derived features remain pending review.

See [COLORS_V1 dataset preparation](ml/datasets/colors_v1/README.md) and the
[local runtime audit](docs/audits/colors-v1-local-runtime-2026-11.md) for details.

## Repository structure

```text
.agent/          Codex continuity notes for this workspace
.github/         CI workflows and community files
apps/web/        React/Vite browser recognition app
artifacts/       Local generated reports and protected model packages
docs/            Architecture, operations, datasets, model cards, tests, reports
infrastructure/  Nginx public gateway configuration
ml/              Local MoSL data, preprocessing, training, evaluation, export, validation
packages/        Shared language-neutral contracts
scripts/         Verification and benchmarking utilities
services/api/    FastAPI recognition API and optional private contribution workflow
services/inference/ Internal ONNX Runtime inference service
services/speech/ Internal local Arabic speech service
tests/           Cross-project architecture, contract, privacy tests and fixtures
```

Root files are intentionally limited to project entry points: `README.md`, `LICENSE`,
`NOTICE`, `Makefile`, `docker-compose.yml`, `docker-compose.local.yml`, `.env.example`, and `.gitignore`.

## Requirements and model assets

The verified development setup uses Python 3.12, Node.js 22 with npm, and Docker
Compose. GPU is not required. The local ONNX model and MediaPipe task are ignored by
Git and must already be provisioned at the paths in [model assets](docs/operations/model-assets.md);
a fresh clone alone does not contain them or the raw dataset. Review their provenance
and usage restrictions before obtaining or sharing them. Offline video preprocessing
also needs OpenCV and MediaPipe, as described in the ML workspace.

## Quick Docker startup

```bash
make up
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
```

Open the app at:

```text
http://localhost:8081/app/recognition
```

## Development commands

```bash
make help
make install
make ml-install
make up
make down
```

## Testing commands

```bash
make test-all
make compose-check
make architecture-check
make verify
```

Useful focused checks:

```bash
make test-backend
make test-inference
make speech-test
make test-ml
make test-frontend
make test-e2e
```

## Documentation index

- [Documentation home](docs/README.md)
- [Architecture](docs/architecture/overview.md)
- [Runtime flow](docs/architecture/runtime-flow.md)
- [Repository map](docs/architecture/repository-map.md)
- [Operations](docs/operations/local-development.md)
- [Configuration](docs/operations/configuration.md)
- [Community contribution workflow](docs/contributions/README.md)
- [Docker](docs/operations/docker.md)
- [Testing](docs/testing/automated-tests.md)
- [Dataset documentation](docs/datasets/README.md)
- [Model cards](docs/model-cards/README.md)
- [Privacy and security](docs/architecture/privacy-security.md)
- [Root project structure final report](docs/reports/root-project-structure-final-report.md)
- [Professional project structure report](docs/reports/professional-project-structure-report.md)

## Community and security

- [Contributing](.github/CONTRIBUTING.md)
- [Code of conduct](.github/CODE_OF_CONDUCT.md)
- [Security policy](.github/SECURITY.md)
- [License](LICENSE)
- [Notice](NOTICE)

## Non-production warning

OpenSign Darija is a research prototype with limited vocabulary, small evaluation
coverage, no signer-independent validation, and `UNCONFIRMED` physical-camera
generalization. Do not use it for medical, legal, financial, emergency, accessibility
compliance, or safety-critical decisions.
