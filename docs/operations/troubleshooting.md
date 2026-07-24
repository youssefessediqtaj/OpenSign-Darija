# Troubleshooting

Use these checks after Docker startup, browser testing, or a failed regression run. They
are intentionally scoped to the current stateless recognition runtime.

## API logs

```bash
docker compose logs api
```

Expect only health/version, `/recognitions/word`, and `/speech/sign` traffic. Block on:

- tracebacks;
- DB, Redis, or MinIO connection attempts;
- legacy routes returning non-404 responses;
- payload logging;
- repeated speech for one segment;
- inference or speech dependency failures.

## Inference logs

```bash
docker compose logs -f inference
```

Block on model loading errors, ONNX Runtime errors, checksum errors, schema mismatch,
prediction exceptions, repeated reloads, request latency spikes, or accidental landmark
dumps. Landmark arrays must never be logged.

## Browser console and network

Verify:

- no uncaught React error, rejected promise, or duplicate detector animation loop;
- no MediaPipe model/WASM CDN request;
- no authentication redirect or token/local-storage requirement;
- no request to inference, model registry, alphabet, dataset import, or external source;
- recognition and known-only speech requests return successfully;
- UNKNOWN causes no speech request;
- request bodies contain landmarks only, never video/image/canvas/base64/microphone data;
- camera tracks, timers, speech, and detector loop stop when the camera is disabled.
