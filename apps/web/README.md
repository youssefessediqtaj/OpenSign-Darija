# Web recognition application

The React application owns the public `/` and `/app/recognition` pages. It keeps
camera pixels in the browser, runs MediaPipe locally, automatically segments one
isolated sign, builds the exact 60 × 75 × 3 landmark payload, calls only same-origin
`/api` routes, displays a compact result, speaks known results once, and returns to
the waiting state after cooldown.

Ownership:

- `app/`: application shell and the two compatible route entries;
- `features/recognition/domain/`: deterministic segmentation, normalization,
  resampling, quality, and payload rules;
- `features/recognition/hooks/`: browser camera/MediaPipe lifecycle orchestration;
- `features/recognition/services/`: camera, MediaPipe, public recognition, and
  public sign-speech adapters;
- `features/recognition/state/`: the authoritative flow-state vocabulary;
- `shared/`: generic API transport, configuration, and small UI primitives.

The browser must never call inference or speech containers, and payload code must
never add video, image, canvas, screenshot, microphone, base64 camera, persistent
visitor, or arbitrary speech-text fields. These boundaries are enforced by the
root architecture tests and Playwright.

```bash
npm test -- --run
npm run lint
npm run build
npm run test:e2e
```
