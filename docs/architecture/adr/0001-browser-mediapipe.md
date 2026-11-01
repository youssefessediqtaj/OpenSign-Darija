# ADR 0001: Browser MediaPipe

## Status

Accepted.

## Decision

MediaPipe runs in the browser for the public recognition flow.

## Consequences

For recognition, camera pixels stay local to the browser. The recognition API receives
only normalized finite landmarks and segmentation metadata. The separate optional
contribution workflow has a different, explicit video-upload boundary. Inference containers do not need MediaPipe,
OpenCV, or video/image system packages for runtime prediction.
