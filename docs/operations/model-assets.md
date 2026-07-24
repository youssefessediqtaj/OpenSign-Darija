# Model Assets

Protected runtime assets stay in fixed local paths:

```text
artifacts/models/mosl-isolated-sign-v1/
ml/assets/mediapipe/holistic_landmarker.task
ml/data/external/mosl-video-dataset/
```

The active ONNX package must not be renamed, regenerated, or moved by documentation or
root-structure cleanup. The inference service validates:

- `model.onnx` SHA-256;
- `checksums.json`;
- `labels.json`;
- `supported-signs.json`;
- `landmark-schema.json`;
- `confidence-calibration.json`;
- input shape `[batch, 60, 75, 3]`;
- output shape matching the supported label count.

Use the protected-asset verifier before and after structural refactors:

```bash
services/inference/.venv/bin/python scripts/verification/verify_protected_assets.py --phase before
services/inference/.venv/bin/python scripts/verification/verify_protected_assets.py --phase after
```
