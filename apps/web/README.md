# Web recognition application

The React application owns public recognition at `/` and `/app/recognition`, plus
the separately flagged `/contribute` workflow. Recognition keeps camera pixels in
the browser, runs MediaPipe locally, automatically segments one isolated sign,
builds the exact 60 × 75 × 3 payload, displays a compact result, and speaks known
results once.

Ownership:

- `app/`: application shell and the two compatible route entries;
- `features/recognition/domain/`: deterministic segmentation, normalization,
  resampling, quality, and payload rules;
- `features/recognition/hooks/`: browser camera/MediaPipe lifecycle orchestration;
- `features/recognition/services/`: camera, MediaPipe, public recognition, and
  public sign-speech adapters;
- `features/recognition/state/`: the authoritative flow-state vocabulary;
- `features/contributions/`: independent adult form, notice, reference, readiness,
  MediaRecorder, preview, retake, upload, and receipt flow;
- `shared/`: generic API transport, configuration, and small UI primitives.

Entry point: `src/main.tsx`.

Environment:

- `VITE_API_BASE_URL`: optional same-origin API override for standalone Vite development.
- `VITE_MEDIAPIPE_MODEL_PATH`: browser-served Holistic task model path.
- `VITE_MEDIAPIPE_WASM_PATH`: browser-served MediaPipe WASM directory.
- `VITE_CAMERA_DEFAULT_WIDTH`, `VITE_CAMERA_DEFAULT_HEIGHT`, `VITE_CAMERA_DEFAULT_FPS`:
  camera constraint defaults.

The browser must never call inference or speech containers, and payload code must
never add video, image, canvas, screenshot, microphone, base64 camera, persistent
visitor, or arbitrary speech-text fields. These boundaries are enforced by the
root architecture tests and Playwright.

Contribution readiness also runs MediaPipe locally but never enters the
recognition state machine. It sends a private WebM only after explicit consent,
record, stop, preview, and save actions. See
[contribution architecture](../../docs/contributions/architecture.md).

```bash
npm test -- --run
npm run lint
npm run build
npm run test:e2e
```
