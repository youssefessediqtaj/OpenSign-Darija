# Internal inference service

The inference container is not exposed by Nginx. Its core routes are:

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /model`
- `POST /predict/word`

Normal Docker configuration is `INFERENCE_MODE=real`. Startup loads the complete local
`mosl-isolated-sign-v1` package and fails readiness when its ONNX file, checksum,
`60 x 75 x 3` input, output class count, labels, Arabic mappings, or calibration sidecar
is absent or inconsistent. There is no automatic fallback to fake predictions.

The API is the only caller. The browser cannot reach this service and receives only the
compact recognized/UNKNOWN result after API quality checks.
