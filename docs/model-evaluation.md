# Model Evaluation

Required model metrics:

- Top-1 accuracy
- Top-3 accuracy
- macro precision, recall, F1
- weighted F1
- per-class metrics
- confusion matrix
- unknown/uncertain rate
- calibration metrics
- latency and model size

The final test set must be signer-independent. Validation may be used for thresholds and temperature calibration; test must not be used for hyperparameter selection.

Current local status: no real metrics are available because no valid training dataset exists.
