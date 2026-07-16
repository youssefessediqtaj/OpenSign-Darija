# Dataset Versioning

Dataset versions are managed by admin endpoints under `/api/v1/admin/datasets`.

## Lifecycle

- `DRAFT`
- `BUILDING`
- `VALIDATED`
- `PUBLISHED`
- `ARCHIVED`

The build step includes only approved, non-revoked contributions with confirmed uploads. The validation step checks the generated manifest before publish.

Versions are immutable once published; create a new version for additional approved data.
