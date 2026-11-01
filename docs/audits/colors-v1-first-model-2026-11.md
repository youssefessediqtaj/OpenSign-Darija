# COLORS_V1 first experimental baseline — 2026-11-01

## Dataset integration

The user-supplied ZIP was copied into private, Git-ignored `ml/data/colors_v1/source_v1/`.
Its ten expected video entries were imported without changing source bytes; all ten SHA-256
values matched the supplied checksum list. The original ZIP SHA-256 is
`62eafb39b0466fdb961c89b9d3a5fb893c3aa49d9dcb6be94b214d052254e0b4`.
FFprobe and full FFmpeg decode found no errors or duplicate hashes. The private
`validation-media-v2.json` records full checksums, media properties and metadata. It is
not a tracked public artifact. All source files are H.264 in MOV/MP4-family containers.
The table below gives actual decoded frame counts and hand-detection suggestions, not
reviewed sign boundaries. The screenshots inspected contain Arabic text, logos and
player controls; the model receives landmarks rather than pixels, but those overlays and
rest periods may affect detection and segmentation.

| Source / variant | Duration (s) | FPS | Size | Decoded frames | Detected hand + shoulders / detector frames | First–last detection (s) |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| black(1).mov / `black_variant_01` | 7.60 | 38.91 | 1660×1526 | 295 | 37 / 115 | 2.20–4.28 |
| Bleu.mov / `blue_variant_01` | 8.58 | 42.41 | 1660×1526 | 364 | 26 / 137 | 3.03–4.47 |
| Bleu-2.mov / `blue_variant_02` | 6.99 | 45.00 | 1660×1526 | 315 | 20 / 122 | 1.48–2.50 |
| Brown.mov / `brown_variant_01` | 11.07 | 31.94 | 1660×1526 | 354 | 43 / 132 | 4.25–6.60 |
| Green.mov / `green_variant_01` | 8.99 | 40.78 | 1660×1526 | 367 | 28 / 139 | 2.30–4.00 |
| Orange.mov / `orange_variant_01` | 9.94 | 33.77 | 1660×1526 | 336 | 30 / 127 | 3.62–5.13 |
| Pink.mov / `pink_variant_01` | 5.08 | 45.92 | 1660×1526 | 236 | 34 / 91 | 1.15–2.90 |
| Red.mov / `red_variant_01` | 11.79 | 41.10 | 1660×1526 | 485 | 31 / 180 | 1.55–3.25 |
| White.mov / `white_variant_01` | 14.78 | 34.53 | 1184×1526 | 510 | 32 / 192 | 6.10–7.98 |
| yellow.mov / `yellow_variant_01` | 14.79 | 32.39 | 1184×1526 | 487 | 32 / 181 | 5.87–7.53 |

The configured semantic labels are black, blue, brown, green, orange, pink, red, white
and yellow. Both blue variants map to `blue`. There are ten declared source-lineage
groups, but signer identities and independence are unknown. The owner confirmed local
experimental training for all ten recordings. This is recorded separately from the
unknown original provenance, copyright and consent; all ten remain pending linguistic
and boundary review. It does not authorize redistribution.

## Preprocessing

The new `COLORS_V1_VIDEO_V1_EXPERIMENTAL` path processes decoded frames sequentially in
MediaPipe VIDEO mode at up to 24 fps using FFprobe timestamps and the same 0.5 detection
thresholds as the browser. It normalizes shoulders, preserves pose/left/right ordering,
excludes face features, filters frames without shoulders or a hand, then selects 60
frames by the browser's uniform rounding policy. Short sequences repeat samples and
saved source timestamps preserve repetition information. The legacy offline pipeline
continues to use IMAGE mode and zero-padding; neither it nor the active model was altered.

The shared Python/browser fixtures test numerical normalization, missing-landmark masks
and temporal index/sequence selection. These are component-level tests, not a comparison
of Python and browser detector outputs from the same decoded video. Platform-specific
MediaPipe runtimes, capture cadence, decoding, time origin and browser segmentation may
still differ. Real-camera and end-to-end parity are **not established**. The current
feature outputs use full clips with unreviewed detection intervals. Explicit start/end
metadata can be supplied later, but no automatically suggested interval is marked approved.
The current local environment used Python 3.12.2, MediaPipe 0.10.35 and OpenCV 5.0.0.93;
direct versions are recorded in `ml/requirements-colors-preprocess.txt`, but a clean,
fully locked preprocessing environment remains outstanding.

## Recognition baseline and reliability

A CPU nearest-template sequence matcher stores the ten normalized sequences, semantic
labels, variant IDs, feature version and manifest hash in
`artifacts/colors_v1/experimental/template-v1.npz`. It uses weighted squared distance
on jointly present landmarks; it is a simple diagnostic suited to very little data, not
an evidence-backed model selection. It returns `UNKNOWN_SIGN` unless a caller explicitly
supplies an uncalibrated maximum distance; it also exposes no-hand, insufficient-frame,
invalid-input and model-not-ready states. It is not mounted in the application.

As a wiring check only, each of the ten stored templates was matched against the same
stored package using an exact-zero threshold: 10/10 semantic and 10/10 variant self-matches.
This is tautological **in-sample self-matching, not accuracy**. The ten source recordings
provide at most one example per variant; independent known-sign validation and unknown
examples are absent. Independent accuracy, OOV rejection, calibration and real-camera
reliability are **NOT ESTABLISHED**. A local 100-call self-match timing measured mean
0.456 ms, P50 0.400 ms and P95 0.527 ms for the matching function only, excluding camera,
MediaPipe, network and UI; results are machine-specific.

## Training and ONNX

A separate one-epoch, seed-42 bidirectional GRU smoke experiment was fitted on the same
10 sequences, using nine semantic output classes. Its checkpoint, ONNX file and metadata
are isolated in `artifacts/colors_v1/experimental/gru-smoke-v1/`, with no overwrite of
legacy model assets. It records sample count, manifest hash, feature version, model
configuration, seed and dependency versions; its in-sample loss is a training diagnostic,
not generalization evidence. ONNX Runtime matched PyTorch with maximum absolute difference
`8.94e-08` for the tested batch-one and batch-two inputs. Warnings about tracing and GRU
batch-size portability remain; this does not establish broader runtime compatibility.
No color model is registered, exposed by the API, activated or shown as a real frontend
prediction. The public runtime continues using the protected legacy three-sign package.
The template baseline itself is not exported to ONNX.

## Evaluation, remaining work and expansion

The existing evaluation helpers support per-class precision, recall, F1 and confusion
counts, plus false acceptance, false rejection and unknown rejection for actual supplied
observations. No held-out report can be honestly produced from one source per variant.
Acquire independently recorded, rights-cleared, reviewed examples from multiple signers
and representative unfamiliar signs; review sign boundaries; validate browser/Python
feature parity; pin and verify the preprocessing environment; then split by signer and
lineage, calibrate on validation data and evaluate a separate held-out set. Registry,
promotion gates and frontend color states remain future work.

For generated derivatives, add private manifest records with parent `source_video_id`,
matching semantic label, sign variant and lineage, generation method, known signer identity,
rights/consent and `PENDING_REVIEW`; run the validator and arrange qualified sign-language
review before approved training. The validator supports this metadata, but there is no
complete derivative-copy importer yet. Appearance changes are not independent signers.
See the [dataset guide](../../ml/datasets/colors_v1/README.md) for actual commands.

## Verification

Before these changes, `make test-all` passed architecture 14, API 75, inference 29, ML
40, speech 9 and frontend 43 tests; Playwright passed 6 with 2 Docker-dependent skips.
The local dataset import, checksum verification, full decode, ten-video feature extraction,
template fitting, one-epoch smoke training and ONNX parity checks were executed. The final `make test-all` passed architecture 14, API 75, inference 29, ML 47,
speech 9 and frontend 45 tests; Playwright passed 6 with 2 Docker-dependent skips.
Ruff, MyPy, ESLint, TypeScript and Vite build also passed. `make compose-check` and
`git diff --check` passed; protected legacy model, mapping, dataset-manifest and
MediaPipe hashes matched previous values. Docker daemon and physical camera
were unavailable; no physical-camera or deployment claim is made.
