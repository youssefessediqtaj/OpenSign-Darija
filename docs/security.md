# Core security controls

- anonymous recognition with no public account/token surface;
- Nginx same-origin API, security headers, 2 MB gateway ceiling, camera self-only, and
  microphone denied;
- strict Pydantic `extra=forbid`, exact V1 shape, finite/range checks, size ceiling, and
  in-memory anonymous rate limit;
- browser sends landmarks only and never reaches private inference/speech services;
- real inference fails readiness on package/checksum/schema/shape/label/calibration
  inconsistency and never silently falls back to mock;
- supported label keys—not arbitrary browser text—drive speech;
- offline speech uses direct subprocess arguments without a shell and ephemeral WAV files;
- no runtime DB, Redis, MinIO, credentials, migrations, external dataset or TTS request.

Do not log full landmark tensors, audio/base64, local video paths, or sensitive camera
details. OpenSigne Darija is a research prototype, not a certified interpreter.
