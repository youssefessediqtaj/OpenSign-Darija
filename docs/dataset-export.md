# Dataset Export

Dataset exports are manifest-based.

## Privacy Rules

- Exports use anonymous contributor IDs such as `signer_000001`.
- Exports must not include email, auth user IDs, passwords, access tokens, or refresh tokens.
- Splits are assigned by contributor so one contributor cannot appear in train and test at the same time.
- Video object keys are included only when a recording has video consent and an uploaded video key.

## Commands

```bash
python -m ml.datasets.build_manifest
python -m ml.datasets.validate_dataset
python -m ml.preprocessing.prepare_sequences
python -m ml.datasets.generate_statistics
```

The backend admin build also writes manifest and statistics objects to the dataset export bucket.
