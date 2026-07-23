# Landmark Schema V1

Canonical schema name:

```text
OPEN_SIGNE_LANDMARK_SCHEMA_V1
```

This schema formalizes the offline video preprocessing and browser/API/inference contract for MoSL word recognition.

## Shape

```text
frames x 75 x 3
```

Per frame:

- 33 MediaPipe pose landmarks, indices `0..32`
- 21 left-hand landmarks, indices `0..20`
- 21 right-hand landmarks, indices `0..20`
- Face landmarks are excluded.
- Coordinate order is `x, y, z`.
- `z` is MediaPipe relative landmark depth, not verified real-world 3D reconstruction.

## Normalization

Implemented in `ml/preprocessing/landmark_schema_v1.py`.

- Root center: midpoint between pose landmarks 11 and 12, left/right shoulders.
- Scale: shoulder-width Euclidean distance.
- Missing landmarks: zeros in the landmark tensor and `0` in the presence mask.
- Present landmarks: normalized coordinates and `1` in the presence mask.
- Padding: zero frames to target length.
- Truncation: deterministic head truncation.
- Mirroring: not applied by default because handedness can change sign meaning.
- Left/right policy: left and right hands remain separate ordered blocks.
- Expected fixed sequence length for baseline config: 60 frames.

## Compatibility

The core product uses `OPEN_SIGNE_LANDMARK_SCHEMA_V1` exclusively on public
`POST /api/v1/recognitions/word` and internal `POST /predict/word`. Legacy compact and
alphabet contracts are not mounted in the simplified runtime. A mismatched schema,
frame count, landmark count, coordinate count, non-finite value, or extra raw-media field
is rejected.
