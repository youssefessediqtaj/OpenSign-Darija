# Community Video Contribution Feature Report

Date: 2026-07-26<br>
Status: software complete and verified; public collection blocked pending legal and reference-media readiness

## Executive summary

OpenSign Darija now has a separate `/contribute` workflow for voluntary community
video contributions. It accepts only the five contribution signs listed below,
requires an adult contributor and explicit consent, records video without audio,
validates every upload before private quarantine, separates contributor details
from video metadata, and exposes review, withdrawal, deletion, retention, and
research-export operations through an operator CLI.

The feature is deliberately unavailable by default:

```dotenv
CONTRIBUTION_COLLECTION_ENABLED=false
CONTRIBUTION_REFERENCE_VIDEOS_APPROVED=false
```

Enabling the first switch alone is insufficient. The API also requires the
configured controller, purpose, recipients, collaborator-sharing position,
storage category, retention period, rights channel, CNDP procedure and real
reference, notice version, and approved reference media. Missing any requirement
keeps collection closed. Test-only values used in isolated integration tests are
not legal evidence and must never be copied into a deployment.

No contribution is sent to inference, added to a training dataset, or activated
as a model. The protected recognition flow remains:

```text
camera -> automatic detection -> 60x75x3 sequence -> API -> ONNX
       -> Arabic label or UNKNOWN -> speech for recognized labels only
```

## Architecture

### Runtime boundary

The contribution feature is a sibling of recognition, not an extension of its
request path:

```text
/contribute
  -> browser-local camera/readiness/recording
  -> POST /api/v1/contributions
  -> origin, CSRF and contribution-specific rate checks
  -> strict multipart parsing
  -> signature, ffprobe and full-decode validation
  -> private quarantine object + separate SQLite metadata
  -> operator review / rights / retention / export CLI

/recognize
  -> existing inference and speech services (unchanged)
```

The browser page fetches the server's status, exact sign catalog, and current
notice. When collection is closed, the page remains an informational preview:
PII fields, consent, camera, recording, and submission are disabled. A link from
the recognition workspace is the only integration into the protected UI flow.

The API uses a lazy contribution service so disabled deployments do not create a
database or storage directory merely by serving status and notice endpoints.
Storage or database failures are isolated from recognition health and requests.

### Data storage

SQLite schema version 1 keeps contributor PII in `contributors`, technical video
metadata in `videos`, and state transitions in `events`. Records use opaque UUIDs.
The public receipt omits names, city, age, file keys, hashes, and internal review
notes.

The local adapter uses:

- private directories with mode `0700`;
- private database and video files with mode `0600`;
- server-generated UUID object keys;
- a pending object followed by an atomic quarantine promotion;
- compensating deletion if metadata persistence fails.

The S3 adapter creates private objects without public URLs or public ACLs and
supports server-side encryption settings. The bucket policy, credentials,
encryption keys, backup policy, and lifecycle policy remain operator
responsibilities.

### Failure isolation and operating modes

- Default mode: status and notice are readable; contribution writes are closed.
- Legally incomplete mode: the feature remains closed even if its collection
  flag was set.
- Storage-unready mode: the status reports storage unavailable and writes remain
  closed.
- Ready mode: all legal fields, approved references, and private storage must be
  ready before the write path opens.
- Recognition: continues independently in every contribution mode.

### Created files

Frontend:

- `apps/web/public/reference-signs/posters/{salam,chokran,tabib,mosaada,maa}.svg`
- `apps/web/src/features/contributions/components/ConsentNotice.tsx`
- `apps/web/src/features/contributions/components/ContributionForm.tsx`
- `apps/web/src/features/contributions/components/ContributionPage.tsx`
- `apps/web/src/features/contributions/components/ContributionSuccess.tsx`
- `apps/web/src/features/contributions/components/ContributorCamera.tsx`
- `apps/web/src/features/contributions/components/RecordedVideoPreview.tsx`
- `apps/web/src/features/contributions/components/RecordingControls.tsx`
- `apps/web/src/features/contributions/components/RecordingReadiness.tsx`
- `apps/web/src/features/contributions/components/ReferenceSignVideo.tsx`
- `apps/web/src/features/contributions/domain/contribution-state.ts`
- `apps/web/src/features/contributions/domain/contribution-words.ts`
- `apps/web/src/features/contributions/domain/readiness-policy.ts`
- `apps/web/src/features/contributions/domain/recording-policy.ts`
- `apps/web/src/features/contributions/hooks/useContributionCamera.ts`
- `apps/web/src/features/contributions/hooks/useContributionRecording.ts`
- `apps/web/src/features/contributions/index.ts`
- `apps/web/src/features/contributions/services/contribution-api.service.ts`
- `apps/web/src/features/contributions/types/index.ts`
- four contribution unit/component test files under
  `apps/web/src/features/contributions/tests/`
- `apps/web/tests/e2e/contribution.spec.ts`

API and operations:

- `services/api/app/api/v1/contributions.py`
- `services/api/app/cli/{__init__,contributions}.py`
- `services/api/app/core/contribution_settings.py`
- `services/api/app/schemas/contributions.py`
- `services/api/app/services/contribution_catalog.py`
- `services/api/app/services/contribution_request_protection.py`
- `services/api/app/services/contribution_service.py`
- `services/api/app/services/contribution_validation.py`
- `services/api/app/storage/{__init__,contribution_repository,video_storage}.py`
- `services/api/tests/test_contributions.py`

Documentation:

- `docs/contributions/README.md`
- `docs/contributions/architecture.md`
- `docs/contributions/cndp-readiness-checklist.md`
- `docs/contributions/data-flow.md`
- `docs/contributions/data-subject-rights-process.md`
- `docs/contributions/model-development-boundary.md`
- `docs/contributions/privacy-notice-template.md`
- `docs/contributions/recording-quality.md`
- `docs/contributions/reference-video-provenance.md`
- `docs/contributions/retention-policy-template.md`
- `docs/contributions/review-process.md`
- `docs/contributions/security-review.md`
- `docs/contributions/testing.md`
- this report.

### Modified files

- `.agent/CONTINUITY.md`, `.env.example`, `.gitignore`, `Makefile`, and
  `docker-compose.yml`
- `apps/web/README.md`
- `apps/web/src/app/routes.tsx`
- `apps/web/src/features/recognition/components/RecognitionWorkspace.tsx`
- `apps/web/src/shared/api/client.ts`
- `docs/README.md` and `docs/operations/configuration.md`
- `infrastructure/nginx/default.conf`
- `services/api/Dockerfile`, `services/api/README.md`,
  `services/api/pyproject.toml`, and `services/api/requirements.lock`
- `services/api/app/api/v1/router.py` and `services/api/app/api/v1/system.py`
- `services/api/app/core/config.py` and `services/api/app/main.py`
- `services/api/app/services/recognition.py` and
  `services/api/app/services/request_protection.py`
- `services/api/tests/conftest.py`,
  `services/api/tests/test_recognition_modes.py`, and
  `services/api/tests/test_system.py`
- `tests/architecture/test_architecture_contracts.py`
- `tests/privacy/test_public_privacy_contract.py`

The changes in existing recognition service files are formatting or integration
boundary changes; recognition behavior and assets were not replaced.

## Legal-readiness

This repository provides a technical readiness gate and evidence checklist; it
does not assert that the project has completed a Moroccan legal filing.

The gate requires:

- real data-controller identity and contact details;
- a specific collection and research purpose;
- recipient categories and an explicit collaborator-sharing position;
- storage-location category and retention period;
- a rights-request channel and deletion instructions;
- a versioned consent/privacy notice;
- a confirmed CNDP procedure type and real procedure reference;
- approved, traceable reference-sign media.

The notice template covers the submitted data, video-content risk, purpose,
recipients, storage, retention, voluntariness, withdrawal and other rights, and
the fact that browser guidance is not face identification. Consent is an
unchecked direct affirmative action and the accepted notice version is stored
with the contribution.

The withdrawal flow prevents a contribution from appearing in later research
exports. Deletion records the lifecycle event and removes the private object.
Retention runs in report-only mode unless a real retention period is configured;
destructive execution requires explicit operator confirmation.

The CNDP readiness checklist is grounded in the official CNDP
[notification](https://www.cndp.ma/notifier-un-traitement/),
[conditions](https://www.cndp.ma/conditions/), and
[model-notice](https://www.cndp.ma/mentions-types/) pages. Those sources do not,
by themselves, determine which procedure applies to this project. Therefore:

- CNDP procedure type: **UNCONFIRMED**
- CNDP reference/receipt: **UNCONFIRMED**
- legal review and Moroccan Arabic notice approval: **UNCONFIRMED**
- authorization to open public collection: **not granted**

No fake CNDP number or inferred filing status appears in application defaults.

## Vocabulary

The contribution catalog is closed and exact:

| Key | Display label |
|---|---|
| `salam` | سلام |
| `chokran` | شكرا |
| `tabib` | طبيب |
| `mosaada` | مساعدة |
| `maa` | ماء |

These keys are contribution labels only. They do not alter the protected model
package's supported-sign vocabulary, class ordering, output labels, thresholds,
or speech normalization.

### Reference-media provenance

No approved demonstration MP4 is shipped. Public redistribution rights,
provenance, correct sign performance, and community validation could not be
established from repository evidence. Consequently,
`CONTRIBUTION_REFERENCE_VIDEOS_APPROVED` remains `false`, no video is represented
as an authoritative sign example, and public collection cannot open.

The five bundled SVGs are explicit “reference unavailable” disclosure posters,
not sign demonstrations:

| Poster | SHA-256 |
|---|---|
| `chokran.svg` | `f07a56655791319fa61d120f1735e9d39231189c45d5d32cb0d41243bed3f96d` |
| `maa.svg` | `7bc56e4464c402cf1477509dc69493ddee447e04c17e2f8a387814ce74b3c968` |
| `mosaada.svg` | `c31171ee63366a38e71178785b038808393cb400dd31c3b0e946e1c627ef0b0a` |
| `salam.svg` | `da0388fa73b846b8054245ebb596258a800974dddfbd47018ac73e3d923a7fcd` |
| `tabib.svg` | `38199ef65943f997ff28b0a8052c06b44896e5c1ac4d441b34a52c3f0eb0f164` |

Approved video hashes: **UNCONFIRMED; no approved videos are present**.

## Recording

The contribution page is mobile-first. On wider layouts, the selected reference
area is sticky on the right and the form, consent, camera, readiness, recording,
and preview workflow occupy the left. The reference remains first in document
order for small screens and assistive technology.

Camera access is explicit and scoped to this page. Audio is disabled in the
media constraint and recording path. Browser-local MediaPipe observations guide:

- face and upper-body visibility;
- at least one visible hand;
- approximate subject distance;
- stability;
- whether the scene is bright enough for reliable landmark detection;
- a short readiness dwell before recording.

This processing is transient in the browser and is not face recognition,
identity verification, biometric identification, emotion inference, or storage
of face templates.

The recorder prefers VP9 WebM, then VP8 WebM, and applies an automatic maximum
duration. Contributors can preview, retake, or submit. Camera tracks and object
URLs are cleaned up on retake, unmount, or completion. A regression test covers
the late-`onstop` lifecycle case so cleanup cannot create an unreclaimed preview
URL.

## Security/privacy

The server does not trust browser-provided filenames, MIME claims, dimensions,
duration, or sign values. It applies:

- exact multipart field allowlisting and bounded field lengths;
- the closed five-key contribution catalog;
- adult-only age validation;
- explicit consent validation;
- same-origin checks and a contribution-specific CSRF header;
- contribution-specific IP/request rate limits;
- maximum upload size;
- allowed WebM MIME values and EBML signature checks;
- bounded `ffprobe` checks for video-only expectations, duration, dimensions,
  frame rate, and codec/container properties;
- a bounded full `ffmpeg` decode to reject corrupt or truncated streams;
- SHA-256 content hashing;
- subprocess timeouts, argument arrays without a shell, and resource limits;
- UUID storage keys and PII-free application logs;
- a private quarantine/review lifecycle;
- an export that excludes rejected, withdrawn, deleted, or unapproved records;
- confirmation gates for approval, deletion, retention execution, and export.

Videos remain capable of revealing identity, home interiors, disability or
health context, location clues, and bystanders. The product copy discloses this
risk and asks users to record against a neutral background without other people.
The application neither promises anonymity nor describes the video as
non-personal data.

Known production limitations:

- the included rate limiter is process-local; a multi-instance deployment needs
  a shared edge or datastore-backed limiter;
- local filesystem permissions are access controls, not application-level
  encryption; disk, backup, and host controls must be supplied operationally;
- S3 privacy depends on verified bucket policy, IAM, encryption, lifecycle, and
  audit configuration;
- SQLite is suitable for the scoped deployment but needs a documented backup,
  restore, access, and migration process before production;
- automated content validation cannot prove that a contributor performed the
  intended sign or that no sensitive background information is visible;
- human review remains necessary, and reviewers must be authorized and trained.

## Tests

Final source-state command:

```text
make test-all && make architecture-check && make compose-check
```

Result: **exit 0**.

| Area | Exact final result |
|---|---|
| Architecture/contracts/privacy | 14 passed; the same suite passed again in the explicit architecture check |
| Privacy subset | 5 passed |
| API | 75 passed; Ruff clean; strict MyPy clean; 1 Starlette/httpx deprecation warning |
| API contribution tests | 21 passed (included in the API total) |
| Inference | 29 passed; Ruff clean; MyPy clean; 1 existing Starlette warning |
| ML | 31 passed; Ruff clean; 5 existing PyTorch/ONNX warnings |
| Speech | 9 passed; Ruff clean; MyPy clean |
| Frontend | 11 test files, 42 passed; ESLint clean; TypeScript/Vite production build passed |
| Playwright | 7 passed, 1 skipped |
| Compose validation | normal and ML profiles passed |

The passing Playwright cases include all three contribution cases and four
protected recognition cases, including two automatic speech cycles and UNKNOWN
without speech. The skipped case is the Docker real-video fake-camera scenario
because `PLAYWRIGHT_FAKE_CAMERA_VIDEO` was not supplied.

Additional evidence:

- the active model-package regression suite passed: **14 passed**;
- an isolated Docker project was enabled with unmistakably test-only legal
  sentinels and a disposable volume;
- a real 3-second, 320x240, 24 fps, VP9 WebM upload through Nginx returned 201;
- the receipt contained only the documented non-PII fields;
- receipt lookup returned 200 and an attempted public video route returned 404;
- runtime permissions were root directory `0700`, database `0600`, video `0600`;
- the isolated project and volume were destroyed after the successful run;
- the default Docker stack built from final source, started healthy, and kept
  contribution collection unavailable;
- the default runtime status reported the missing legal fields and storage as
  not checked;
- the default notice clearly stated that no contribution data are collected
  while readiness is incomplete;
- the protected recognition fixture through Nginx still returned recognized
  Arabic output (`أَحَبَّ`, confidence `0.9815`);
- final default-stack log inspection found no traceback, exception, error,
  critical, or panic entries.

The API image now includes FFmpeg. Its cached Docker layering separates OS/media
dependencies and pinned Python dependencies from application source. The first
uncached FFmpeg layer added approximately 429 MB of packages and took about 195
seconds in the observed environment; this is an accepted validation dependency
and a deployment-size tradeoff.

Manual in-app browser inspection could not run because no in-app browser session
was available. Standalone Playwright coverage passed, but a physical camera,
lighting variations, mobile devices, and human assessment of the five signs
remain **UNCONFIRMED**.

## Protected assets before/after

All protected assets have identical SHA-256 values before and after this work:

| Protected asset | Before | After |
|---|---|---|
| `artifacts/models/mosl-isolated-sign-v1/model.onnx` | `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54` | `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54` |
| `artifacts/models/mosl-isolated-sign-v1/checksums.json` | `707367e05abc7840a1330fecbc8fd7d946e6decb82a88ecd0d618197e01034f6` | `707367e05abc7840a1330fecbc8fd7d946e6decb82a88ecd0d618197e01034f6` |
| `artifacts/models/mosl-isolated-sign-v1/supported-signs.json` | `79fee1027ae43beed5e8c25956867184af3e4f092e1254d750daf2298c02a6da` | `79fee1027ae43beed5e8c25956867184af3e4f092e1254d750daf2298c02a6da` |
| `ml/data/external/mosl-video-dataset/manifests/videos.jsonl` | `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62` | `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62` |
| `ml/assets/mediapipe/holistic_landmarker.task` | `e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8` | `e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8` |

The dataset manifest remains 2,216 lines. No contribution was appended to it.
No ONNX file, checksum manifest, supported-sign definition, MediaPipe task, model
threshold, output vocabulary, or active-model pointer was modified.

## Remaining blockers

Public collection must remain closed until every item below is resolved and
evidenced:

1. A qualified Moroccan privacy/legal reviewer confirms the controller details,
   purpose, recipients, collaborator access, rights process, storage position,
   and retention period.
2. The correct CNDP procedure is confirmed and completed; a real reference or
   receipt is recorded.
3. The French/Arabic/Darija public notice and consent language receive qualified
   legal and community-language review.
4. Each of the five reference videos is created or sourced, sign-validated by
   qualified community reviewers, rights-cleared for public redistribution,
   hashed, and entered in the provenance register.
5. A privacy/security owner verifies production storage, IAM, encryption,
   backup, deletion, audit logging, incident response, and shared rate limiting.
6. Authorized reviewer identities, training, access controls, and escalation
   procedures are established.
7. Physical-camera tests cover supported browsers, mobile devices, permissions,
   lighting, framing, retake, track shutdown, accessibility, and the five exact
   signs. Manual visual inspection also remains outstanding.
8. Retention and rights workflows are rehearsed against a production-like
   environment with accountable owners.

Even after those blockers are resolved, collected videos stay in quarantine
until human approval. Research export is a deliberate, confirmed action. Dataset
ingestion, training, evaluation, model packaging, and activation remain separate
governed processes and were not triggered by this feature.

## Acceptance status

The scoped software, documentation, privacy controls, validation, review
operations, regression protection, and Docker integration are complete. The
criterion requiring an approved sign demonstration on the right side is
intentionally not represented as complete because no rights-cleared and
sign-validated reference video exists. The UI exposes that absence honestly, and
the fail-closed gate prevents public collection.

Related operating documents are indexed in
[`docs/contributions/README.md`](../contributions/README.md).
