# Physical-Camera WORD_ISOLATED Recognition Fix

Date: 2026-07-19

## Summary

Real browser camera testing reached the native OpenSigne API at
`POST /api/v1/recognitions/word`, but FastAPI returned HTTP 422. The backend was
reachable; the UI incorrectly showed “Le backend est indisponible.”

The fix preserves the strict `WORD_ISOLATED` V1 schema and does not change the
application architecture, model mode, dataset, or inference boundary.

## Original 422 Evidence

Docker logs captured real Firefox browser requests:

- API: `POST /api/v1/recognitions/word HTTP/1.1` returned `422 Unprocessable Entity`
- Nginx: Firefox request from `http://localhost:8081/app/recognition` returned 422
  with a 7,359-byte response body
- Inference: no corresponding inference failure; the request was rejected by API
  validation before inference

The original browser response body was not available in the container logs. A
sanitized reproduction against the same Docker API produced the matching FastAPI
validation detail:

```json
{
  "loc": ["body", "frames", 0, "timestamp_ms"],
  "msg": "Input should be less than or equal to 10000",
  "type": "less_than_equal"
}
```

The sanitized debug report is:
`artifacts/reports/physical-camera-422-debug.json`.

## Root Cause

The frontend V1 payload builder sent each frame’s absolute
`requestAnimationFrame` timestamp as `frames[*].timestamp_ms`. In a real browser
session, MediaPipe loading and user positioning can push those timestamps above
the backend limit of `10000` milliseconds per frame.

The fake-camera Playwright test previously mocked the recognition API response,
so it asserted the shape but did not exercise FastAPI/Pydantic validation.

## Contract After Fix

`WORD_ISOLATED` now builds:

- `recognition_mode`: `WORD_ISOLATED`
- `feature_schema_version`: `OPEN_SIGNE_LANDMARK_SCHEMA_V1`
- `target_frame_count`: `60`
- `landmark_count`: `75`
- `coordinate_count`: `3`
- `frames`: exactly 60
- frame landmarks: exactly 75 x 3 finite coordinates
- frame presence masks: exactly 75 values
- frame timestamps: monotonic, relative to capture start, 0..10000 ms

`ALPHABET_STATIC` remains unchanged on legacy schema `1.0.0` with 63 compact
features.

## Files Modified

- `apps/web/src/lib/api.ts`
- `apps/web/src/features/recognition/components/RecognitionWorkspace.tsx`
- `apps/web/src/features/recognition/hooks/useLandmarkRecorder.ts`
- `apps/web/src/features/recognition/services/capture-state.service.ts`
- `apps/web/src/features/recognition/services/landmark-schema-v1-normalizer.service.ts`
- `apps/web/src/features/recognition/services/recognition-api.service.ts`
- `apps/web/src/features/recognition/services/sequence-validator.service.ts`
- `apps/web/src/features/recognition/types/sequence.types.ts`
- `apps/web/src/features/recognition/tests/*`
- `apps/web/tests/e2e/recognition-camera.spec.ts`
- `services/api/tests/test_recognition_modes.py`
- `apps/web/src/features/recognition/test-fixtures/word-recognition-v1-valid.json`
- `tests/fixtures/recognition/word-recognition-v1-valid.json`

## Capture Lifecycle

Capture start is now gated by:

- camera ready
- detector ready, or explicit mock-camera fallback
- word mode active
- framing ready
- torso visible
- at least one hand visible
- acceptable distance
- stable pose
- no active submission

The UI no longer allows word capture while the detector is loading.

## Frame Finalization

The frontend now finalizes a capture by:

1. Keeping valid source frames with visible pose and at least one hand.
2. Rejecting captures with too few valid frames.
3. Resampling valid frames deterministically to exactly 60 frames.
4. Preserving chronological ordering.
5. Emitting 75 x 3 finite coordinates and a 75-entry presence mask per frame.
6. Converting timestamps to relative capture timestamps before serialization.

## Error Message Correction

HTTP 422 now maps to:

`La sequence capturee ne respecte pas le format attendu.`

Network failures remain:

`Le backend est indisponible.`

Development mode may include the safe invalid field path, such as
`frames.0.timestamp_ms`.

## Test Results

- Backend: `50 passed`, Ruff passed, MyPy passed
- Inference: `10 passed`, Ruff passed, MyPy passed
- ML: `23 passed`
- Speech: `4 passed`, Ruff passed, MyPy passed
- Frontend unit tests: `35 passed`
- Frontend lint: passed
- Frontend build: passed with the existing Vite chunk-size warning
- Playwright: `10 passed`
- Docker Compose config: passed
- Docker Compose ML profile config: passed
- Docker build: passed
- Docker ML profile build: passed
- Docker stack: API, inference, speech, PostgreSQL, Redis, MinIO healthy

## Docker Browser Verification

Against `http://localhost:8081/app/recognition?mockCamera=1` with the rebuilt web
container and real Docker API:

- Request URL: `/api/v1/recognitions/word`
- Request status: HTTP 200
- Payload size: 86,967 bytes
- Sequence ID: valid UUID
- Mode: `WORD_ISOLATED`
- Schema: `OPEN_SIGNE_LANDMARK_SCHEMA_V1`
- Frame count: 60
- Landmark count: 75
- Coordinate count: 3
- Timestamp range: 0..1200 ms
- Response model: `opensign-darija-landmark-mock`
- Response predictions: 3
- Raw video present: no
- Raw image/base64 present: no
- Audio present: no
- Direct browser request to inference: no
- Console errors: 0
- Page errors: 0
- Failed requests: 0

## Physical Camera Status

Actual FaceTime HD Camera retest from this CLI/headless session is
`UNCONFIRMED`; a human still needs to repeat the final browser test on the
physical device.

Expected final manual acceptance:

- detector transitions from loading to ready
- “Commencer” remains disabled during detector loading
- capture produces 60 x 75 x 3
- `POST /api/v1/recognitions/word` returns non-422
- result appears with confirmation/correction available
- no raw media upload occurs

Known non-blocking browser warnings may remain: WebGL/OpenGL warnings and
MediaPipe `NORM_RECT without IMAGE_DIMENSIONS`.

## Remaining Limitations

- The MoSL word model remains a development smoke/mock validation path, not a
  production recognizer.
- Physical-camera validation is not complete until a human runs the final
  FaceTime HD Camera check and records the successful network request.
