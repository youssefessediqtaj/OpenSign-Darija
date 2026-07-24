# Root Project Structure Final Report

Date: 2026-07-24  
Branch: `refactor/root-project-structure`

## Root files before and after

Before this pass, the root contained the required project entry points plus community,
dataset, and model-card documents that belonged under `.github/` and `docs/`:

```text
.agent/
.github/
.pytest_cache/
.ruff_cache/
CODE_OF_CONDUCT.md
CONTRIBUTING.md
DATASET_CARD.md
LICENSE
MODEL_CARD.md
Makefile
NOTICE
README.md
SECURITY.md
SPEECH_MODEL_CARD.md
THIRD_PARTY_DATASETS.md
apps/
artifacts/
docker-compose.yml
docs/
infrastructure/
ml/
packages/
scripts/
services/
tests/
.env.example
.gitignore
```

After cleanup, the root is limited to the intended project owners:

```text
.agent/
.github/
apps/
artifacts/
docs/
infrastructure/
ml/
packages/
scripts/
services/
tests/
.env.example
.gitignore
docker-compose.yml
LICENSE
Makefile
NOTICE
README.md
```

Retained root files and reasons:

- `README.md`: concise developer/contributor entry point.
- `LICENSE`: repository license.
- `NOTICE`: third-party and provenance notice.
- `Makefile`: root developer command surface.
- `docker-compose.yml`: local runtime orchestration.
- `.env.example`: local configuration template.
- `.gitignore`: repository-wide ignore policy.

Moved files:

- `CODE_OF_CONDUCT.md` → `.github/CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md` → `.github/CONTRIBUTING.md`
- `SECURITY.md` → `.github/SECURITY.md`
- `DATASET_CARD.md` → `docs/datasets/mosl-video-dataset-card.md`
- `THIRD_PARTY_DATASETS.md` → `docs/datasets/third-party-datasets.md`
- `MODEL_CARD.md` → `docs/model-cards/mosl-isolated-sign-v1.md`
- `SPEECH_MODEL_CARD.md` → `docs/model-cards/speech-service.md`
- loose architecture, operations, testing, ML, attribution, and integration docs were
  moved into `docs/architecture/`, `docs/operations/`, `docs/testing/`,
  `docs/datasets/`, `docs/model-cards/`, `docs/audits/`, and `docs/research/`.
- root cross-project test file moved to `tests/architecture/`.
- scripts moved to `scripts/verification/` and `scripts/benchmarking/`.

Deleted or removed as obsolete/generated:

- `.pytest_cache/`, `.ruff_cache/`, and generated `__pycache__/` folders.
- untracked obsolete `ml/artifacts/` experiment-output folder.
- empty folders left by moves.
- obsolete duplicate docs after content was merged:
  `docs/browser-speech-fallback.md`, `docs/speech-contract.md`,
  `docs/speech-provider.md`, `docs/speech-security.md`, `docs/privacy.md`,
  `docs/security.md`, `docs/manual-recognition-testing.md`,
  `docs/operations/backend-log-checklist.md`,
  `docs/operations/browser-console-checklist.md`,
  `docs/operations/inference-log-checklist.md`.
- stale docs that contradicted the current V1 runtime:
  `docs/landmark-schema.md` and `docs/signer-independent-testing.md`.

## Documentation

Final documentation categories:

- `docs/README.md`
- `docs/architecture/`
- `docs/datasets/`
- `docs/model-cards/`
- `docs/operations/`
- `docs/testing/`
- `docs/audits/`
- `docs/reports/`
- `docs/images/`
- `docs/research/`

Merged documents:

- Speech architecture, contract, provider, security, and fallback notes are consolidated
  into `docs/operations/speech.md`.
- Privacy and security notes are consolidated into
  `docs/architecture/privacy-security.md`.
- Manual physical-camera record is consolidated into
  `docs/testing/physical-camera.md`.
- Backend/inference/browser log checklists are consolidated into
  `docs/operations/troubleshooting.md`.
- Local training notes are consolidated into `docs/architecture/model-lifecycle.md`.

Broken-link validation:

- `tests/architecture/test_documentation_links.py` validates repository-local Markdown
  links.
- Latest architecture check result: `11 passed`.

## Community files

Community files now live in GitHub-compatible locations:

- `.github/CODE_OF_CONDUCT.md`
- `.github/CONTRIBUTING.md`
- `.github/SECURITY.md`

The root README links were updated to the new `.github/` paths. No root compatibility
duplicates remain.

## Dataset and model cards

Dataset documentation:

- `docs/datasets/README.md`
- `docs/datasets/mosl-video-dataset-card.md`
- `docs/datasets/third-party-datasets.md`
- `docs/datasets/provenance.md`
- `docs/datasets/licensing.md`
- `docs/datasets/quality-limitations.md`
- `docs/datasets/preprocessing.md`
- `docs/datasets/mendeley-mosl-v1-attribution.md`

Model-card documentation:

- `docs/model-cards/README.md`
- `docs/model-cards/mosl-isolated-sign-v1.md`
- `docs/model-cards/speech-service.md`
- `docs/model-cards/technical-smoke-model.md`

Preserved facts:

- active vocabulary remains `اب`, `احب`, `سوق`;
- public/input shape remains `60 × 75 × 3`;
- active ONNX checksum is unchanged;
- dataset manifest checksum is unchanged;
- local-only dataset policy and license uncertainty are preserved;
- class imbalance, signer-diversity, OOV, and physical-camera limitations remain explicit.

## Root folders

| Folder | Responsibility | Decision |
| --- | --- | --- |
| `.agent/` | Shared continuity for future Codex maintenance turns. | Kept with `.agent/README.md`. |
| `.github/` | CI workflows plus community/security documents. | Kept. |
| `apps/` | Public React application. | Kept. |
| `artifacts/` | Machine-readable reports, dataset manifests, and protected model metadata; large binaries ignored selectively. | Kept. |
| `docs/` | Human-maintained documentation and reports. | Kept and indexed. |
| `infrastructure/` | Nginx public gateway. | Kept. |
| `ml/` | Offline local data, preprocessing, training, evaluation, export, validation. | Kept; empty obsolete dataset/output folders removed. |
| `packages/` | Shared language-neutral contracts. | Kept because tests and service/browser contracts use it. |
| `scripts/` | Verification and benchmarking utilities. | Kept and organized. |
| `services/` | Stateless API, internal inference, internal speech. | Kept. |
| `tests/` | Cross-project architecture, contracts, privacy, and fixtures. | Kept and organized. |

## Code quality

- Added concise comments for non-obvious browser segmentation, payload validation,
  React Strict Mode detector cleanup, and the Python landmark schema module.
- Added `.agent/README.md`, `scripts/README.md`, `docs/README.md`, dataset and
  model-card indexes, Docker/model-asset/troubleshooting docs.
- Added cross-project tests for documentation links, contract closure, speech contract
  ownership, raw-media exclusion, and same-origin API gateway use.
- Updated script root detection after moving scripts one level deeper.
- Updated Makefile benchmark and architecture-check paths.
- Regenerated root and architecture audit evidence.

## Tests

Observed validation for this root-structure pass:

- `make verify`: passed.
- Architecture/contracts/privacy/docs: `11 passed`
- API: `54 passed`
- Inference: `29 passed`
- Speech: `9 passed`
- ML: `31 passed`
- Frontend unit tests: `30 passed`
- Ruff: passed for API, inference, speech, and ML
- MyPy: passed for API, inference, and speech
- ESLint: passed
- TypeScript/Vite build: passed
- Default Playwright: `4 passed`, `1 skipped` for the explicit Docker-gated real API
  case
- Compose config: passed for normal and `ml` profile
- Docker build: passed for web, API, inference, and speech
- Docker health: API, inference, and speech healthy; web and Nginx running
- Docker log scan: no `Traceback`, `Exception`, `ERROR`, `FATAL`, `panic`, or
  `Unhandled` patterns in the final 30-minute window.
- Final public API paths:
  `/health`, `/api/v1/health`, `/api/v1/version`,
  `/api/v1/recognitions/word`, `/api/v1/speech/sign`.
- Nginx public runtime checks:
  - `/` reachable
  - `/api/v1/health` healthy
  - `/api/v1/version` returned `1.0.0`
  - `/api/v1/recognitions/word` returned recognized `احب` with confidence `0.9815`
  - `/api/v1/speech/sign` returned completed WAV data for `احب`
- Real Docker Playwright with the local Y4M fake-camera fixture passed in non-strict
  private-path mode: `1 passed`.

Strict `PLAYWRIGHT_EXPECT_TWO_SIGNS=1` was attempted with both existing and alternate
local Y4M fixtures. It still failed because at least one of the two real Docker
decisions was UNKNOWN. This is documented as a fixture/model-quality limitation, not
reported as a passing two-known-sign result.

## Protected behavior

Machine-readable evidence:

- `artifacts/reports/root-structure-protected-assets-before.json`
- `artifacts/reports/root-structure-protected-assets-after.json`
- `artifacts/reports/root-structure-parity.json`

Protected parity:

- ONNX before/after:
  `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`
- Dataset manifest before/after:
  `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`
- Dataset records: `2216`
- Model package checksum manifest matches files: `true`
- Raw dataset files match manifest: `true`
- MediaPipe `.task` asset unchanged: `true`
- Canonical fixture top label: `احب`
- Canonical fixture accepted: `true`
- Protected model/data/MediaPipe/canonical outputs unchanged: `true`

Recognition and speech behavior preserved:

- anonymous public recognition remains;
- browser sends `60 × 75 × 3` finite landmarks through `/api`;
- API calls internal inference and speech services;
- known result displays Arabic/Darija and requests speech;
- UNKNOWN does not request speech;
- no direct browser inference/speech request is allowed;
- raw video/image/audio/base64/microphone fields remain forbidden.

## Remaining limitations

- Active vocabulary is limited to three labels: `اب`, `احب`, `سوق`.
- Active evaluation set is tiny: one validation and one test example per active class.
- OOV false-acceptance risk remains high.
- Physical-camera validation remains `UNCONFIRMED`.
- Strict two-known-sign real Docker Playwright remains `UNCONFIRMED` because local Y4M
  fixtures still produce at least one UNKNOWN decision.
- No model retraining, dataset modification, vocabulary change, or frontend redesign was
  performed.
