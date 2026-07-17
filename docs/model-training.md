# Model Training

The training entrypoint is:

```bash
python -m ml.training.train --config ml/configs/gru.yaml --dataset-version 0.1.0
```

Training always runs dataset validation first. It refuses to continue unless the dataset is `READY` or `PUBLISHED`, has compatible consent/licensing, contains approved non-revoked contributions, has valid checksums, and keeps contributors separated by split.

Current local status: training is blocked because the scaffold manifest has no items.

Configuration lives in `ml/configs/*.yaml`. Seeds, dataset version, feature schema, architecture, and hyperparameters are recorded in the artifact directory.
