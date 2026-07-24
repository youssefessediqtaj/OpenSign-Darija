# MoSL Native Integration

Date: 2026-07-19

The local MoSL video dataset and the useful recognition ideas from the nested research project have been integrated through native OpenSign Darija modules. The external project runtime, notebooks, generated outputs, virtual environment and duplicate Docker stack were not copied into production paths.

## Implemented

- Source inventory and migration-decision reports for the nested project.
- Native raw-video copy under `ml/data/external/mosl-video-dataset/raw/`.
- SHA-256 migration verification: 2,216 source videos, 2,216 native videos, 2,216 matching checksums, zero missing/unexpected/mismatched files.
- Unicode-safe Arabic label parsing, category separation, manifests, checksums and split reports.
- `OPEN_SIGNE_LANDMARK_SCHEMA_V1`: 60 frames, 75 landmarks, 3 coordinates, `shoulder_centered_v1`.
- Browser/API/inference route separation:
  - `/api/v1/recognitions` keeps legacy `1.0.0`.
  - `/api/v1/recognitions/alphabet` keeps compact alphabet `1.0.0`.
  - `/api/v1/recognitions/word` requires `OPEN_SIGNE_LANDMARK_SCHEMA_V1`.
- Full MediaPipe preprocessing over all 2,216 videos with deterministic cache reuse.
- Processed artifact validation and duplicate-checksum metadata warnings.
- MoSL word training manifest with 108 eligible labels and 372 eligible samples after preprocessing.
- Real ONNX smoke model package for labels `16` and `17`, marked smoke-only.
- Dev-only smoke model registry and activation guard with `VALIDATED_SMOKE`.
- Docker, Playwright, backend, inference, ML, speech and frontend automated gates.

## Deliberately Not Integrated

- External app runtime and nested package layout.
- Text-to-pose SignLLM pipeline.
- AraBERT/text encoders.
- RL pose-generation loss.
- BLEU/ROUGE sign-generation metrics.
- Nested Docker/Compose/notebook environment.
- Generated external checkpoints and output folders.

## Deletion Status

The nested source folder is not deleted.

Deletion is currently blocked by the final gate report:

```text
artifacts/reports/nested-mosl-final-deletion-verification.json
```

Current blocker:

- `physical_camera_manual_validation`: `UNCONFIRMED`

The verifier reports zero active code/Make/test/runtime dependency matches for the nested source names. Remaining matches are provenance-only docs, reports, manifests and dataset artifacts.

## Production Readiness

The MoSL smoke model is not production-ready. Its metrics are smoke-only and cover two labels. Production activation still requires reviewed labels, signer-aware evaluation or an accepted substitute protocol, full training, calibration, confusion/error analysis and human validation.
