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

Nginx exposes the React application and `/api/`. Inference and speech are
container-only services. The API has no PostgreSQL, Redis, MinIO, migration,
seed, authentication, storage, or repository layer.

The active runtime services are web, API, inference, speech, and Nginx. The optional
`ml` Compose profile runs a one-shot audit of data already present locally; it performs
no runtime package or dataset download.

Source dependencies follow one direction:

```text
web app → recognition feature → shared browser API/UI
public API routes → services → typed internal clients
inference routes → bounded runtime → checksum-validated model package
speech routes → synthesis service → one local system-speech provider
offline ML stages → immutable model package → inference reads package
```

Automated boundary tests reject browser internal-service URLs, cross-service
Python imports, runtime ML imports, stateful API dependencies, raw-media contract
fields, non-gateway host ports, and drift in the 60 × 75 × 3 schema.

The model package on disk is the sole activation source. API and inference read the same
supported-sign mapping, and inference validates package checksums, schema, ONNX shapes,
labels, Arabic mappings, and calibration before readiness. There is no public registry
or model selector that can diverge from loaded weights.
