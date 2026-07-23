# Core architecture

OpenSigne Darija is a deliberately small stateless runtime:

```text
browser camera
  -> local MediaPipe Holistic landmarks
  -> automatic isolated-sign segmenter
  -> public FastAPI word endpoint
  -> private ONNX Runtime service
  -> supported Arabic label or UNKNOWN
  -> private offline speech service for a known label
  -> browser playback, cooldown, next sign
```

Nginx exposes the React application and `/api/`. Inference and speech are container-only
services. The core API boots without PostgreSQL, Redis, MinIO, migrations, seed data, or
authentication. Historical persistence modules remain unmounted on disk solely because
deleting old tables/workflows without a migration would be destructive.

The active runtime services are web, API, inference, speech, and Nginx. The optional
`ml` Compose profile runs a one-shot audit of data already present locally; it performs
no runtime package or dataset download.

The model package on disk is the sole activation source. API and inference read the same
supported-sign mapping, and inference validates package checksums, schema, ONNX shapes,
labels, Arabic mappings, and calibration before readiness. There is no public registry
or model selector that can diverge from loaded weights.
