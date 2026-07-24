# Historical two-class smoke artifact

`artifacts/models/mosl-word-smoke-v1/` is retained only to prove the old training/export
plumbing once worked.

- `TECHNICAL_SMOKE_ONLY`
- `NOT_USER_MODEL`
- `NOT_PRODUCTION_READY`
- labels: `16`, `17`
- training samples: 4
- validation samples: 2
- epochs: 2
- reported validation accuracy: 1.0 on only one sample per class
- ONNX parity max absolute difference: `4.470348358154297e-08`

Its tiny metric is not evidence of general recognition quality. No public route, frontend
control, Make activation alias, or Docker default loads it. The selected user-flow model
is `artifacts/models/mosl-isolated-sign-v1/` and must pass full package validation.
