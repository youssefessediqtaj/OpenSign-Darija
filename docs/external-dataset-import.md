# External Dataset Import

Kaggle metadata/download:

```bash
make dataset-download-kaggle-alphabet
```

Mendeley manual preparation:

```bash
make dataset-import-mendeley
python -m ml.datasets.external.import_local_archive --source mendeley_mosl_v1 --archive /path/to/archive.zip --output data/raw/external/mendeley-mosl-v1
```

Audit:

```bash
make dataset-validate-licenses
make dataset-audit-external
make dataset-check-duplicates
```
