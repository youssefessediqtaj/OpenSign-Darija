# Playwright automatic-flow gate

```bash
cd apps/web
npm run test:e2e
```

The deterministic suite verifies:

- `/` and `/app/recognition` expose the same minimal anonymous product;
- only `Activer la caméra` is clicked;
- manual capture/finish/submit/mode/auth/external controls are absent;
- rest -> first gesture -> rest/reset -> second gesture runs two automatic cycles;
- every request has 60 frames, 75 landmarks, 3 finite coordinates, strict increasing
  relative timestamps, boundary metadata, and no raw media;
- known results display Arabic and invoke speech once each;
- UNKNOWN displays the safe message and invokes speech zero times;
- held poses do not create additional recognition or speech;
- the browser never calls inference, legacy/alphabet/auth/model/external endpoints.

A separate non-intercepted test targets the real Docker API and speech service. It skips
only with an explicit health-unavailable reason. Synthetic landmark gestures are not
misrepresented as guaranteed known model examples; a real fake-video/physical-camera run
is recorded separately.

For the strict two-known-sign gate, start Docker and provide a Y4M file containing rest,
a supported sign, rest/reset, and a second supported sign:

```bash
PLAYWRIGHT_FAKE_CAMERA_VIDEO=/absolute/path/to/two-known-signs.y4m \
PLAYWRIGHT_EXPECT_TWO_SIGNS=1 \
DOCKER_E2E_BASE_URL=http://127.0.0.1:8081 \
npm run test:e2e
```

With `PLAYWRIGHT_EXPECT_TWO_SIGNS=1`, the test requires exactly two recognized decisions,
two correlated speech requests, no third duplicate, and at least 15 effective processed
frames per second for both captures. The fixture must be created only from already-local
videos; it must not be downloaded.
