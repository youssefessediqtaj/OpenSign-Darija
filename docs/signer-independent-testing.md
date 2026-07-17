# Signer-Independent Testing

Contributors must not overlap across train, validation, test, or holdout.

The validation command checks contributor leakage:

```bash
python -m ml.datasets.validate_training_dataset --dataset-version 0.1.0
```

It reports contributors per split, classes per split, sequences per split, and contamination errors.
