# MoSL Word Smoke Model Card

Date: 2026-07-19

## Model

- Name: `mosl-word-smoke-v1`
- Version: `0.1.0-smoke`
- Status: `VALIDATED_SMOKE`
- Task: `WORD_ISOLATED`
- Input schema: `OPEN_SIGNE_LANDMARK_SCHEMA_V1`
- Input shape: `60 x 75 x 3`
- Labels: `16`, `17`
- Architecture: small bidirectional GRU

## Scope

This model is a real ONNX export used to validate the native training/export/registry/inference path. It is not a production recognition model and must not be described as accurate MoSL recognition.

## Validation

- Package validation: passed
- Required sidecars: present, including `dataset-manifest-checksum.txt`
- ONNX Runtime load: passed
- ONNX parity: `4.470348358154297e-08`
- Registry smoke activation: development-only and guarded

## Known Limits

- Two labels only.
- Smoke split is tiny and not signer-independent.
- Metrics are marked `SMOKE TEST ONLY - NOT PRODUCTION METRICS`.
- Full MoSL production evaluation, calibration and error analysis remain future work.
