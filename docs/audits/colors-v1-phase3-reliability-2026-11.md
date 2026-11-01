# COLORS_V1 phase-three reliability — 2026-11-01

## Executive summary

Prepared a private review packet for all ten source videos, compared Python and browser
MediaPipe on identical local frames, registered the experimental GRU without activation,
and added explicitly enabled loopback-only inference and Vite development UI paths.
COLORS_V1 remains uncalibrated, unvalidated and inactive for ordinary users. The legacy
three-sign model and source videos remain unchanged. The local developer mode exposes
an unvalidated diagnostic candidate while its recognition decision remains UNKNOWN.

## Dataset quality and review

The private packet is `ml/data/colors_v1/review_phase3/index.html`; it contains ten
contact sheets, playable source links, approximate timestamps, detection counts and a
`review-draft.json`. Start/end values are empty. Technical and linguistic statuses are
separately `PENDING`, each with reviewer and date fields. The hand-detection first/last
values are only suggestions; detection gaps, pauses, transitions, occlusion and repeated
movements require review of the full video. In the blue-variant-two contact sheet, the
visible hand movement extends around the detection interval and rest/player overlays
appear before and after it, demonstrating why hand presence alone is not approval.

| Variant | First–last detected hand (s) | Valid/detector frames | Largest sampled detection gap (s) | Review |
| --- | --- | ---: | ---: | --- |
| `black_variant_01` | 2.20–4.28 | 37/115 | 0.15 | pending |
| `blue_variant_01` | 3.03–4.47 | 26/137 | 0.10 | pending |
| `blue_variant_02` | 1.48–2.50 | 20/122 | 0.10 | pending |
| `brown_variant_01` | 4.25–6.60 | 43/132 | 0.15 | pending |
| `green_variant_01` | 2.30–4.00 | 28/139 | 0.25 | pending |
| `orange_variant_01` | 3.62–5.13 | 30/127 | 0.10 | pending |
| `pink_variant_01` | 1.15–2.90 | 34/91 | 0.15 | pending |
| `red_variant_01` | 1.55–3.25 | 31/180 | 0.12 | pending |
| `white_variant_01` | 6.10–7.98 | 32/192 | 0.20 | pending |
| `yellow_variant_01` | 5.87–7.53 | 32/181 | 0.10 | pending |

Sampled gaps are from the already resampled valid landmarks, not a complete detector
failure timeline. No reviewer approved any interval or sign correctness. The extractor
accepts a separate source-hash-bound review file and uses bounds only after an explicit
technical approval with reviewer and date; linguistic approval is independent and needs
a qualified reviewer. Existing unreviewed feature files remain provisional and are not
silently overwritten. Rights, consent, signer identities and source provenance remain
unconfirmed; the owner authorized local experimental training only.

## Preprocessing compatibility

The [versioned feature contract](../architecture/colors-v1-feature-contract.md)
documents MediaPipe/model identity, timestamps, ordering, coordinate normalization,
mirroring, missing points, 60-frame sampling and dtype. Component fixtures check
normalization, masks, handedness, mirroring and short/long temporal sampling. Python and
Chromium 0.10.35 then processed the **same 12 local PNG frames** from one source with
matching synthetic 50 ms detector timestamps and the same task asset. Both detected pose
on 12/12 frames, right hand on 7/12, left hand on neither. For 1,629 common raw XYZ
coordinates, mean absolute difference was 0.00168, P95 0.00764 and max 0.05023. Each
produced seven valid source frames; resampled masks were identical. Final 60×75×3 tensors
had mean absolute difference 0.00416, P95 0.01647 and max 0.07111. No tolerance or
performance acceptance criterion has been established. These are measurements of one
short sequence, not proof of detector, browser-camera or end-to-end parity. Browser
capture cadence, decoder, detector implementation and segmentation still differ from
local preprocessing. Screenshots and raw landmarks remain private and Git-ignored.

## Recognition and registry

The new registry `artifacts/colors_v1/registry-gru-smoke-v1.json` records the existing
`colors_v1_gru_experimental` GRU: experimental, smoke-only, evaluation pending,
uncalibrated and inactive. Registration verifies ONNX input/output shape, label order,
artifact hashes, training-report metadata and feature version. Loading repeats these
checks. Its paths are local and must be re-registered elsewhere. The legacy
`mosl-isolated-sign-v1` model remains the active default and its protected hashes were
checked separately. There is no automatic promotion; a readiness helper checks for
protocol, compatibility, independent evaluation, calibration, rights/review and a named
approver but cannot activate anything or establish evidence by itself.

The experimental model uses the existing 60-frame payload and returns raw logits only
as an opt-in diagnostic candidate. Candidate labels are semantic colors; the model
predicts nine semantic classes and does not infer a blue sign variant. Decision remains
`UNKNOWN_SIGN`, with `UNCALIBRATED` metadata and no accepted semantic label. Missing
hands, insufficient usable frames, unavailable model, preprocessing and inference errors
have distinct states. Camera segmentation/cooldown remains the existing implementation;
no smoothing or threshold was invented. Template self-matches and the one-epoch training
smoke result are not recognition-accuracy evidence.

## Backend and frontend

The experimental FastAPI routes are not mounted by default. Both processes require an
explicit enable flag and a shared local token of at least 16 characters; they reject
non-loopback and forwarded requests. The inference process additionally requires the
private registry. A Vite development-only, loopback-only checkbox is disabled until a
token is supplied, and it does not appear in the production build. On selection the UI
shows only an explicitly unvalidated candidate and does not speak it. The API rejects
accepted color labels on this uncalibrated path. Default recognition and speech routes
are unchanged. The development token is browser-visible and is not production
authentication. Local deployment commands and constraints are in the
[COLORS_V1 guide](../../ml/datasets/colors_v1/README.md).

A real loopback API→inference request using the existing landmark fixture returned
UNKNOWN with no candidate by default; a diagnostic request returned an uncalibrated
candidate. Missing-token and forwarded requests returned 403. A separate headless browser
run used the existing synthetic camera fixture, the actual gateway and actual ONNX model;
it displayed the unvalidated candidate, returned HTTP 200 and had zero page errors. This
is not a physical-camera or real-sign accuracy test. Production bundle verification with
a synthetic token marker confirmed the experimental route, candidate text and marker
were absent. Physical-camera validation and Docker runtime remain unavailable.

## Evaluation and dataset expansion

Existing metrics cover class outcomes and known/unknown rejection. Held-out reports
require supplied signer, source-lineage and hash disjointness; metadata disjointness alone
is not independent verification. Calibration readiness now requires known and unknown
validation examples and disjoint training/validation/test metadata, but computes no
threshold. Promotion remains inactive until a documented protocol and human-approved
compatibility, rights/review, calibration and independent evaluation evidence exist.

For the next exploratory dataset, obtain repeated *original* performances covering all
ten variants from at least enough identifiable independent signers to populate separate
training, validation and test groups; three groups per class are an operational minimum
for the existing splitter, not a scientific sufficiency guarantee. Collect separate
unfamiliar signs and rest/invalid gestures, and record consent, rights, environment and
qualified review. A credible evaluation needs more independent signers and repetitions,
varied devices, lighting/backgrounds and separate real-camera testing; no fixed sample
count guarantees accuracy. Synthetic character replacements remain children of their
source with the same lineage, must start pending review, and cannot count as independent
signers. The new `extend_manifest` command validates and registers supplied private
additions without copying, approving or overwriting files.

## Testing and blockers

The pre-change `make test-all` passed architecture 14, API 75, inference 29, ML 47,
speech 9 and frontend 45; Playwright passed 6 with 2 Docker-dependent skips. The final `make test-all` passed architecture 14, API 78, inference 32, ML 52,
speech 9 and frontend 46; Playwright passed 6 with 2 Docker-dependent skips. A focused
frontend test/lint rerun passed after the final development-mode guard change. Focused
API and inference tests, Ruff and MyPy passed after the final token-comparison hardening. Ruff,
MyPy, ESLint, TypeScript, Vite build, `make compose-check` and `git diff --check` passed.
The ten imported video hashes and protected legacy model, mapping, manifest and MediaPipe
asset hashes were unchanged. A local Vite asset check returned HTTP 200 for the optional
task link and WASM path; that check is not physical-camera validation. Model calibration, independently
reviewed signs and boundaries, independent signer/OOV evaluation, live-camera parity,
production governance and explicit model approval remain blockers to validation or
activation.
