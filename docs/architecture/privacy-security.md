# Privacy And Security

The public recognition page is anonymous and landmark-only.

The browser must not send raw video, images, canvas screenshots, microphone audio,
base64 camera payloads, persistent visitor IDs, arbitrary text-to-speech input, or
direct requests to internal inference or speech services.

The API validates closed schemas and returns compact known/UNKNOWN decisions. It
does not persist recognition records and does not mount auth, admin, dataset, or
database routes. Speech is requested only for API-verified supported sign keys.

Nginx is the public boundary on port `8081`; internal service ports are not exposed
to the host.

## Camera and landmark privacy

The live camera stream and MediaPipe pixel processing stay in the browser. The core API
receives only a transient normalized landmark sequence, presence masks, boundary
metadata, and aggregate quality values. It does not persist the request or prediction.

Landmarks still describe a person's body motion and should be treated as sensitive in
transport and logs even though they are not raw pixels. The runtime does not turn camera
sessions into dataset contributions and has no public contribution/import workflow.

## Security controls

- anonymous recognition with no public account/token surface;
- Nginx same-origin API, security headers, 2 MB gateway ceiling, camera self-only, and
  microphone denied;
- strict Pydantic `extra=forbid`, exact V1 shape, finite/range checks, size ceiling, and
  in-memory anonymous rate limit;
- browser sends landmarks only and never reaches private inference/speech services;
- real inference fails readiness on package/checksum/schema/shape/label/calibration
  inconsistency and never silently falls back to mock;
- supported label keys, not arbitrary browser text, drive speech;
- offline speech uses direct subprocess arguments without a shell and ephemeral WAV
  files;
- no runtime DB, Redis, MinIO, credentials, migrations, external dataset or TTS request.

Do not log full landmark tensors, audio/base64, local video paths, or sensitive camera
details. OpenSigne Darija is a research prototype, not a certified interpreter.
