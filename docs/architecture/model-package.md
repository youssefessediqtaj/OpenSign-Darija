# Model Package

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
