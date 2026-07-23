# Machine Learning Workspace

The active ML path is the offline, local-only MoSL isolated-sign workflow. It uses
the native 60 x 75 x 3 landmark caches under
`ml/data/external/mosl-video-dataset/` and never downloads datasets or model
assets.

Directory ownership:

- `assets/`: local MediaPipe task model used by browser Docker mount and offline preprocessing.
- `data/`: protected local dataset, manifests, splits, and processed caches.
- `datasets/`: dataset scanning, auditing, manifests, and split utilities.
- `preprocessing/`: offline landmark preprocessing helpers.
- `training/`: local model training entry points.
- `evaluation/`: offline evaluation helpers.
- `export/`: ONNX package validation and export checks.
- `validation/`: data/model validation utilities.
- `tests/`: deterministic ML tests.

```bash
ml/.venv/bin/python -m ml.datasets.mosl_video.local_audit
ml/.venv/bin/python -m ml.training.train_mosl_v1 --epochs 40 --hidden-size 64 --patience 8
ml/.venv/bin/python -m ml.export.validate_mosl_v1
ml/.venv/bin/python -m pytest -q ml/tests
ml/.venv/bin/python -m ruff check ml
```

The selected package is written to
`artifacts/models/mosl-isolated-sign-v1/`. Its model card and calibration report
are authoritative about supported signs and limitations. The older
`mosl-word-smoke-v1` package is retained only as a technical smoke artifact.
