# Configuration Reference

Configuration is owned by `.env.example`, `docker-compose.yml`, Vite build
variables, and each service's Pydantic settings. The browser must not receive
internal service URLs or model filesystem paths.

| Variable | Owner | Default | Required | Sensitive | Decision |
| --- | --- | --- | --- | --- | --- |
| `APP_NAME` | API metadata | `OpenSigne Darija` | no | no | keep |
| `APP_VERSION` | API metadata | `1.0.0` | no | no | keep |
| `NGINX_HOST_PORT` | Compose gateway | `8081` | no | no | keep |
| `VITE_API_BASE_URL` | Web build | empty same-origin | no | no | keep |
| `VITE_MEDIAPIPE_MODEL_PATH` | Web build | `/models/holistic_landmarker.task` | no | no | keep |
| `VITE_MEDIAPIPE_WASM_PATH` | Web build | `/mediapipe/wasm` | no | no | keep |
| `MEDIAPIPE_HOLISTIC_MODEL_PATH` | Web Docker mount | `ml/assets/mediapipe/holistic_landmarker.task` | yes in Docker | no | keep |
| `VITE_CAMERA_DEFAULT_WIDTH` | Web build | `1280` | no | no | keep |
| `VITE_CAMERA_DEFAULT_HEIGHT` | Web build | `720` | no | no | keep |
| `VITE_CAMERA_DEFAULT_FPS` | Web build | `30` | no | no | keep |
| `INFERENCE_SERVICE_URL` | API internal client | `http://inference:8001` in Docker | yes in Docker | no | keep |
| `INFERENCE_TIMEOUT_SECONDS` | API internal client | `3` | no | no | keep |
| `FEATURE_SCHEMA_VERSION` | Inference contract | `OPEN_SIGNE_LANDMARK_SCHEMA_V1` | no | no | keep |
| `RECOGNITION_MAX_PAYLOAD_BYTES` | API validation | `1500000` | no | no | keep |
| `RECOGNITION_MIN_DURATION_MS` | API validation | `500` | no | no | keep |
| `RECOGNITION_MAX_DURATION_MS` | API validation | `8000` | no | no | keep |
| `RECOGNITION_RATE_LIMIT` | API validation | `30` | no | no | keep |
| `RECOGNITION_MIN_USABLE_FRAMES` | API validation | `12` | no | no | keep |
| `RECOGNITION_MIN_HAND_RATIO` | API validation | `0.35` | no | no | keep |
| `RECOGNITION_MAX_MISSING_FRAME_RATIO` | API validation | `0.50` | no | no | keep |
| `RECOGNITION_MIN_DYNAMIC_MOVEMENT` | API validation | `0.04` | no | no | keep |
| `MODEL_NAME` | Inference package | `mosl-isolated-sign-v1` | no | no | keep |
| `MODEL_VERSION` | Inference package | `1.0.0` | no | no | keep |
| `MODEL_PATH` | Inference package | `/workspace/artifacts/models/.../model.onnx` | yes in Docker | no | keep internal |
| `LABELS_PATH` | Inference package | `/workspace/artifacts/models/.../labels.json` | yes in Docker | no | keep internal |
| `SUPPORTED_SIGNS_PATH` | API/inference package | `/workspace/artifacts/models/.../supported-signs.json` | yes in Docker | no | keep internal |
| `CALIBRATION_PATH` | Inference package | `/workspace/artifacts/models/.../confidence-calibration.json` | yes in Docker | no | keep internal |
| `MODEL_CHECKSUM_REQUIRED` | Inference package | `true` | no | no | keep |
| `MODEL_MAX_SIZE_BYTES` | Inference package | `50000000` | no | no | keep |
| `MODEL_WARMUP_ENABLED` | Inference runtime | `true` | no | no | keep |
| `ONNX_EXECUTION_PROVIDER` | Inference runtime | `CPUExecutionProvider` | no | no | keep |
| `INFERENCE_MAX_CONCURRENT_REQUESTS` | Inference runtime | `4` | no | no | keep |
| `SPEECH_SERVICE_URL` | API internal client | `http://speech:8010` in Docker | yes in Docker | no | keep |
| `SPEECH_MODE` | Speech runtime | `local` | no | no | keep |
| `SPEECH_MODEL_VERSION` | Speech runtime | `opensign-system-arabic-v1` | no | no | keep |
| `SPEECH_GENERATION_TIMEOUT_SECONDS` | API/speech timeout | `20` | no | no | keep |
| `SPEECH_MAX_TEXT_LENGTH` | Speech validation | `500` | no | no | keep |
| `SPEECH_MAX_SENTENCES` | Speech validation | `5` | no | no | keep |
| `SPEECH_MAX_CONCURRENT_GENERATIONS` | Speech runtime | `2` | no | no | keep |

Machine-readable audit: `artifacts/reports/environment-variable-audit.json`.
