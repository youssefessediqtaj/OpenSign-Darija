# ADR 0001: Browser MediaPipe

## Status

Accepted.

## Decision

MediaPipe runs in the browser for the public recognition flow.

## Consequences

Camera pixels stay local to the browser. The API receives only normalized finite
landmarks and segmentation metadata. Inference containers do not need MediaPipe,
OpenCV, or video/image system packages for runtime prediction.
