# COLORS_V1 experimental dataset

The current private import contains ten source recordings, nine semantic colors and ten
variants. `Bleu.mov` and `Bleu-2.mov` retain separate variant IDs and share semantic label
`blue`. The owner confirmed **local experimental training** on these ten clips; original
source, copyright, consent, signer identity and linguistic review remain unverified.
This does not authorize publication or redistribution. The legacy three-sign model is
still the active runtime. Neither experimental model below is deployed or validated.

## Import and inspect

The original ZIP remains in the user's Downloads folder. Current private files are under
Git-ignored `ml/data/colors_v1/source_v1/`; checksum-verified originals are never modified.
To import a fresh copy to a **new** private destination, run the importer with the ZIP and
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
  --feature-dir ml/data/colors_v1/features_v1 \
  --output artifacts/colors_v1/experimental/new-template.npz --allow-pending-review
```

A separate small bidirectional-GRU smoke trainer consumes an experimental template
package, saves a new checkpoint, exports ONNX, and checks one-input numerical parity:

```bash
ml/.venv/bin/python -m ml.datasets.colors_v1.train_smoke \
  --package artifacts/colors_v1/experimental/template-v1.npz \
  --output-dir artifacts/colors_v1/experimental/new-gru-smoke --epochs 1 --seed 42
```

The current one-epoch run is a pipeline smoke test on the same ten samples, **not an
independent validation or a calibrated model**. Output directories must be new. The GRU is registered as experimental and inactive; the local-only diagnostic API is
opt-in and neither artifact is activated for ordinary users. An eventual release
needs rights and linguistic review, validated sign intervals, matched camera preprocessing,
independent signer-disjoint data, unknown-sign calibration, held-out evaluation, package
validation and explicit activation. See the
[experiment report](../../../docs/audits/colors-v1-first-model-2026-11.md).

## Phase-three review and local integration

A private review packet is available at `ml/data/colors_v1/review_phase3/index.html`;
its `review-draft.json` contains ten pending technical and linguistic decisions. The
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

The optional API/inference routes are mounted only if `COLORS_EXPERIMENTAL_ENABLED=true`
and `COLORS_EXPERIMENTAL_TOKEN` is at least 16 characters. Bind both Uvicorn processes
to `127.0.0.1`, configure the inference process with `COLORS_EXPERIMENTAL_REGISTRY` set
to the absolute private registry path, and configure the API's `INFERENCE_SERVICE_URL` to
that loopback inference server. Forwarded requests and non-loopback clients are rejected.
The default Docker configuration does not enable these routes. For the Vite development
server only, set `VITE_COLORS_EXPERIMENTAL_TOKEN` to the same local token and
`VITE_API_BASE_URL=http://127.0.0.1:8000`; bind Vite to loopback and open
`http://localhost:5173` using `npm run dev -- --host 127.0.0.1` from `apps/web`.
The token is visible to the local browser and is not a production
secret or a substitute for authentication. The developer must explicitly select the
experimental checkbox before starting the camera. A candidate is labeled unvalidated,
never spoken and never promoted to an accepted color. A production build excludes the
experimental route and token marker. The default legacy recognition path is unchanged.
Live camera use also requires locally served MediaPipe task and WASM assets; camera
permissions, assets and the full physical-camera path remain to be verified on-device.

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
