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

## Optional community contribution collection

All legal/controller fields are required for public submission. Empty values and
disabled reference-video approval keep the feature fail-closed.

| Variable | Purpose | Safe default |
| --- | --- | --- |
| `CONTRIBUTION_COLLECTION_ENABLED` | controller-approved public opening flag | `false` |
| `CONTRIBUTION_REFERENCE_VIDEOS_APPROVED` | provenance/sign/rights approval gate | `false` |
| `DATA_CONTROLLER_NAME` | legal controller identity | empty |
| `DATA_CONTROLLER_ADDRESS` | controller address | empty |
| `DATA_CONTROLLER_CONTACT` | controller contact | empty |
| `DATA_PROCESSING_PURPOSE` | exact approved purpose | empty |
| `DATA_RECIPIENT_CATEGORIES` | approved recipient categories | empty |
| `DATA_MODEL_COLLABORATOR_SHARING` | collaborator-sharing disclosure | empty |
| `DATA_STORAGE_LOCATION_CATEGORY` | storage/transfer category disclosure | empty |
| `DATA_RETENTION_DAYS` | approved positive retention duration | empty |
| `DATA_RIGHTS_CONTACT` | rights/deletion contact | empty |
| `CNDP_PROCEDURE_TYPE` | externally confirmed `declaration` or `prior_authorization` | empty |
| `CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE` | real CNDP evidence reference | empty |
| `CONSENT_NOTICE_VERSION` | approved notice version captured with consent | empty |
| `CONTRIBUTION_STORAGE_BACKEND` | `local` or private `s3` adapter | `local` |
| `CONTRIBUTION_STORAGE_ROOT` | private staging/quarantine root | `/app/var/contributions` |
| `CONTRIBUTION_DATABASE_PATH` | private SQLite metadata path | under storage root |
| `CONTRIBUTION_S3_*` | private bucket/prefix/endpoint/region/encryption | empty / `AES256` |
| `CONTRIBUTION_MAX_VIDEO_BYTES` | streamed file limit | `25000000` |
| `CONTRIBUTION_MIN_VIDEO_BYTES` | empty/truncated file floor | `1024` |
| `CONTRIBUTION_MIN_DURATION_SECONDS` | server duration floor | `2` |
| `CONTRIBUTION_MAX_DURATION_SECONDS` | server duration ceiling | `10` |
| `CONTRIBUTION_ALLOWED_VIDEO_TYPES` | declared browser WebM allowlist | WebM variants |
| `CONTRIBUTION_FFPROBE_PATH` | fixed metadata-probe executable | `ffprobe` |
| `CONTRIBUTION_FFMPEG_PATH` | fixed decode-check executable | `ffmpeg` |
| `CONTRIBUTION_PROBE_TIMEOUT_SECONDS` | bounded media command timeout | `12` |
| `CONTRIBUTION_RATE_LIMIT` | submissions/minute/client/process | `5` |
| `CONTRIBUTION_READINESS_DWELL_MS` | continuous browser readiness dwell | `1000` |
