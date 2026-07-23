# ONNX inference service

The internal FastAPI service receives only validated 60 × 75 × 3 landmark
sequences. It contains no MediaPipe, OpenCV, browser processing, training code,
speech call, database, or public host port.

Ownership:

- `api/`: health/readiness/model metadata and prediction route;
- `schemas/`: strict internal tensor request and prediction response;
- `model_package/`: checksums, labels, Arabic mapping, provenance, schema,
  calibration, ONNX shape/type validation, and fail-closed session loading;
- `runtime/`: startup state, warmup, bounded concurrency, and response timing;
- `core/`: package paths and runtime limits.

Active routes:

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /model`
- `POST /predict/word`

Environment:

- `MODEL_NAME`, `MODEL_VERSION`: active package identity.
- `MODEL_PATH`, `LABELS_PATH`, `SUPPORTED_SIGNS_PATH`, `CALIBRATION_PATH`: protected package files.
- `MODEL_CHECKSUM_REQUIRED`, `MODEL_MAX_SIZE_BYTES`: package integrity gates.
- `MODEL_WARMUP_ENABLED`, `INFERENCE_MAX_CONCURRENT_REQUESTS`, `ONNX_EXECUTION_PROVIDER`: runtime behavior.

Readiness is reported only after checksum/compatibility validation and optional
warmup. Calibrated maximum probability and margin determine known, uncertain, or
UNKNOWN; the public API keeps Top-K internal.

`requirements.lock` pins the tested production-container resolution. Offline ML
dependencies are deliberately absent from it.

Run `make test-inference` from the repository root.
