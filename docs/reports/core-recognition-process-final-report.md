# Core recognition process final report

Final verification date: 2026-07-23  
Workspace: OpenSigne Darija, branch `main`

## Executive outcome

The application has been reduced to one public process:

> Activate camera → perform an isolated Moroccan sign → automatic boundary detection →
> local ONNX inference → Arabic/Darija result → automatic speech → cooldown/reset → next sign.

The software implementation, unit/integration suites, local-data audit, model package,
Docker stack, and non-intercepted production Playwright flow pass. The Playwright gate
clicks only `Activer la caméra`, processes two known camera sequences with the real local
MediaPipe runtime, sends two private `60 × 75 × 3` requests to the real Docker API, obtains
two recognized results, triggers speech twice, returns to the waiting state, and makes no
external-dataset or direct-inference request.

Two limitations prevent a production-readiness claim:

1. A physical-camera test with a person performing the signs is **UNCONFIRMED** because
   this execution environment has no controllable hardware-camera browser. The production
   fake-camera gate is not represented as a substitute.
2. The active model is a complete, real local ONNX baseline, but it has only three active
   lexical classes, one held-out test video per class, no signer identity, and weak
   out-of-vocabulary rejection. Its status remains
   `LIMITED_LOCAL_BASELINE_NOT_SIGNER_VALIDATED`.

## Audit

The required pre-change evidence is preserved in:

- `docs/audits/core-recognition-process-audit.md`
- `docs/audits/pre-simplification-test-baseline.md`
- `artifacts/reports/frontend-unused-code-audit.json`
- `artifacts/reports/backend-ml-unused-code-audit.json`

### Original application

The original repository exposed about 39 routes and combined recognition with accounts,
contribution/consent, review, dataset administration, external imports, alphabet mode,
fingerspelling, message building/history, linguistic administration, model controls,
speech controls, settings, dashboards, and technical prediction panels. Recognition
required mode selection plus manual `Commencer`, `Terminer`, or `Annuler` capture actions.
Docker defaulted to mock inference; the only real artifact was the two-class
`mosl-word-smoke-v1` package.

### Features removed from the core product

- Login, registration, profile, settings, dashboard, contribution, review, message,
  alphabet/fingerspelling, data-source, model-admin, linguistic-admin, and speech-admin UI.
- Manual capture/countdown/finish/submit controls, mode selection, camera diagnostics,
  landmark overlays, Top-K/model/schema panels, and duplicate recognition state stores.
- Public legacy/mock/alphabet recognition paths, persisted confirmation/correction flow,
  stateful message speech, and public model-selection/reload surfaces.
- Kaggle and Mendeley downloaders, external archive/import/registry code, external source
  runtime routes and UI, remote MediaPipe downloader, related Make targets, credentials,
  dependencies, and dead tests.
- Legacy 30-frame/63-feature, alphabet, generic trainer, placeholder evaluator/exporter,
  and completed migration-only ML code.
- Stateful runtime dependencies that are not required for the public loop: PostgreSQL,
  Redis, MinIO, migration/seed startup, speech worker, and model-registry activation.

The frontend audit reviewed 113 candidates and removed 103 files while retaining 10 core
modules. The backend/ML audit records 80 removed scoped files: 7 API, 3 inference, 1
speech, and 69 ML files.

### Features retained

- Anonymous camera permission and preview.
- Browser-local MediaPipe Holistic landmark extraction using bundled local model/WASM
  assets and the CPU delegate.
- One authoritative recognition state machine and automatic static/dynamic segmentation.
- Strict shoulder-centered `OPEN_SIGNE_LANDMARK_SCHEMA_V1`.
- Browser → public API → internal inference boundary; the browser never calls inference.
- Payload/rate/quality validation and rejection of raw video, image, audio, unknown fields,
  NaN, Infinity, wrong shape, wrong mode, and wrong schema.
- Real local ONNX Runtime inference with package-integrity and compatibility checks.
- Calibrated known/UNKNOWN decision and compact public response.
- Arabic label mapping and automatic known-only speech with `ar-MA` then `ar` fallback.
- Health/readiness/version endpoints and an optional offline-only Docker ML audit.
- Historical persistence modules/migrations and the smoke model package remain isolated on
  disk to avoid destructive schema removal and preserve technical provenance; none is
  mounted into the public recognition flow.

### Authentication decision

Recognition and sign speech are public and stateless. The frontend sends no authorization
header, login redirect, persistent anonymous identifier, or localStorage identity. Auth
pages and active public auth routes were removed from the core route graph. Historical
auth/persistence code remains unmounted where destructive database removal would require a
separate migration decision.

### External ingestion decision

There is no active external dataset downloader, import route, UI control, credential, or
Docker job. Training and preprocessing use only
`ml/data/external/mosl-video-dataset/`. Attribution, citations, and license/provenance
notes remain. Offline-workflow regression tests prevent hidden internet dependencies.

### Final runtime surface

- Frontend routes: `/` and `/app/recognition`, both rendering the same anonymous product.
- Public API: health/version, `POST /api/v1/recognitions/word`, and
  `POST /api/v1/speech/sign`.
- Internal inference: health/readiness/version/model plus `POST /predict/word`.
- Internal speech: health/readiness/version/voices plus `POST /synthesize`.
- Docker services: web, API, inference, speech, and Nginx; `ml-audit` is an optional
  one-shot profile.

## Local dataset

Source reports:

- `artifacts/reports/local-mosl-dataset-audit.json`
- `artifacts/reports/local-mosl-dataset-audit.csv`
- `artifacts/reports/supported-sign-vocabulary-v1.json`
- `artifacts/reports/supported-sign-vocabulary-v1.csv`
- `artifacts/reports/model-v1-split-report.json`

| Measure | Verified result |
|---|---:|
| Local videos | 2,216 |
| Isolated-word videos | 2,145 |
| Alphabet videos retained for audit only | 71 |
| Unique normalized labels, including empty | 1,592 |
| Valid non-empty normalized labels | 1,591 |
| Invalid-label videos | 15 |
| Unique binary checksums | 2,197 |
| Duplicate checksum groups / extra rows | 10 / 19 |
| Valid checksum-keyed landmark caches | 2,197 |
| Manifest rows covered by caches | 2,216 |
| Missing or invalid processed artifacts | 0 |
| Minimum independent examples | 5 |
| Dataset-eligible labels / samples | 11 / 59 |
| Dataset-eligible split | 37 train / 11 validation / 11 test |
| Active lexical model split | 9 train / 3 validation / 3 test |

Category counts are 1,941 Diverse, 130 Numbers, 71 Letters, 59
Days/Months/Seasons, and 15 Pronouns. The 10 duplicate groups all contain ambiguous
cross-label assignments and are excluded from training. The manifest SHA-256 is
`558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`.

Label classifications are:

- 11 `SUPPORTED_FOR_TRAINING`
- 1,539 `INSUFFICIENT_SAMPLES`
- 41 `EXCLUDED_FOR_QUALITY`
- 1 invalid normalized-label record representing the 15 invalid videos

The 11 minimum-five dataset-eligible labels are numeric `11`, `12`, `14`, `15`, `16`,
`17`, `18`, `19` and lexical `اب`, `احب`, `سوق`. Validation-only scope comparison
showed the lexical subset was materially stronger than the mixed numeric/lexical scope,
so the active user model honestly supports only:

| Label key | Arabic display | Examples | Train / validation / test |
|---|---|---:|---:|
| `اب` | `أَبٌ` | 5 | 3 / 1 / 1 |
| `احب` | `أَحَبَّ` | 5 | 3 / 1 / 1 |
| `سوق` | `سُوقٌ` | 5 | 3 / 1 / 1 |

The split uses seed 42, groups by binary SHA-256, stratifies by label, has no checksum
leakage, and keeps UNKNOWN labels disjoint. Signer identity is absent from the manifest
and filenames, so signer-independent splitting and signer-diversity metrics are
unavailable.

## Model

The real package is `artifacts/models/mosl-isolated-sign-v1/`. It contains the required
ONNX model, labels, supported signs, landmark/preprocessing contracts, training config,
metrics, confusion matrix, classification report, calibration, manifest checksum,
checksums, ONNX/package validation, split provenance, and model card.

### Training and selection

All candidates used the same local data, active split, label index, preprocessing, and
validation-only selection procedure:

| Candidate | Validation macro F1 | Validation UNKNOWN rejection | Average / P95 ONNX latency | Parameters |
|---|---:|---:|---:|---:|
| Bidirectional GRU | 1.000 | 0.544 | 1.168 / 1.247 ms | 64,899 |
| Temporal convolution + GRU | 1.000 | 0.471 | 1.576 / 1.680 ms | 89,987 |
| Lightweight Transformer | 1.000 | 0.588 | 0.647 / 0.735 ms | 85,699 |

The lightweight Transformer was selected without test-set peeking. Training used seed 42,
class-weighted loss, balanced sampling, gradient clipping, learning-rate scheduling,
early-stopping support, checkpoint save/recovery, controlled temporal resampling, up to
four dropped frames, coordinate noise, minor scale/translation augmentation, and no
horizontal mirroring. The selected run completed 40 epochs in 1.789 seconds.

### Held-out and UNKNOWN results

| Metric | Result |
|---|---:|
| Active vocabulary | 3 signs |
| Test samples | 3, one per class |
| Top-1 | 0.6667 |
| Top-3 | 1.0000 |
| Macro F1 | 0.5556 |
| Balanced accuracy | 0.6667 |
| Temperature | 0.5 |
| Maximum-probability threshold | 0.0 |
| Margin threshold | 0.8492978 |
| Validation OOV rejection, 68 OOV samples | 0.5882 |
| Test OOV rejection, 68 OOV samples | 0.4412 |
| Test OOV false acceptance | 0.5588 |

UNKNOWN uses calibrated temperature-scaled maximum probability plus the class-margin
threshold. Invalid duration, insufficient usable frames, missing hands/pose, low dynamic
motion, and unreliable boundaries are rejected before inference. UNKNOWN is displayed
but never spoken.

### ONNX validation

- Input: `landmarks`, `[batch, 60, 75, 3]`, float32.
- Landmark order: 33 pose + 21 left hand + 21 right hand.
- Output: `logits`, `[batch, 3]`.
- ONNX checker and CPUExecutionProvider load: passed.
- PyTorch/ONNX maximum absolute difference: `1.1920928955078125e-7`.
- Top-K parity: passed.
- Package checksum/required-file/compatibility validation: passed.
- Model file size: 411,736 bytes.
- Direct ONNX average/P95 latency: 0.647/0.735 ms over 40 repeats.

The previous `mosl-word-smoke-v1` remains only as `TECHNICAL_SMOKE_ONLY`,
`NOT_USER_MODEL`, and `NOT_PRODUCTION_READY`; it supports numeric labels `16` and `17`
and is not active. Docker reports `mosl-isolated-sign-v1` version `1.0.0`,
`mock: false`, status `active`.

### Production-readiness assessment

The engineering package is complete and reproducible, but the recognition quality is not
production-ready. Three test examples cannot establish generalization, signer-independent
accuracy is unknown, and OOV false acceptance is 55.9% on the held-out OOV sample. The
model must remain a limited local baseline until independently signed, larger, cleaner,
camera-representative data improves known accuracy and UNKNOWN rejection.

## Automatic recognition

The frontend uses one `RecognitionFlowState`:

`CAMERA_OFF → INITIALIZING → WAITING_FOR_SIGN → CAPTURING → RECOGNIZING →
DISPLAYING/SPEAKING → COOLDOWN → WAITING_FOR_SIGN`, with `ERROR` for recoverable
failures.

### Boundary detection

- MediaPipe runs browser-local with a 20 FPS target. CPU-first initialization avoids the
  synchronous GPU-delegate stall observed in headless Chromium.
- A rolling 8-frame pre-roll is retained.
- Dynamic start requires motion energy at or above 0.12 for two detector frames.
- Static start requires a stable hand configuration outside a clear resting zone for
  750 ms, using shoulder-scaled hand zones and a learned rest baseline when available.
- Capture ends after energy remains at or below 0.045 for 420 ms, followed by a 3-frame
  post-roll.
- Minimum duration is 500 ms; maximum is 6,000 ms; at least 8 usable pose+hand frames are
  required.
- Usable frames are uniformly resampled to exactly 60, normalized to 75 shoulder-centered
  landmarks × 3 finite coordinates, and submitted automatically.
- Cooldown is at least 800 ms and reset requires 350 ms of stable rest/no-hands.
- A 12-s detector initialization guard and detector-exception handling transition to a
  visible recoverable error rather than leaving the page stuck.

### Duplicate suppression

The segmenter compares a 12-frame pose/hand descriptor against the last recognized
sequence. Similarity of at least 0.985 inside a 3,000-ms duplicate window is suppressed
until a real rest reset is observed. A 15-second held-pose simulation produced one initial
completion and zero duplicates. The production fake-camera gate repeated the same known
sign after a 3-second rest and correctly allowed the second cycle.

### Segmentation and runtime measurements

Source reports:

- `artifacts/reports/frontend-automatic-segmentation-benchmark.json`
- `artifacts/reports/api-runtime-benchmark.json`
- `artifacts/reports/speech-runtime-benchmark.json`

| Measure | Result |
|---|---:|
| Detector target | 20 FPS |
| Real MediaPipe fake-camera cadence | 15.1 and 15.3 FPS in the diagnostic run; final gate enforces both sequences ≥15 FPS |
| Dynamic start observation | 2 frames / nominal 100 ms |
| Static start dwell | 750 ms |
| Stable end + post-roll | nominal 420 + 150 = 570 ms |
| Payload finalization, 100 runs | 2.845 ms mean / 3.040 ms P95 |
| 60-second rest simulation | 1,200 frames; 0 starts, 0 completions, 0 API candidates |
| Held-pose simulation | 15 seconds; 0 duplicate completions |
| Direct ONNX | 0.647 ms mean / 0.735 ms P95 |
| Real API round trip, 20 requests | 45.523 ms mean / 59.666 ms P95 |
| Server-reported request latency | 32.3 ms mean / 49.0 ms P95 |
| Speech generation, 5 requests | 28.368 ms mean / 22.444 ms P95; max 63.065 ms |
| Speech payload | 5/5 playable WAV; 36,184 bytes average; no fallback |

The component P95 after a segment has finalized is approximately 62.7 ms
(3.040-ms payload construction + 59.666-ms API round trip), excluding small browser
render scheduling. Including the configured 570-ms boundary confirmation gives an
estimated component total near 633 ms from stable motion cessation to response, below the
preferred one-second target in this deterministic environment. This is a derived
component estimate, not a physical-camera end-to-text measurement.

Text-to-audio network generation P95 is 22.444 ms, but actual audible-start latency
depends on browser autoplay, audio decoding, and the device output path and is
**UNCONFIRMED** on physical hardware.

## Process validation

### Production Playwright

Final result: **5 passed**.

The strict non-intercepted case used a Y4M stream constructed locally from black rest
frames and two copies of the supported local video `أَحَبَّ (إِشَارَة 2).mp4`, separated
by three seconds of rest. It:

- opened `http://127.0.0.1:8081/app/recognition`;
- clicked only `Activer la caméra`;
- loaded the bundled MediaPipe WASM and model without an internet request;
- reached `Prêt — Faites un signe`;
- created two automatic dynamic segments at at least 15 effective FPS;
- sent exactly two anonymous `60 × 75 × 3` finite landmark payloads;
- received two HTTP 200 recognized decisions for `احب` / `أَحَبَّ`;
- displayed the Arabic result and sent two corresponding sign-speech requests;
- returned to waiting and emitted no third/held duplicate;
- sent no raw video, image, canvas, base64, microphone audio, auth header, persistent
  anonymous identifier, direct inference request, alphabet request, or external-dataset
  request;
- produced no page error or unexpected console error.

MediaPipe/TensorFlow Lite emits the exact informational diagnostic
`INFO: Created TensorFlow Lite XNNPACK delegate for CPU.` through the browser error
channel. The test filters only that known upstream diagnostic and continues to fail on
every other console error.

Separate deterministic cases verify camera refusal messaging, two automatic mocked
cycles, one speech request per known result, UNKNOWN with zero speech, public routing,
absence of manual controls, payload privacy, cooldown/reset, and forbidden-request
absence.

### Docker and service network

- `docker compose config`: passed.
- `docker compose --profile ml config`: passed.
- `docker compose build`: passed.
- `docker compose --profile ml build`: passed.
- `docker compose up -d`: passed.
- `docker compose ps`: API, inference, and speech healthy; web and Nginx running on
  `localhost:8081`.
- Optional `docker compose --profile ml run --rm ml-audit`: valid, 2,216 videos, 11
  minimum-five labels, 59 samples, split 37/11/11.
- API health reports inference and speech healthy.
- Local MediaPipe task model and WASM assets return HTTP 200.
- Runtime logs contain no traceback, exception, fatal error, or application crash.
  Nginx reports non-blocking temporary-file buffering warnings for the 13.7-MB local model/
  WASM assets and ~84-KB recognition payloads.

## Automated test results

| Suite | Final result |
|---|---|
| API | 54 passed; Ruff passed; strict MyPy passed |
| Inference | 25 passed; Ruff passed; strict MyPy passed |
| ML | 31 passed; Ruff passed |
| Speech | 8 passed; Ruff passed; strict MyPy passed |
| Frontend unit | 30 passed |
| Frontend lint/build | ESLint passed; TypeScript/Vite passed; 334.80-KB JS / 106.09-KB gzip |
| Playwright | 5 passed, including strict real-Docker two-known-sign gate |
| Model package | ONNX/package validation passed; vocabulary 3 |
| Compose | normal/profile config and builds passed; running stack healthy |
| Diff hygiene | `git diff --check` passed |

The expected ML warnings are PyTorch nested-tensor prototype and ONNX tracing/export
warnings covered by the explicit ONNX checker, runtime, exact-shape, finite-output, and
parity tests. API/inference each report one upstream Starlette/httpx deprecation warning.

## Physical-camera validation

Status: **UNCONFIRMED — manual acceptance gate remains**.

No controllable physical camera or in-app browser was available to this execution
session. Therefore the report does not claim:

- a person performed both supported signs successfully;
- physical camera permission-to-ready latency;
- physical detector FPS/dropped frames or thermal behavior;
- real-world boundary precision/recall under clothing, lighting, distance, occlusion, and
  background variation;
- physical-camera sign-end-to-text latency;
- device-audible playback start or autoplay behavior.

The stack remains running at `http://localhost:8081/app/recognition` for the manual gate
documented in `docs/testing-camera.md`. The operator must click only
`Activer la caméra`, perform supported signs, inspect console/network, and record the
actual result without reclassifying UNKNOWN as success.

## Remaining limitations

- 1,539 normalized label records have fewer than five independent usable examples; 41 are
  excluded for quality/ambiguity; invalid filenames account for 15 videos.
- Only three lexical signs are active despite 1,591 valid non-empty normalized labels.
- Each active class has only five examples and one test video.
- Signer identity/diversity and signer-independent generalization are unknown.
- OOV rejection is below a production safety bar.
- Real-world thresholds are not calibrated on representative live-camera rest/sign
  recordings.
- Lighting, framing, clothing, occlusion, signing speed, camera mirroring, and device
  performance may materially change behavior.
- The local speech provider is experimental Arabic/Darija-oriented synthesis; natural
  Moroccan pronunciation is not established.
- Continuous signing, sentence segmentation, grammatical translation, and continuous
  language translation are not supported. This is isolated-sign classification only.
- Historical persistence/migration code remains isolated rather than being destructively
  removed; a future database-removal project would require explicit migration approval.

## Final acceptance status

All code-controlled and automated acceptance criteria pass, including the exact
activate-camera → two automatic known recognitions → Arabic display → two speech calls →
rest/reset loop. The sole unexecuted acceptance criterion is the physical-camera/person
test. The model is active and real, not mock or smoke, but must remain labeled a limited
local baseline until the documented data and real-world validation limitations are
resolved.
