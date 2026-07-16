export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  mediapipeModelPath:
    import.meta.env.VITE_MEDIAPIPE_MODEL_PATH ??
    'https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/1/holistic_landmarker.task',
  mediapipeWasmPath:
    import.meta.env.VITE_MEDIAPIPE_WASM_PATH ??
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm',
  cameraDefaultWidth: Number(import.meta.env.VITE_CAMERA_DEFAULT_WIDTH ?? 1280),
  cameraDefaultHeight: Number(import.meta.env.VITE_CAMERA_DEFAULT_HEIGHT ?? 720),
  cameraDefaultFps: Number(import.meta.env.VITE_CAMERA_DEFAULT_FPS ?? 30),
  landmarkTargetFrames: Number(import.meta.env.VITE_LANDMARK_TARGET_FRAMES ?? 30),
  enableLandmarkOverlay: import.meta.env.VITE_ENABLE_LANDMARK_OVERLAY !== 'false',
  enablePerformanceMetrics: import.meta.env.VITE_ENABLE_PERFORMANCE_METRICS === 'true',
};
