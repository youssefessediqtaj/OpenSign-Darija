# COLORS_V1 local runtime correction

On 2026-11-01, port 8081 served the Compose Nginx/web/API stack. Its inference
configuration selected `mosl-isolated-sign-v1`, its legacy word route was the default,
and experimental color routes were disabled. The served frontend was a production Vite
build, which excluded the development-only color toggle. API version `1.0.0` was not a
reliable frontend build identifier; the served pre-change bundle was `index-gP95zAdc.js`.
This was configuration and routing behavior, not evidence of browser caching.

`make up` and `make dev` now apply `docker-compose.local.yml`: host port 8081 binds only
to 127.0.0.1, the experimental gateway and inference are enabled on a dedicated internal
network, and only the read-only COLORS_V1 artifact directory is mounted in inference.
The local browser token is public and is a diagnostic guard, not a production secret.
The frontend requires a loopback host and same-origin API. Forwarded headers are stripped
by the dedicated local Nginx route; direct service access still requires the token and
loopback or the explicitly configured internal network. Standard Compose does not enable
experimental inference. Never use the local override as a production deployment.

In this mode legacy model construction is skipped; both word endpoints return 404 and
there is no legacy fallback. Missing or invalid color artifacts yield `MODEL_NOT_READY`.
The candidate is an uncalibrated argmax for diagnostic purposes only; UNKNOWN remains the
model decision and no candidate is spoken. Reset aborts and invalidates pending requests,
clears segmentation, and keeps the camera and detector running.

The registry and training report point to COLORS_V1, share the SHA-256 of the ten-record
source manifest, and specify nine labels and ten samples. Both blue source variants map to
`blue`. The preprocessing tools reject paths overlapping the legacy dataset. The local
inference container no longer mounts the legacy weights. This provenance evidence does
not establish that the provisional derived features were approved: technical and
linguistic review, source rights and consent remain pending or unconfirmed. The single
epoch, in-sample smoke model has no independent accuracy or calibration; real-camera
recognition and segmentation require separate validation with sufficient diverse signers.

The Docker gateway and ONNX runtime returned a color candidate for a contract landmark
fixture; the legacy word endpoint returned 404. Playwright's mocked detector exercised
candidate display, reset, no speech and no legacy request. Two separate Chromium tests
feeding converted source videos into the real camera/MediaPipe path reached preview but
did not submit a segment within 30 seconds: existing hand/body visibility checks rejected
the captured segments. These source videos were not validated camera fixtures, and this
does not establish physical-camera performance. No capture thresholds were relaxed.
