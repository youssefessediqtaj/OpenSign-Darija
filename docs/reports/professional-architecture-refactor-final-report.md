# Professional architecture refactor — final report

Completed on 2026-07-23 from baseline commit
`a831df8fbc825a02d0b6a41753c22a89ba25d117` on
`refactor/professional-architecture`. No commit or push was performed.

## Outcome

The anonymous automatic recognition loop is preserved:

```text
camera → browser MediaPipe → automatic segmentation → 60×75×3 landmarks
→ public API → internal ONNX inference → Arabic/Darija result
→ known-only local speech → cooldown/reset → next sign
```

The public pages remain `/` and `/app/recognition`. Nginx is still the only
public gateway. The browser sends normalized finite landmarks and approved
segmentation metadata only; raw video, images, canvas exports, audio, Base64
camera content, and persistent anonymous identifiers are forbidden.

## Architecture delivered

- Web: reorganized into `app`, one recognition feature with `domain`, `state`,
  `hooks`, `services`, and `components`, plus small shared UI/config/API modules.
  Pure segmentation, normalization, resampling, sequence-quality, and contract
  logic remain deterministic and independently tested.
- API: reduced to health/version, strict word recognition, and supported-sign
  speech. Thin routes delegate to explicit recognition, request-protection, and
  speech orchestration services and typed internal clients.
- Inference: separated HTTP schemas/routes, runtime lifecycle/prediction, and
  model-package integrity. Startup validates checksums, vocabulary, Arabic
  mappings, calibration, ONNX types/shapes, performs warmup, bounds concurrency,
  and fails closed.
- Speech: reduced to strict schemas/routes, one local provider, system-TTS
  adapter, text/audio validation, bounded concurrency, and timeout handling.
- ML: remains offline-only. Current dataset audit, preprocessing, training,
  evaluation, export, validation, tests, model package, caches, and provenance
  remain separate from runtime services.
- Contracts: added language-neutral recognition and speech JSON Schemas plus
  parity/architecture tests spanning TypeScript, Pydantic, fixtures, Playwright,
  imports, dependencies, Docker, routes, and gateway boundaries.
- Operations: added service READMEs, architecture/dependency documentation,
  operational docs, a complete pre-change file inventory, and generated static
  dependency evidence.

## Simplification and deletion evidence

The baseline contained 349 tracked files. The final working source has 258 files:
156 old paths were removed, 65 new or moved paths were introduced, and 44
baseline paths were simplified in place. Removed code had zero supported runtime
references across startup, routes, imports, tests, Docker, Make, CI, scripts, and
current documentation commands.

Major removals include:

- unmounted authentication, admin, contribution, review, message, linguistic,
  database, migration, Redis/MinIO/storage, seed, job, and model-registry code;
- SQLAlchemy/Alembic/PostgreSQL/Redis/MinIO/JWT/Argon2 and other inactive API
  dependencies and environment configuration;
- runtime MediaPipe, OpenCV, and graphics system packages from inference;
- duplicate speech provider abstractions and obsolete persistence/job schemas;
- superseded two-class smoke trainer/validator, old split builder, placeholders,
  stale notebooks, duplicate README image package, and contradictory historical
  product/model documents.

Git history, the pre-refactor inventory, and retained provenance reports preserve
auditability. The ignored smoke model package remains as historical
reproducibility evidence; the active three-label package is unchanged.

## Dependency and container audit

The final graph contains 257 current source/config nodes and 190 resolved local
import edges, with:

- 0 circular import components;
- 0 forbidden cross-layer findings;
- 0 orphan module candidates;
- 0 unused declared dependency candidates.

The two unreferenced TypeScript export candidates are composite public type
members, not executable dead code. The suspicious `httpx2` speech dependency was
verified as intentional development-only FastAPI TestClient infrastructure.
Each Python service now has a tested transitive production lock; dev dependencies
are not installed in runtime images.

| Image | Pre-refactor | Final | Change |
| --- | ---: | ---: | ---: |
| API | 382,068,781 B | 187,122,936 B | −51.0% |
| Inference | 1,533,758,640 B | 303,138,583 B | −80.2% |
| Speech | 224,526,608 B | 224,545,238 B | effectively unchanged |
| Web | approximately 83.8 MB | 83,811,768 B | effectively unchanged |

## Final verification

| Gate | Result |
| --- | --- |
| Architecture/contract tests | 6 passed |
| API | 54 passed; Ruff and strict MyPy passed |
| Inference | 29 passed; Ruff and strict MyPy passed |
| Offline ML | 31 passed; Ruff passed; five expected Torch/ONNX warnings |
| Speech | 9 passed; Ruff and strict MyPy passed |
| Frontend | 30 passed; ESLint, TypeScript, and Vite build passed |
| Default Playwright | 4 passed, 1 intentional Y4M-dependent skip |
| Focused cooldown race repetition | 5/5 passed serially |
| Strict production Docker Playwright | 5/5 passed |
| Compose | normal/profile config, locked build, recreate, and health passed |
| Runtime logs | no traceback, fatal, exception, or error finding |

Final QA found and corrected two timing issues instead of masking them:

1. The development-only synthetic second sign could arrive before audio cooldown
   completed on a contended worker. Its deterministic rest interval now covers
   audio, React scheduling, cooldown, and reset; the public production bundle
   still contains no mock-camera bypass.
2. A nominal 20 FPS detector threshold could quantize to every fourth 60 Hz
   animation frame and measure 14.8 FPS. The target now has headroom; the rebuilt
   real MediaPipe/Y4M run passed the required two-capture ≥15 FPS assertion.

The strict browser run also verified two known decisions with exactly two speech
calls, UNKNOWN silence, duplicate suppression, no raw-media field, no direct
browser call to inference/speech, and no browser/page error.

The exact API paths remain:

```text
/health
/api/v1/health
/api/v1/version
/api/v1/recognitions/word
/api/v1/speech/sign
```

## Protected assets and parity

- ONNX SHA-256:
  `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`
- Model checksum-manifest SHA-256:
  `707367e05abc7840a1330fecbc8fd7d946e6decb82a88ecd0d618197e01034f6`
- Dataset manifest SHA-256:
  `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`
- Raw dataset verification: 2,216/2,216 records matched size and SHA-256.
- Labels: `اب`, `احب`, `سوق`.
- Input/output: `[batch,60,75,3]` → `[batch,3]`.
- Canonical logits remained
  `[-2.4934840202331543,1.7240511178970337,-0.6624970436096191]`.
- Canonical probabilities remained
  `[0.00021525139163713902,0.9914032816886902,0.008381485939025879]`.
- Canonical decision remained accepted label `احب`, margin
  `0.9830217957496643`.

The protected-assets comparison reports every model, dataset, processed-cache,
MediaPipe, canonical-output, preexisting report, and additive-report gate as
unchanged/preserved.

## Evidence

- `docs/audits/pre-architecture-refactor-baseline.md`
- `artifacts/reports/pre-architecture-refactor-baseline.json`
- `artifacts/reports/repository-file-inventory.json`
- `artifacts/reports/repository-file-inventory.csv`
- `docs/architecture/dependency-graph.md`
- `artifacts/reports/module-dependency-graph.json`
- `artifacts/reports/architecture-refactor-protected-assets.json`
- `artifacts/reports/architecture-refactor-final-report.json`

## Honest limitations

- A person repeating the final flow with the physical FaceTime HD camera remains
  `UNCONFIRMED`; deterministic production Chromium/Y4M is not represented as a
  physical-person test.
- Model-quality limits documented in the model card remain unchanged; this task
  did not retrain, replace, or broaden the three-label model.
- The supplied prompt file ends abruptly in section 15 after the incomplete
  example `index += 1`. All complete requirements present in the attachment were
  implemented; text beyond that cutoff was unavailable.
