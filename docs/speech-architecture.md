# Speech Architecture

Phase 6 adds an internal speech path:

```text
Frontend -> Backend API -> Speech service -> MinIO signed URL
```

The browser never calls the internal speech service directly. The API verifies message ownership, finalization, risk confirmation, voice status, speed and format before synthesis.

Current MVP synthesis is local and deterministic through `local-darija`. It is an experimental non-human synthetic voice used to validate the private audio pipeline. No voice cloning, microphone access, third-party TTS API, or automatic playback is used.

The synchronous path is allowed for short messages. The database model stores statuses compatible with asynchronous workers: `CREATED`, `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `EXPIRED`, `DELETED`.
