# Contribution architecture

The feature adds one optional boundary without changing the protected recognition
loop.

```text
Browser /contribute
  ├─ GET status, five signs, notice
  ├─ MediaPipe readiness (browser only)
  ├─ MediaRecorder preview (browser only)
  └─ explicit multipart POST
          ↓
FastAPI contribution route
  ├─ legal/configuration gate
  ├─ origin, rate, field and allowlist validation
  ├─ bounded FFprobe + FFmpeg decode validation
  ├─ contributor metadata → private SQLite
  └─ UUID video → private pending quarantine

Recognition → API → inference → speech remains independent
```

Frontend ownership is under `apps/web/src/features/contributions/`. Backend
ownership is under the API `api/v1`, `schemas`, `services`, `storage`, `core`, and
`cli` modules. Inference, speech, recognition state, ONNX runtime, and ML training
do not import the contribution feature.

SQLite is the smallest safe local concurrent metadata store. It uses WAL,
foreign keys, schema version `1`, a five-second busy timeout, `0700` directories,
and `0600` database/video files. Identifying contributor fields and technical
video metadata are stored in separate joined tables. Video keys contain only a
UUID. A private S3-compatible adapter is available for production deployments and
uses no public ACL or URL.

Storage and repository construction are lazy. Disabled collection does not touch
contribution storage. Contribution unavailability returns 503 only on contribution
surfaces; the core API health contract still checks only inference and speech.

Local storage uses a staging file, a SQLite transaction, an atomic filesystem
rename, and compensating cleanup if the database commit fails. The S3 adapter
uses a private staging object followed by a server-side copy to the quarantine
key. No contribution storage path is mounted into Nginx or the web container.
