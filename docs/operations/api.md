# Core runtime API

Nginx exposes only the stateless API needed by automatic isolated-sign recognition. The
public client does not need a token, account, model ID, or dataset choice.

## Public endpoints

- `GET /api/v1/version`
- `GET /api/v1/health`
- `POST /api/v1/recognitions/word`
- `POST /api/v1/speech/sign`

The application also exposes `GET /health` as a container health alias. Account,
contribution, message, dataset-registry, alphabet, mock-recognition, and manual
confirmation modules are absent from the core source and runtime.

## Word recognition

`POST /api/v1/recognitions/word` accepts only JSON landmark data:

- mode `WORD_ISOLATED`;
- schema `OPEN_SIGNE_LANDMARK_SCHEMA_V1`;
- exactly 60 sequential frames;
- exactly 75 landmarks per frame;
- exactly three finite coordinates per landmark;
- binary 75-element presence mask;
- duration, quality, and automatic-segmentation metadata.

Unknown fields are forbidden. Consequently `video`, `image`, `audio`, blobs, base64
camera data, and developer-only parameters return validation errors rather than being
silently ignored. Nginx and the API enforce request size limits; the endpoint also has an
anonymous rate limit.

Recognized response:

```json
{
  "status": "recognized",
  "label_key": "احب",
  "label_ar": "أَحَبَّ",
  "confidence": 0.91,
  "unknown": false,
  "latency_ms": 84
}
```

Unknown response:

```json
{
  "status": "unknown",
  "label_key": null,
  "label_ar": null,
  "confidence": 0.31,
  "unknown": true,
  "latency_ms": 79
}
```

Top-K remains inside the API-to-inference contract and is not returned to the public UI.
Quality rejection and calibrated low confidence both produce the same safe UNKNOWN
shape.

## Sign speech

`POST /api/v1/speech/sign` accepts exactly:

```json
{"label_key": "احب"}
```

The API resolves the Arabic display value from the validated active model package; it
does not accept arbitrary text from the browser. An unsupported key returns 404. A
supported key returns a playable WAV data URL and metadata. The API tries the offline
`ar-MA` voice, then the offline `ar` fallback.

## Internal services

The API alone calls internal `POST /predict/word` on the inference service and
`POST /synthesize` on the speech service. Neither service is routed by public Nginx.
Their `/health` and `/ready` endpoints are used for container readiness. Real inference
fails closed if the package, shapes, labels, calibration, or checksums are inconsistent.
