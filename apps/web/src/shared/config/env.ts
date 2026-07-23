export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  mediapipeModelPath:
    import.meta.env.VITE_MEDIAPIPE_MODEL_PATH ??
    '/models/holistic_landmarker.task',
  mediapipeWasmPath:
    import.meta.env.VITE_MEDIAPIPE_WASM_PATH ??
    '/mediapipe/wasm',
  cameraDefaultWidth: Number(import.meta.env.VITE_CAMERA_DEFAULT_WIDTH ?? 1280),
  cameraDefaultHeight: Number(import.meta.env.VITE_CAMERA_DEFAULT_HEIGHT ?? 720),
  cameraDefaultFps: Number(import.meta.env.VITE_CAMERA_DEFAULT_FPS ?? 30),
};
