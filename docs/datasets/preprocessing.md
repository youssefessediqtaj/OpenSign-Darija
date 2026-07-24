# MoSL Preprocessing

Date: 2026-07-19

Command:

```bash
make ml-preprocess-mosl
```

MediaPipe asset:

```text
ml/assets/mediapipe/holistic_landmarker.task
```

The asset is ignored by Git. Current SHA-256:

```text
e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8
```

The preprocessor reads `ml/data/external/mosl-video-dataset/manifests/videos.jsonl`, runs MediaPipe Tasks HolisticLandmarker, normalizes to `OPEN_SIGNE_LANDMARK_SCHEMA_V1`, and writes checksum-keyed caches:

```text
ml/data/external/mosl-video-dataset/processed/landmarks/<sha256>.npz
```

Each cache contains:

- `landmarks`: `60 x 75 x 3`
- `presence_mask`: `60 x 75`
- `metadata`: source checksum, schema version, preprocessing version, label key, mode and quality counters

## Full Run

First full completion:

- Total source videos: 2,216
- Successfully processed: 2,216
- Newly processed in completion run: 158
- Cache hits in completion run: 2,058
- Failed: 0
- Unreadable videos: 0
- Invalid labels: 15
- NaN/Infinity/all-zero sequences: 0
- Low left-hand detection warnings: 339
- Output bytes: 91,044,446
- Duration: 301.088674 seconds

Cache verification run:

- Successfully processed: 2,216
- Newly processed: 0
- Cache hits: 2,216
- Failed: 0
- Duration: 1.709608 seconds

Processed artifact validation passed with 2,216 valid manifest entries and 350 warnings. The warnings are low-left-hand-detection cases plus duplicate-checksum rows whose label metadata differs because the same video bytes appear under multiple labels.
