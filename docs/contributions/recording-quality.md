# Recording quality

The browser enables recording only after 800–1500 ms of continuous readiness
(configured by `CONTRIBUTION_READINESS_DWELL_MS`). Checks are local:

- detector ready;
- face visible for framing only;
- shoulders/upper body framed;
- at least one hand visible;
- shoulder span indicates acceptable distance;
- detections provide an adequate-lighting proxy;
- shoulder position is stable.

“Face visible” never means identity recognition, matching, embedding, or biometric
authentication. Landmarks are not uploaded as readiness evidence.

The contributor records one sign per video using VP9 WebM, VP8 WebM, then generic
WebM preference. Default duration is 2–10 seconds, with automatic stop at the
maximum. The server independently verifies declared MIME, EBML signature, byte
limits, WebM container, duration, dimensions, frame rate, and full FFmpeg decode.
FFprobe/FFmpeg use fixed argument arrays, no shell, a timeout, and POSIX resource
limits where available.
