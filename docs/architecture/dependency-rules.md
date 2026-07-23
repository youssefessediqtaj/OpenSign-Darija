# Dependency Rules

The runtime is deliberately narrow.

| Owner | May depend on | Must not contain |
| --- | --- | --- |
| Frontend | Same-origin public API routes, browser MediaPipe, camera APIs | Direct inference/speech calls, raw media upload, training code |
| API | Strict schemas, typed inference/speech clients, protected model vocabulary | ONNX Runtime, MediaPipe, SQLAlchemy, Redis, MinIO, auth/admin code |
| Inference | ONNX Runtime, NumPy, protected model package | Speech calls, browser/media processing, training code |
| Speech | Local system TTS, strict synthesis schemas | Recognition logic, model inference, browser routes |
| ML | Local dataset, preprocessing, training, evaluation, export | Runtime startup dependency |
| Nginx | Public HTTP gateway | Product logic |

Architecture tests fail on forbidden public browser URLs, raw-media fields,
database/auth dependencies in the active API, and cross-layer import drift.
