# Core recognition process supervisor audit

Audit completed on 2026-07-19 before application-code changes. Scope included `apps/`, `services/`, `ml/`, `packages/`, `scripts/`, `tests/`, `docs/`, `infrastructure/`, Compose, Make, README, environment examples, all mounted FastAPI routes, every frontend route and feature family, runtime services, dataset modules, model artifacts, and current tests.

## Executive conclusion

The repository contains many independently useful phase prototypes, but the requested process does not currently exist. The page accepts anonymous visitors, yet it is wrapped in an application/admin navigation shell and requires explicit `Commencer` and `Terminer` actions. There is no automatic boundary detector, authoritative recognition state machine, cooldown/reset logic, duplicate suppression, automatic speech, or second-sign loop. Docker starts in mock inference mode. The only real ONNX package is a two-class smoke artifact for labels `16` and `17`, trained with four samples and validated with two. Its numeric keys do not map to seeded Arabic sign meanings.

The reusable foundation is sound: browser-only MediaPipe extraction, no camera/audio upload, strict V1 landmark normalization, exact `60 × 75 × 3` schemas, an API-to-internal-inference boundary, an ONNX Runtime loader, a local speech service, and a complete local 2,216-video MoSL copy with validated caches.

## Required audit answers

### 1. What is the current application flow?

The public home promotes a simulated demo. A visitor who knows `/app/recognition` can open it anonymously through a special `ProtectedRoute` exception. The page asks for camera access, initializes MediaPipe, displays framing/lighting/debug guidance, asks the user to select word or alphabet mode, then requires `Commencer`, a three-second countdown, and `Terminer`. The browser normalizes landmarks and posts them to the API; the API calls the internal inference service, persists technical Top-K results, and displays a technical prediction panel. Speech is a separate finalized-message workflow requiring another user action.

### 2. Which pages and components are visible to the user?

`AppRoutes` exposes about 39 routes: home/demo/signs/about/privacy/accessibility/login/register; recognition, message builder/history/favorites, settings, contribution consent/campaign/session/history; and review, datasets, external datasets, models, linguistics, and speech administration. Anonymous recognition is rendered through `AppLayout`, whose navigation exposes contribution, messages, settings, review, external datasets, model registry, linguistics, speech, and session/logout controls.

The recognition page visibly includes mode tabs, instructions, camera selector, detector status, framing and lighting cards, landmarks overlay, countdown/progress, manual camera/capture controls, Top-K predictions, model/schema/latency data, confirm/correct actions, and message-builder actions.

### 3. Which features are unrelated to the required process?

Public registration/accounts, simulated demo, sign catalogue, alphabet/fingerspelling, settings, dataset contribution/consent/review/export, external-source administration, message construction/history/favorites/revisions, linguistic administration, model-selection UI, and most dashboards are unrelated to activate-camera → sign → meaning → speech.

### 4. Which features block or complicate recognition?

Manual capture and mode selection directly block the target flow. The cluttered app shell obscures the single public action. Model registry state can diverge from the actual inference process because database activation does not reload or configure inference weights. Arabic meaning currently depends on seeded `Sign` records that do not contain the smoke model's numeric labels. Speech requires creating/finalizing a message. Legacy 30×63, alphabet, V1, mock, and real paths coexist.

There is also a detector lifecycle defect: `RecognitionWorkspace` recreates a recorder object on render; that destabilizes `handleFrame` and `useHolisticLandmarker.start`, so the camera effect can start additional animation-frame loops without stopping the prior loop. A rejected MediaPipe loader promise is cached permanently.

### 5. Does recognition require authentication?

No. `/app/recognition` is an anonymous frontend exception, and API recognition endpoints use optional authentication. Anonymous session ID or client IP supplies the rate-limit key. The route is nevertheless visually embedded in an authenticated-style shell. Admin activation still legitimately requires role-based authentication.

### 6. Does the user currently need to start and finish capture manually?

Yes. `CameraControls` renders `Commencer`, `Terminer`, and `Annuler`; `useLandmarkRecorder` ignores frames until manually started and finalizes only when the finish callback runs.

### 7. Is recognition continuous or isolated?

It is manual isolated-sign recognition. `WORD_ISOLATED` is the only V1 word request mode. A `CONTINUOUS_SIGNING` enum exists but has no implementation.

### 8. Is automatic sign segmentation implemented?

No. There is no rolling pre-roll buffer, motion/rest state, static dwell detection, post-roll, maximum-duration finalization, cooldown, return-to-rest condition, or duplicate comparison.

### 9. Which model is actually loaded?

No service was running during the audit. With the committed Compose defaults, inference loads no ONNX file and enters ready mock mode. A legacy local database row naming a mock model does not load weights.

### 10. Is real inference used or mock inference?

Mock inference is the Docker default. Real mode is fail-closed but must be explicitly supplied `MODEL_PATH`, `LABELS_PATH`, and optional threshold/calibration paths.

### 11. Which labels can the current model recognize?

Default word mock output selects from `oui`, `non`, `aide`, `eau`, `medecin`, `douleur`, `merci`, `vouloir`, `ou`, and `urgence`. The only real ONNX artifact has labels `16` and `17`. Neither is an accepted user vocabulary.

### 12. Is the current model trained only on two smoke-test classes?

Yes. `mosl-word-smoke-v1` uses labels `16` and `17`, four training samples, two validation samples, two epochs, and explicitly smoke-only metrics. Its 1.0 validation accuracy/F1 are based on only one validation sample per class. It is not active by default and activation is development-guarded.

### 13. What dataset is currently used for training?

The smoke trainer reads the locally generated `mosl-word-isolated-v1` manifest derived from the native `ml/data/external/mosl-video-dataset/` copy. Older generic trainers still point at an empty legacy 30-frame/63-feature contributor manifest and are not usable for the V1 word model.

### 14. Are external Kaggle/Mendeley ingestion modules still active?

Yes. Make exposes Kaggle download and Mendeley import commands; a Kaggle module invokes the CLI for metadata and download; external archive/registry/license/audit modules remain; alphabet and legacy Mendeley-oriented pipelines remain; the API mounts external-source admin routes and persists external source/label/import tables; frontend routes and controls invoke them.

### 15. Does any runtime code download external datasets?

The normal web/API/inference startup does not automatically download a dataset. Operator-reachable Kaggle CLI code does perform network downloads. The Mendeley helper writes remote/manual-import metadata rather than downloading bytes. Normal MoSL preprocessing uses the present local MediaPipe task asset, but optional `urlopen` downloading and a Make downloader remain. Browser MediaPipe assets also default to remote URLs, which is not dataset ingestion but is an avoidable runtime internet dependency.

### 16. Which frontend components are unused?

Proven unreferenced candidates include `recognition/workers/landmark.worker.ts`, `messages/stores/message.store.ts`, three unused message type files, several unused type aliases, `getPreferredCameraDeviceId`, `enableLandmarkOverlay`, legacy/mode client methods, unused dataset/message/speech client methods, and unused recorder diagnostic state. Conditional dead code after removal of manual/alphabet flows includes `CameraControls`, `CaptureCountdown`, `useRecognitionCapture`, `RecognitionInstructions`, fingerspelling UI, legacy compact normalization, and the existing technical `PredictionPanel`.

A machine-readable decision inventory will be written to `artifacts/reports/frontend-unused-code-audit.json` before removals are finalized.

### 17. Which backend endpoints are unused?

For the core flow, only health/version, anonymous V1 word recognition, internal word inference, operational model activation/health, and speech generation are required. Clear dead/placeholder endpoints include message speech `prepare`, internal speech `prepare` and generation lookup placeholders, and no-op reload endpoints. Legacy/mock/alphabet recognition and confirmation/correction are outside the normal user process. Contribution, dataset, external-source, linguistic, and message endpoints remain reachable prototypes but are unrelated to this product contract.

### 18. Which ML scripts are unused?

External/alphabet/legacy-Mendeley pipelines, completed source-migration helpers, empty legacy contributor-dataset loaders/trainers/configs, placeholder evaluator/export/package/register scripts, and the legacy 30×63 benchmark do not participate in the native V1 model path. Several Make production aliases are misleading: `ml-register-word-model` aliases smoke registration, while `ml-train-word` targets the wrong empty manifest.

### 19. Which authentication modules are still required?

Authentication is not required for recognition. It remains required if isolated internal model administration is retained: user/role entities, password/token helpers, login/current-user dependencies, and role enforcement. Registration/profile/contributor/reviewer UI and endpoints are not required by the public flow and must not appear there. Database/auth removal must follow a dependency audit and migrations; it should not be done blindly.

### 20. Which Docker services are still required?

Under the current persistence design, web, API, inference, speech, PostgreSQL, and Nginx are core. MinIO and the speech cleanup worker are needed only if cached WAV objects and signed URLs remain. Redis is not used by current recognition rate limiting or speech caching; it is only a health/dependency requirement. `ml-trainer` is a profile-only one-shot build tool, not runtime. A direct sign-speech path can reduce core dependencies, but legacy internal tools may still retain storage services.

### 21. Which code can be removed safely?

After reference updates and tests: external ingestion UI/API/commands/modules/env credentials; alphabet/mode UI and normal-flow endpoints; manual capture/countdown controls; simulated demo; proven unreferenced files/exports; placeholder reload/prepare endpoints; completed migration-only helpers; and legacy empty-dataset training scaffolds. Old database objects may be removed only through a new migration. Attribution, citations, licenses, and already-generated provenance reports must remain.

### 22. Which code must remain for the core process?

Camera permission/stream handling; stable browser MediaPipe inference; 33-pose + 21-left + 21-right normalization; exact V1 finite validation; privacy-preserving landmark-only API transport; payload ceiling/rate limiting; API→internal inference boundary; local ONNX Runtime loader; calibrated UNKNOWN decision; supported-key→Arabic mapping; direct automatic speech with failure isolation; health/readiness; and minimal accessible status/result controls. Internal authenticated model operations may remain isolated.

### 23. What currently prevents the exact target process from working?

- Manual start/finish and no segmentation/state machine.
- Detector loop lifecycle instability.
- Default mock inference and no production-oriented model package.
- Only a two-class smoke artifact.
- Database activation and inference loader can disagree.
- No Arabic mapping for smoke labels.
- Technical Top-K response rather than compact recognized/unknown output.
- No recognition-to-speech path or automatic playback.
- Mock never emits a true UNKNOWN decision.
- Static signs are rejected by a mandatory movement threshold.
- Pydantic silently ignores extra `raw_video`, `image`, or `audio` fields instead of rejecting them.
- Current speech provider produces deterministic experimental tones rather than intelligible Arabic speech.
- Existing Playwright tests explicitly exercise manual buttons and the smoke model.

## Dataset and model audit details

The native manifest contains 2,216 readable MP4s (222,795,265 bytes): 1,941 Diverse, 71 Letters, 130 Numbers, 15 Pronouns, and 59 Days/Months/Seasons. There are 2,145 word rows and 71 alphabet rows. The manifest checksum is `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`.

There are 1,591 valid non-empty normalized labels (1,559 word, 32 alphabet) and 15 invalid diacritic-only filenames. Ten binary-checksum groups contain 29 rows (19 duplicate extras), all with conflicting labels. The 2,197 checksum-keyed NPZ files validly cover all 2,216 rows; every validated sequence is finite `60×75×3`. Signer identity is unavailable.

Vocabulary tradeoff among unique valid word binaries:

| Minimum examples | Labels | Samples | Deterministic train/validation/test |
|---:|---:|---:|---:|
| 3 | 108 | 372 | 156 / 108 / 108 |
| 4 | 30 | 138 | 78 / 30 / 30 |
| 5 | 13 | 70 | 44 / 13 / 13 |
| 6 | 5 | 30 | 20 / 5 / 5 |

The minimum-five set has eight numeric labels and five lexical labels (`أَبٌ`, `أَحَبَّ`, `سُوقٌ`, `لَوَّنَ`, `نَادَى`). It is the preferred honest V1 scope because every class can have at least three training samples plus independent validation and test examples. It remains too small and signer-poor for a production-readiness claim.

## Implementation decision

The correction will use the native local dataset only, globally group duplicate checksums, exclude invalid/conflicting-quality rows, choose the documented minimum-five vocabulary unless benchmark evidence invalidates it, benchmark three compact architectures on identical splits, calibrate UNKNOWN with disjoint unsupported-label samples, export a complete ONNX package, and configure normal Docker inference to load it. The primary route will become a minimal anonymous state-machine-driven loop with one camera activation action and automatic speech for known results only.
