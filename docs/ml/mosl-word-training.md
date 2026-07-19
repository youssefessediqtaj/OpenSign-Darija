# MoSL Word Training

Date: 2026-07-19

Commands:

```bash
make ml-prepare-word-training-manifest
make ml-train-smoke
make ml-validate-word-smoke-model
make ml-register-word-smoke-model
make ml-activate-word-smoke
```

The production-oriented aliases remain placeholders for a future full model workflow:

```bash
make ml-train-word
make ml-evaluate-word
make ml-export-word
make ml-package-word
make ml-register-word-model
```

## Current Data State

- `WORD_ISOLATED` samples: 2,145
- Processed word samples: 2,145
- Eligible labels after full preprocessing: 108
- Eligible samples: 372
- Smoke subset labels from the manifest: `16`, `17`, `18`, `19`, `لون`

## Smoke Model

The current validated model package is:

```text
artifacts/models/mosl-word-smoke-v1/
```

Validation requires:

- `model.onnx`
- `labels.json`
- `landmark-schema.json`
- `preprocessing.json`
- `metrics.json`
- `onnx-validation.json`
- `model-card.md`
- `checksums.json`
- `training-config.yaml`
- `dataset-manifest-checksum.txt`

Current ONNX contract:

- Input: `landmarks`, shape `[batch, 60, 75, 3]`
- Output: `logits`, shape `[batch, 2]`
- Labels: `16`, `17`
- ONNX parity max absolute difference: `4.470348358154297e-08`

The smoke model may be registered and activated only for development validation with:

```bash
APP_ENV=development ALLOW_SMOKE_MODEL_ACTIVATION=true make ml-activate-word-smoke
```

It is not production-ready.
