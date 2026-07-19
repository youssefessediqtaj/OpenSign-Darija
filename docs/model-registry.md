# Model Registry

Backend model versions live in `model_versions`.

Important fields:

- name and semantic version
- status
- architecture
- dataset version
- feature schema version
- labels
- metrics
- thresholds
- calibration
- artifact path
- checksum
- active flag

Model artifacts are private and belong in `opensign-model-artifacts`.

## Smoke Models

`VALIDATED_SMOKE` is reserved for end-to-end development validation artifacts. A smoke
model may prove that schema, ONNX loading, API routing and frontend capture work
together, but it is not a production model and its metrics must not be presented as
dataset performance.

Smoke activation is blocked by default. It is allowed only when:

- `APP_ENV=development`
- `ALLOW_SMOKE_MODEL_ACTIVATION=true`
- the model has an artifact path and checksum

When activated under that guard, the model remains visibly `VALIDATED_SMOKE` instead
of being promoted to `ACTIVE`.

## MoSL Smoke Registration

The MoSL word smoke artifact is validated and registered separately from production
models:

```bash
make ml-validate-word-smoke-model
make ml-register-word-smoke-model
```

For Docker real-mode smoke validation, mount/use:

```bash
INFERENCE_MODE=real
FEATURE_SCHEMA_VERSION=OPEN_SIGNE_LANDMARK_SCHEMA_V1
MODEL_NAME=mosl-word-smoke-v1
MODEL_VERSION=0.1.0-smoke
MODEL_PATH=/workspace/artifacts/models/mosl-word-smoke-v1/model.onnx
LABELS_PATH=/workspace/artifacts/models/mosl-word-smoke-v1/labels.json
ALLOW_SMOKE_MODEL_ACTIVATION=true
```
