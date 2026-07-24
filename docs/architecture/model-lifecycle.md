# Model Lifecycle

The active package is `artifacts/models/mosl-isolated-sign-v1/`.

It contains the ONNX graph, labels, Arabic label mapping, supported-sign metadata,
landmark schema, calibration thresholds, and checksums. Runtime services validate
the package before accepting traffic:

- ONNX checksum must match the manifest.
- Input shape must be `[batch, 60, 75, 3]`.
- Output shape must match the supported label count.
- Labels and Arabic mappings must be compatible.
- Confidence and margin thresholds control UNKNOWN rejection.

The package is read-only at runtime. This task must not retrain, regenerate, move,
or rename it.

## Local training workflow

Training uses only the native local dataset and its validated landmark caches. It does
not download or import data.

```bash
make ml-install
make ml-dataset-audit
make ml-validate-mosl-artifacts
make ml-train-v1
make ml-validate-model
```

`ml-dataset-audit` verifies all 2,216 manifest rows, binary checksums, cache shape and
finiteness, label counts, duplicate groups, deterministic splits, and the absence of
split leakage. Existing valid `60 x 75 x 3` NPZ caches are reused. `ml-preprocess-mosl`
is needed only for missing, invalid, or obsolete caches and uses the already-local
MediaPipe task asset.

`ml-train-v1` benchmarks on identical splits:

1. bidirectional GRU;
2. temporal convolution plus GRU;
3. lightweight Transformer encoder.

The run uses deterministic seeds, balanced sampling/class weighting, gradient clipping,
learning-rate scheduling, early stopping, recoverable checkpoints, and temporal/noise/
frame-drop/scale/translation augmentation. Horizontal mirroring is intentionally absent.

The active vocabulary is selected by a declared validation-only policy before test
metrics are revealed. The complete package is written to
`artifacts/models/mosl-isolated-sign-v1/`; all final metrics and limitations belong in
the active model card. The much older `mosl-word-smoke-v1` artifact is retained only as
technical provenance and cannot be activated by the normal user process.
