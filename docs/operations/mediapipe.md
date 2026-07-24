# Browser MediaPipe

The frontend uses `@mediapipe/tasks-vision` `HolisticLandmarker` in VIDEO mode. Both the
WASM runtime and `holistic_landmarker.task` are served locally by the web container:

- `VITE_MEDIAPIPE_WASM_PATH=/mediapipe/wasm`
- `VITE_MEDIAPIPE_MODEL_PATH=/models/holistic_landmarker.task`

There is no CDN or runtime model download. A rejected loader promise is cleared so a
later camera activation can retry. The animation-frame loop is idempotent and owns one
run ID, preventing multiple detector loops after React renders.

The core application processes at a nominal 15 FPS cadence. Each result is reduced to 33
pose, 21 left-hand, and 21 right-hand landmarks; face landmarks are not transmitted.
Physical FPS depends on the device and must be measured rather than inferred from the
throttle setting.
