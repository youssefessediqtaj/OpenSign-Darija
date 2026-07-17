# Model Calibration

Temperature scaling is implemented for validation logits.

Calibration must use validation data only. The test set is reserved for final signer-independent evaluation.

Artifacts:

- `calibration.json`
- ECE
- NLL
- selected temperature
