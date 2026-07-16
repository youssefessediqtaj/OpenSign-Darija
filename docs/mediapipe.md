# MediaPipe

The frontend uses the official `@mediapipe/tasks-vision` package and `HolisticLandmarker`.

## Loading

`useHolisticLandmarker` loads the WASM files and model path from environment variables:

- `VITE_MEDIAPIPE_MODEL_PATH`
- `VITE_MEDIAPIPE_WASM_PATH`

The model is loaded once per browser session. A 12 second timeout falls back to test mode messaging.

## Runtime

MediaPipe runs in `VIDEO` mode. The analysis loop samples frames at a configurable rate:

- `QUALITY`: about 20 FPS
- `BALANCED` and `AUTO`: about 15 FPS
- `PERFORMANCE`: about 10 FPS

The UI stores only the latest frame in React state; capture buffers stay in refs.

## Worker

MediaPipe itself runs on the main browser context because the Tasks Vision API depends on browser image sources. Sequence compaction and validation are isolated in `landmark.worker.ts` for future off-main-thread use.
