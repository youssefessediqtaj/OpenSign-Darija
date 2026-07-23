# Browser console/network checklist

- no uncaught React error, rejected promise, or duplicate detector animation loop;
- no MediaPipe model/WASM CDN request;
- no authentication redirect or token/local-storage requirement;
- no request to inference, model registry, alphabet, dataset import, or external source;
- recognition and known-only speech requests return successfully;
- UNKNOWN causes no speech request;
- request bodies contain landmarks only, never video/image/canvas/base64/microphone data;
- camera tracks, timers, speech, and detector loop stop when the camera is disabled.
