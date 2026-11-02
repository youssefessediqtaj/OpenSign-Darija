# COLORS_V1 experimental dataset

The current private dataset contains ten cleaned recordings, nine semantic colors and ten
variants. `08_bleu_1.mp4` and `09_bleu_2.mp4` map to separate variants of `blue`.
The owner supplied the cleaned replacements and requested local feature regeneration
and a smoke test; original source, copyright, consent, signer identity, equivalence to
earlier performances and linguistic review remain unverified. This does not authorize
publication or redistribution. See the [clean-video update](../../../docs/audits/colors-v1-clean-video-update-2026-11.md).
The local diagnostic runtime still uses the historical smoke model, not a model trained
on the cleaned videos by default; its fingerprint mismatch makes it unavailable. A
separate clean-data learning diagnostic can be selected explicitly as documented in the
[learning report](../../../docs/audits/colors-v1-clean-model-training-2026-11.md).
No color model is validated for recognition.

## Import and inspect

The original ZIP remains in the user's Downloads folder. Current private files are under
Git-ignored `ml/data/colors_v1/source_v1/`. The original manifest and checksums are
preserved in `ml/data/colors_v1/history/source-v1-before-cleaning/`; they describe the
old files and must not be used as the active dataset. The archive importer below is for
the historical ZIP, not the cleaned recordings. To import it to a **new** private destination, run the importer with the ZIP and
destination arguments. `--local-training-permitted` may be used only when the owner has
confirmed that permission. Existing directories are never overwritten:

```bash
services/inference/.venv/bin/python -m ml.datasets.colors_v1.import_sources \
  /path/to/OpenSigne_COLORS_V1_10_source_videos.zip /private/new-destination \
  --local-training-permitted
```

This importer targets the exact ten-file source package. Future derivative videos need a
separate manifest entry conforming to [the manifest schema](manifest.schema.json), with
source video ID, same lineage and semantic/variant, transformation type, independent
signer ID if actually known, rights, consent and linguistic review. `validate` can inspect
such expanded manifests, but a general derivative-copy importer is **not implemented**.
Do not equate generated appearances with new independent signers. Keep parent and derived
videos in the same split; qualified linguistic review remains necessary.

```bash
services/inference/.venv/bin/python -m ml.datasets.colors_v1.validate \
  --config ml/configs/colors_v1.json \
  --manifest ml/data/colors_v1/source_v1/manifest.json \
  --video-root ml/data/colors_v1/source_v1 \
  --report ml/data/colors_v1/new-validation.json
```

Reports are created owner-only outside the video directory and never overwritten. The
validator checks media decoding, labels, variants, hashes, source relationships, review,
consent and known split collisions. The current sources have pending review and rights,
so `media_review_ready`, `preprocessing_ready`, `training_ready` and `evaluation_ready`
remain false. Optional `--split-report /private/new-splits.json` requires approved records
and known signer identities; it cannot establish that supplied identities are correct.

## Experimental features

`COLORS_V1_VIDEO_V1_EXPERIMENTAL` uses MediaPipe Holistic VIDEO mode, CPU, 0.5 pose/hand
confidence, 24 fps maximum detector cadence, unmirrored frames and strictly increasing
millisecond timestamps derived from decoded video timestamps. It retains 33 pose, 21 left
hand and 21 right hand points; shoulder-center and scale normalization, missing-point mask
and six-decimal rounding follow the browser contract. Frames with shoulders and a hand
are uniformly selected into 60 positions with the same nonnegative rounding as the browser;
short clips repeat frames, not zeros. Presence masks identify missing landmarks; the saved
source timestamps expose repeated frames. Face features are not included. No manual source
intervals were approved, so current extracted features use full clips and automatically
observed hand intervals are *suggestions*, not reviewed boundaries. `sign_start_time`, `sign_end_time`, `segmentation_method`, and separate technical and
linguistic statuses in the source-hash-bound review file record later human review. Do not assume a detected hand equals the entire sign.

The import environment has Python 3.12, MediaPipe 0.10.35 and OpenCV 5.0.0.93 in the
inference venv, while the ML venv supplies PyTorch/ONNX. This is a recorded local setup,
the direct versions are listed in `ml/requirements-colors-preprocess.txt`, but transitive
dependencies and FFmpeg are not locked or verified in a clean environment. FFmpeg and
FFprobe are required. To process one video
into a **new** feature directory:

```bash
services/inference/.venv/bin/python -m ml.datasets.colors_v1.preprocess \
  --manifest ml/data/colors_v1/source_v1/manifest.json \
  --video-root ml/data/colors_v1/source_v1 \
  --output-dir ml/data/colors_v1/new-features --video-id blue_variant_01
```

Outputs are private and cannot overwrite existing feature files. A shared Python/browser
sequence fixture tests selection and normalization. Python and browser use different
MediaPipe runtimes, decoding and capture cadence, and the browser uses automatic sign
segmentation. End-to-end detector equivalence and real-camera transfer are **unverified**.

## Baseline and smoke training

The sequence-template baseline fits the ten experimental features to a private package.
It stores templates, labels, variant IDs, feature version and manifest hash; it does not
produce ONNX. A missing distance threshold makes predictions `UNKNOWN_SIGN`. A manually
supplied threshold is uncalibrated, so do not use it for real decisions. Supply the actual
source-frame count to its inference interface: a repeated 60-frame tensor alone cannot
prove that enough distinct source frames were observed. The command below
explicitly permits pending linguistic review **only for local experimental work**; omit
the flag for a reviewed-only run:

```bash
ml/.venv/bin/python -m ml.datasets.colors_v1.baseline \
  --manifest ml/data/colors_v1/source_v1/manifest.json \
  --feature-dir ml/data/colors_v1/features_clean_v2 \
  --output artifacts/colors_v1/experimental/new-template-clean-v2.npz --allow-pending-review
```

A separate small bidirectional-GRU smoke trainer consumes an experimental template
package, saves a new checkpoint, exports ONNX, and checks one-input numerical parity:

```bash
ml/.venv/bin/python -m ml.datasets.colors_v1.train_smoke \
  --package artifacts/colors_v1/experimental/new-template-clean-v2.npz \
  --output-dir artifacts/colors_v1/experimental/new-gru-smoke-clean-v2 --epochs 1 --seed 42
```

The earlier one-epoch run is a pipeline smoke test on the earlier ten samples, **not an
independent validation or a calibrated model**. Output directories must be new. The GRU is registered as experimental and inactive; the local-only diagnostic API is
opt-in and neither artifact is activated for ordinary users. An eventual release
needs rights and linguistic review, validated sign intervals, matched camera preprocessing,
independent signer-disjoint data, unknown-sign calibration, held-out evaluation, package
validation and explicit activation. See the
[experiment report](../../../docs/audits/colors-v1-first-model-2026-11.md).

## Phase-three review and local integration

A private review packet for the cleaned recordings is available at
`ml/data/colors_v1/review_phase3/index.html`; its `review-draft.json` contains ten
pending technical and linguistic decisions. Video and preview URLs include source
hashes so browsers do not reuse older cached content. The previous packet is preserved
under `ml/data/colors_v1/history/review_phase3-before-cleaning/`. The
contact sheets and hand-detection times are approximate prompts, not approved boundaries.
Edit a copy of that JSON after review, recording technical start/end, reviewer and ISO
review date separately from a qualified linguistic review. Pass it to preprocessing via
`--review /private/path/review.json`; only source-hash-matching, technically approved
boundaries are used. A new output directory is required. Source files and earlier reviews
are never overwritten. See the [feature contract](../../../docs/architecture/colors-v1-feature-contract.md).

For new original or synthetic samples, place authorized media in the private source tree,
prepare a JSON array of additions with parent, lineage, transformation, rights, consent
and `PENDING_REVIEW`, then run `python -m ml.datasets.colors_v1.extend_manifest` with
`--base`, `--additions`, `--video-root`, and a new `--output` outside the source tree.
The tool checks the combined dataset and writes a separate owner-only manifest; it does
not copy media or approve reviews.

A local registry entry was created at `artifacts/colors_v1/registry-gru-smoke-v1.json`.
It uses absolute local paths and must be regenerated with `python -m
ml.datasets.colors_v1.registry --model-dir <dir> --output <new-file>` on another machine.
Registration verifies hashes, label order and ONNX shapes and does not activate the model.

The local Docker development stack runs color diagnostics with `make up` (or `make dev`)
and serves `http://localhost:8081`. `docker-compose.local.yml` binds the host port to
127.0.0.1, enables the color-only routes, mounts the registry read-only, and trusts only
its dedicated internal Docker subnet plus a local diagnostic token. The token is visible
in the browser and is not a production secret or authentication. The same-origin browser
interface never sends a legacy word request or speaks candidates. Missing artifacts show
`MODEL_NOT_READY`. The registry's absolute paths are resolved against the local registry
mount when the original host paths are unavailable, with all hashes checked again.

Standard `docker-compose.yml` leaves the experimental endpoints disabled; do not use the
local override on a production or shared host. Color predictions remain uncalibrated,
non-validated diagnostics; no promotion or speech is enabled. The current smoke checkpoint
was trained using provisional features from the earlier ten color clips, whose technical and
linguistic reviews are still pending. It does not establish approved derived features,
rights or consent, or scientific recognition accuracy.

For a local Vite session using the real detector, from the repository root create the
optional asset link below (only if that path does not already exist), and set the WASM
path in the Vite environment before starting it:

```bash
mkdir -p apps/web/public/models
ln -s ../../../../ml/assets/mediapipe/holistic_landmarker.task apps/web/public/models/holistic_landmarker.task
export VITE_MEDIAPIPE_WASM_PATH=/node_modules/@mediapipe/tasks-vision/wasm
```

The linked model and WASM URLs both returned HTTP 200 in a local Vite check. Remove the
link when the local session is no longer needed. This does not establish camera or
recognition performance.
