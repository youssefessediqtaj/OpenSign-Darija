# Speech service

Internal stateless Arabic synthesis for supported Darija sign labels. The API,
not the browser, calls this service. It uses the local `espeak-ng`/system engine
without a cloud request, downloaded voice model, database, queue, or cache.

Routes actives :

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /voices`
- `POST /synthesize`

`POST /synthesize` accepts the bounded internal contract, normalizes controlled
Arabic/Darija text, selects the `ar-MA` identity or explicit `ar` fallback,
validates the generated WAV, and returns in-memory Base64 audio metadata. A
bounded semaphore and subprocess timeout prevent unbounded local synthesis.

Code ownership:

- `api/`: health/readiness/voice/synthesis HTTP routes;
- `schemas/`: strict request/response and voice shapes;
- `providers/`: one local provider plus the system command adapter;
- `services/`: normalization, validation, concurrency, and result formatting;
- `core/`: environment-backed limits.

`requirements.lock` pins the tested production-container resolution. The
`httpx2` TestClient dependency is development-only.

Run `make speech-test` from the repository root.
