# Inference Service

The inference service supports:

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /model`
- `POST /predict`
- `POST /predict/mock`
- `POST /admin/reload-model`

`INFERENCE_MODE=mock` is for development and tests. `INFERENCE_MODE=real` requires a local ONNX model path, labels, thresholds, and calibration files. If the real model is absent, `/ready` returns 503 and predictions fail instead of returning fake results.
