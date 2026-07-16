# Recognition Flow

```text
Browser camera
  -> local video element
  -> MediaPipe HolisticLandmarker
  -> local normalization and sequence validation
  -> POST /api/v1/recognitions
  -> API calls internal inference /predict
  -> simulated Top 3 predictions
```

The frontend never calls the inference service directly.

## Manual Capture

1. User activates the camera.
2. Framing is evaluated.
3. User starts a 3 second countdown.
4. Landmarks are buffered in memory.
5. User finishes capture.
6. Sequence is compacted and validated.
7. Only compact landmarks are submitted.

Invalid sequences are rejected locally and by the backend.
