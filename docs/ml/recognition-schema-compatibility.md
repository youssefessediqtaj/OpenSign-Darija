# Recognition Schema Compatibility

OpenSign Darija currently supports two landmark contracts. They are intentionally versioned because the legacy browser contract and the MoSL video training contract are not the same representation.

| Mode | Route | Schema | Per-frame shape | Status |
| --- | --- | --- | --- | --- |
| Legacy word compatibility | `POST /api/v1/recognitions` | `1.0.0` | `features: 63`, `presence_mask: 21` | Preserved for existing behavior and regression tests. |
| Alphabet static | `POST /api/v1/recognitions/alphabet` | `1.0.0` | `features: 63`, `presence_mask: 21` | Preserved for current alphabet workflow. |
| MoSL isolated word | `POST /api/v1/recognitions/word` | `OPEN_SIGNE_LANDMARK_SCHEMA_V1` | `landmarks: 75 x 3`, `presence_mask: 75` | Active target contract for MoSL smoke model integration. |

## Legacy `1.0.0`

The old compact frame is not `21 hand landmarks x 3`. It is a reduced mixed-body representation flattened to 63 floats:

- 6 pose landmarks: shoulders, elbows and wrists.
- 3 face landmarks: nose, mouth-left and mouth-right.
- 6 selected left-hand landmarks: wrist and five fingertips.
- 6 selected right-hand landmarks: wrist and five fingertips.

The presence mask has one value per reduced landmark, so it has 21 entries.

## `OPEN_SIGNE_LANDMARK_SCHEMA_V1`

The MoSL word schema uses:

- `recognition_mode: WORD_ISOLATED`
- `coordinate_format: shoulder_centered_v1`
- `landmark_count: 75`
- `coordinate_count: 3`
- 33 pose landmarks, then 21 left-hand landmarks, then 21 right-hand landmarks.
- No face landmarks.

Missing landmarks are represented as `[0, 0, 0]` with a `0` presence-mask value. Present landmarks are shoulder-centered and shoulder-width scaled.

## Rejection Behavior

- `/api/v1/recognitions/word` rejects legacy 63-feature frames.
- `/api/v1/recognitions/alphabet` rejects the 75-landmark word payload.
- Unknown schema identifiers are rejected with request validation errors.
- NaN, infinity, invalid mask values, wrong frame counts and wrong landmark shapes are rejected before inference.
- Payloads remain size-limited; the default API ceiling is 1.5 MB to accommodate 60 frames of `75 x 3` JSON landmarks without accepting raw video or images.

## Migration Strategy

The browser word capture path now builds `OPEN_SIGNE_LANDMARK_SCHEMA_V1` payloads and sends them through the public API. The alphabet path keeps using legacy `1.0.0`. The old root recognition route remains a compatibility route until downstream consumers are migrated or removed.
