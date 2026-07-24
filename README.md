# OpenSign Darija

OpenSign Darija is a local research prototype for anonymous Moroccan Sign Language
isolated-word recognition. The current product is intentionally narrow: one browser
camera loop, one protected local ONNX model package, Arabic/Darija display, and
known-result speech.

It is not a certified interpreter and is not production-ready.

## User flow

```text
Activate camera
→ browser MediaPipe
→ automatic sign start/end detection
→ 60 × 75 × 3 landmark sequence
→ public FastAPI API through /api
→ internal ONNX inference
→ Arabic/Darija result or UNKNOWN
→ automatic speech for known results only
→ cooldown
→ wait for the next sign
```

There are no login screens, admin panels, public dataset imports, manual capture
controls, model selectors, PostgreSQL, Redis, or MinIO in the active runtime.

## Privacy model

Camera pixels stay in the browser. The browser sends only finite normalized landmarks,
presence masks, segmentation metadata, and aggregate quality values to the public API.

The browser must never send raw video, images, screenshots, canvas exports, base64 camera
payloads, microphone audio, or arbitrary text-to-speech input. It calls only same-origin
`/api` routes; inference and speech services are private Docker-network services.

## Active vocabulary and limits

The active model recognizes only three unambiguous lexical labels:

- `اب` — `أَبٌ`
- `احب` — `أَحَبَّ`
- `سوق` — `سُوقٌ`

UNKNOWN rejection is calibrated but limited. The held-out active test set has only three
known examples and OOV false acceptance remains high, so the model is a local baseline,
not a safety guarantee.

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
services/api/    Public stateless FastAPI API
services/inference/ Internal ONNX Runtime inference service
services/speech/ Internal local Arabic speech service
tests/           Cross-project architecture, contract, privacy tests and fixtures
```

Root files are intentionally limited to project entry points: `README.md`, `LICENSE`,
`NOTICE`, `Makefile`, `docker-compose.yml`, `.env.example`, and `.gitignore`.

## Quick Docker startup

```bash
docker compose build
docker compose up -d
docker compose ps
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
