# Scripts

Scripts are non-destructive by default and assume they are run from the repository root
unless their command-line help says otherwise.

## Verification

- `verification/audit_project_structure.py` writes root, dependency, environment, and
  unused-code audit evidence under `artifacts/reports/` and human summaries under
  `docs/audits/`.
- `verification/audit_repository_architecture.py` writes the repository inventory,
  dependency graph, and architecture graph documentation.
- `verification/verify_protected_assets.py` snapshots protected model, dataset,
  MediaPipe, and canonical inference evidence.

## Benchmarking

- `benchmarking/benchmark_inference.py` measures public API recognition latency against
  the active local model package.
- `benchmarking/benchmark_speech.py` measures public sign-speech latency and validates
  returned WAV data.

Prefer the root Makefile targets where available:

```bash
make architecture-check
make benchmark-inference
make benchmark-speech
make verify
```
