# Repository Map

OpenSign Darija is a small monorepo centered on one anonymous recognition loop.
Every top-level directory has a single owner.

| Path | Responsibility |
| --- | --- |
| `.agent/` | Workspace continuity notes for future Codex work. |
| `.github/` | CI workflows. |
| `apps/web/` | Public React recognition application. |
| `artifacts/` | Ignored generated reports and protected model packages. |
| `docs/` | Architecture, audit, operations, and final reports. |
| `infrastructure/` | Nginx gateway configuration. |
| `ml/` | Offline MoSL dataset, preprocessing, training, evaluation, export, and validation. |
| `packages/contracts/` | Language-neutral JSON contracts shared by tests and services. |
| `scripts/` | Reproducible audits, benchmarks, and protected-asset verification. |
| `services/api/` | Public stateless FastAPI API. |
| `services/inference/` | Internal ONNX inference runtime. |
| `services/speech/` | Internal local Arabic speech runtime. |
| `tests/` | Cross-service architecture and contract tests. |

Root `data/` is intentionally removed. ML datasets belong under `ml/data/`,
model packages and generated evidence belong under `artifacts/`, and deterministic
test data belongs under test fixture folders.

Machine-readable audit: `artifacts/reports/root-folder-audit.json`.
