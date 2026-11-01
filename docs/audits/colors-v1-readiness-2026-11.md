# COLORS_V1 readiness — 2026-11-01

## Executive summary

An isolated dataset configuration, metadata/media validator, lineage and split-leakage
checks, conservative grouped split allocator, common numerical normalization fixture, and experimental decision/metrics helpers
are implemented. COLORS_V1 is **not ready to preprocess, train, evaluate, export, or
activate**. The actual color videos and eight color names are not provided. The existing
three-sign model remains active; no legacy data were used to train a new model.

## Legacy dataset and archive

The source contains 2,216 MP4 files and 2,216 manifest rows. A local snapshot was copied
to `~/Desktop/OpenSigne-Darija-Archive/`: 4,571 files totaling 432,303,475 bytes,
including 2,216 videos, dataset metadata and processed assets, model packages and
checkpoints, reports, dataset/model documentation, and selected ML source. Each source
file was SHA-256 hashed before copying; archive and source were rehashed and matched.
`archive-manifest.json` records source, destination, size, hash, type and dataset, and
`SHA256SUMS.txt` provides the checksums. Symbolic links were rejected; caches and
`.DS_Store` were excluded. Existing source files were not deleted or moved. The archive
root has mode `0700` and files mode `0600`; it contains potentially identifiable media.

Desktop's `FXICloudDriveDesktop` preference returned `0`, and no iCloud Desktop folder
was observed. Other third-party synchronization cannot be ruled out from these checks;
confirm local storage policy before sharing or additional copies. The current runtime
still references the legacy ONNX package, mapping and MediaPipe asset. The original
legacy dataset and outputs remain available to historical offline workflows. Any removal
requires a separate dependency review and explicit approval. The new validator refuses
the legacy dataset root or its ancestors/descendants, but cannot detect a legacy video
copied under another name elsewhere.

## Dataset architecture

`ml/configs/colors_v1.json` provides nine planning slots and ten variants. Both blue
variants map to `blue`; the remaining eight slots are explicitly placeholders and cannot
be used as labels until replaced. Video counts and performer profiles are not limits.
The [manifest schema](../../ml/datasets/colors_v1/manifest.schema.json) describes
video/label/variant, provenance, consent, review, signer, parent, lineage, path, hash,
and split metadata. The validator computes video hashes and media properties, decodes
with FFmpeg, reports unsupported/missing/corrupt files, duplicate content, unknown
labels and variants, parent mismatches/cycles, unregistered files and split collisions.
Synthetic appearances do not create independent signer evidence. The JSON schema is a
metadata reference; the implemented Python checks are the executable validation rules.

`media_review_ready` reflects only validation of supplied files and review/consent
metadata, not independent legal or linguistic verification. Preprocessing, training and
evaluation readiness are always false until their separate implementations and evidence
exist. Existing data and output ignore rules protect the designated private directories,
but files stored elsewhere need equivalent protection.

## Model, reliability, training and evaluation

The legacy model candidates include a compact bidirectional GRU, temporal-convolution
GRU and Transformer. A configurable bidirectional GRU is a reasonable *candidate* for a
small temporal baseline, not a selected or validated COLORS_V1 model. No color-specific
trainer, checkpoint workflow, calibration, ONNX export, model registry
or promotion process is implemented. Existing legacy trainers must not be used for this
experiment. The existing runtime's ONNX package and API have not changed.

The V1 feature contract is 60 x 75 x 3 normalized pose and hand landmarks, with missing
points masked and no face landmarks. The shared fixture verifies numerical Python/browser
normalization for one frame and missing points. It does **not** demonstrate extractor
parity: offline MediaPipe uses IMAGE mode and zero-pads short clips; the browser uses
VIDEO mode and repeats samples. Version and resolve that difference and validate real
recordings before training or deployment. The observed inference environment includes
OpenCV 5.0.0 and MediaPipe 0.10.35; the ML training environment lacks both, and a clean
pinned preprocessing environment is not yet established.

`ml/evaluation/colors_v1.py` implements semantic confusion counts, per-class precision,
recall and F1, accuracy, and known/unknown rejection rates for supplied observations.
It returns unavailable rates when denominators are absent. Its abstention function
returns unknown when no threshold is supplied and never calls a supplied threshold
calibrated. These helpers do not create evaluation reports or establish model quality.
No accuracy or real-camera claims can be made without real held-out data. Existing browser
segmentation/cooldown belongs to the legacy flow and is not evidence of color stability.

## How to prepare the videos

1. Replace the eight placeholders and their variants in `ml/configs/colors_v1.json`
   with the owner's actual labels; preserve blue's two-to-one semantic mapping.
2. Put authorized, reviewed videos in a private directory outside the legacy dataset.
   Supply a JSON-array manifest conforming to the schema and instructions in the
   [COLORS_V1 guide](../../ml/datasets/colors_v1/README.md). Keep parent/lineage and
   signer identity separate from character appearance.
3. Run the documented `python -m ml.datasets.colors_v1.validate` command with explicit
   manifest, video-root and private report paths. Review errors and warnings. The tool
   does not move or mutate videos; the report registers validated metadata and hashes.
4. **Blocked:** preprocessing, first training, evaluation, ONNX export and camera testing
   have no COLORS_V1 commands yet. They must be implemented and verified after resolving
   feature parity, environment reproducibility, grouped splitting, evaluation and explicit
   model promotion. Do not substitute legacy training commands.

## Validation and outstanding work

The baseline `make test-all` passed architecture 14, API 75, inference 29, ML 31, speech
9, and frontend 42 tests; Playwright 6 passed and 2 Docker-dependent cases skipped.
Compose configuration passed. The new focused ML tests and browser normalization fixture
pass locally. Docker daemon, physical camera, hosted CI and real COLORS_V1 data were not
available. The final `make test-all` passed architecture 14, API 75, inference 29, ML 40,
speech 9 and frontend 43 tests; Playwright had 6 passes and 2 Docker-dependent skips.
Ruff, MyPy, ESLint, TypeScript and Vite build passed. `make compose-check` and
`git diff --check` passed. An empty-input CLI run correctly reported zero videos and all
training-related readiness flags false. A prior intermediate run failed the documentation
link check while this report was still being written; the final rerun passed.

Remaining priorities: implement and test compatible preprocessing and pinned environment;
validate the proposed grouped splits and small-data readiness with real metadata; implement
color-specific training, reproducibility metadata, evaluation and calibration; implement
ONNX parity, explicit registration/promotion and readiness/UI integration; then validate
on real independent signers and unknown signs. No synthetic fixture demonstrates model
accuracy or sign-language correctness.
