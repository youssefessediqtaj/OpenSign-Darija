# Landmark Schema

Version: `1.0.0`

Coordinate format: `torso_normalized_v1`

## Included Points

The compact schema includes 21 selected landmarks:

- shoulders, elbows, wrists from pose;
- nose and two mouth points from face;
- wrist and fingertip points from each hand.

Each point contributes `[x, y, z]`, producing 63 numeric features per frame. `presence_mask` contains 21 binary values.

## Normalization

Origin is the midpoint between shoulders. Scale is shoulder distance. Missing values are encoded as zero features with presence mask `0`.

## Temporal Shape

The frontend resamples each valid capture to 30 frames. Future versions may support 45 or 60 frames with a new schema version if feature ordering changes.

## Excluded Data

Full face meshes, images, video, audio, canvas exports, and screenshots are not sent.
