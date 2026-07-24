# Pre Root-Structure Baseline

Captured on 2026-07-24 before the `refactor/root-project-structure` organization pass.

## Git state

- Branch before creating this branch: `refactor/professional-project-structure`.
- New branch: `refactor/root-project-structure`.
- `git status --short` before branching: clean.
- `git diff --stat` before branching: empty.
- `git diff` before branching: empty.
- Recent commits before branching:
  - `61889c1 docs: record project structure branch publication`
  - `70eccd1 docs: professionalize project structure and audits`
  - `701e496 docs: record refactor branch deletion`
  - `b09dee2 docs: record main branch merge state`
  - `c860870 merge: integrate professional architecture refactor`
  - `b43f5f7 docs: record published refactor branch state`
  - `57962da refactor: simplify recognition architecture and lock production runtimes`
  - `a831df8 simplify and correct the complete application`
  - `d541440 Fix README preview images`
  - `16d7f91 adding images to readme file`

## Root files before cleanup

The repository root still contained documentation that belongs under `.github/`, `docs/datasets/`, and `docs/model-cards/`:

- `.agent/`
- `.env.example`
- `.git/`
- `.github/`
- `.gitignore`
- `.pytest_cache/`
- `.ruff_cache/`
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `DATASET_CARD.md`
- `LICENSE`
- `MODEL_CARD.md`
- `Makefile`
- `NOTICE`
- `README.md`
- `SECURITY.md`
- `SPEECH_MODEL_CARD.md`
- `THIRD_PARTY_DATASETS.md`
- `apps/`
- `artifacts/`
- `docker-compose.yml`
- `docs/`
- `infrastructure/`
- `ml/`
- `packages/`
- `scripts/`
- `services/`
- `tests/`

## Protected-asset baseline

Generated machine-readable snapshot:

- `artifacts/reports/root-structure-protected-assets-before.json`

Observed summary:

- Active ONNX SHA-256: `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`
- Dataset manifest SHA-256: `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`
- Dataset records: `2216`
- Model package checksum manifest matches files: `true`
- Raw dataset files match manifest: `true`
- Canonical top label: `احب`
- Canonical accepted: `true`

## Baseline validation

`make test-all` passed:

- Architecture/contracts: `6 passed`
- API: `54 passed`
- Inference: `29 passed`
- ML: `31 passed`
- Speech: `9 passed`
- Frontend unit tests: `30 passed`
- Playwright: `4 passed`, `1 skipped` for the Docker-gated real API browser check
- Ruff, MyPy, ESLint, TypeScript, and Vite build passed through the Make targets

`make compose-check` passed:

- `docker compose config`
- `docker compose --profile ml config`

`docker compose build` passed for:

- `api`
- `inference`
- `speech`
- `web`

`docker compose up -d && docker compose ps` passed:

- `opensigne-darija-api-1`: healthy
- `opensigne-darija-inference-1`: healthy
- `opensigne-darija-speech-1`: healthy
- `opensigne-darija-web-1`: running
- `opensigne-darija-nginx-1`: running on `0.0.0.0:8081->80/tcp`

## Baseline limitations

- Physical camera validation remains `UNCONFIRMED`.
- The default Playwright run skipped the Docker-gated real API camera case unless explicitly supplied with Docker and a fake-camera video fixture.
