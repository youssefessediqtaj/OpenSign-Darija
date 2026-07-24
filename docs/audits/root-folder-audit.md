# Root Folder Audit

Every root path has one explicit responsibility and decision.

| Path | Decision | Responsibility | Status |
| --- | --- | --- | --- |
| `.agent` | `KEEP` | Workspace continuity for future Codex turns. | directory / tracked |
| `.env.example` | `KEEP` | Documented local configuration template. | file / tracked |
| `.github` | `KEEP` | CI workflow ownership. | directory / tracked |
| `.gitignore` | `KEEP` | Keeps caches, raw data, and large generated binaries out of Git while allowing report/metadata evidence. | file / tracked |
| `.pytest_cache` | `LOCAL_GENERATED_ONLY` | Ignored pytest cache; must not exist in the final root. | absent / untracked_or_absent |
| `.ruff_cache` | `LOCAL_GENERATED_ONLY` | Ignored Ruff cache; must not exist in the final root. | absent / untracked_or_absent |
| `LICENSE` | `KEEP` | Project license. | file / tracked |
| `Makefile` | `KEEP` | Developer command surface. | file / tracked |
| `NOTICE` | `KEEP` | Attribution and provenance notice. | file / tracked |
| `OpenSigne-Darija-readme` | `DELETE_AFTER_VERIFICATION` | Duplicate README workspace removed after verification. | absent / untracked_or_absent |
| `README.md` | `KEEP` | Root project overview. | file / tracked |
| `apps` | `KEEP` | Public React recognition application. | directory / tracked |
| `artifacts` | `KEEP` | Generated reports plus protected local model/data evidence; large binaries remain ignored selectively. | directory / untracked_or_absent |
| `data` | `DELETE_AFTER_VERIFICATION` | Obsolete root data workspace; ML data lives under ml/data. | absent / untracked_or_absent |
| `docker-compose.yml` | `KEEP` | Local production-shaped runtime stack. | file / tracked |
| `docs` | `KEEP` | Architecture, audit, operations, and report documentation. | directory / tracked |
| `infrastructure` | `KEEP` | Nginx gateway configuration. | directory / tracked |
| `ml` | `KEEP` | Offline dataset, preprocessing, training, evaluation, export, and validation. | directory / tracked |
| `packages` | `KEEP` | Language-neutral contracts used by architecture/contract tests. | directory / tracked |
| `scripts` | `KEEP` | Reproducible audits, benchmarks, and verification tools. | directory / tracked |
| `services` | `KEEP` | Stateless API, internal inference, and internal speech services. | directory / tracked |
| `tests` | `KEEP` | Cross-service architecture and contract tests. | directory / tracked |

Generated machine-readable source: `artifacts/reports/root-folder-audit.json`.
