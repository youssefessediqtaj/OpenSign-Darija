# Landmark Selection Schema

Version: `1.0.0`

Coordinate format: `torso_normalized_v1`

The frontend extracts MediaPipe Holistic landmarks locally and submits only a compact feature set. Full face meshes, images, canvas captures, audio, and video are excluded.

## Origin And Scale

- Origin: midpoint between left and right shoulders.
- Scale: Euclidean distance between shoulders.
- Missing or invalid scale: sequence is invalid.
- Coordinates keep relative depth `z`.

## Feature Order

See `landmark-schema.json`. Each selected point contributes `[x, y, z]` in the documented order. A separate `presence_mask` keeps missing landmarks explicit.

## Privacy

Landmarks can still be sensitive because they describe a person's body motion. They must not be stored automatically or treated as fully anonymous.
