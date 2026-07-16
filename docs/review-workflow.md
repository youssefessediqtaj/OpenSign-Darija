# Review Workflow

Dataset approval has two gates.

## Linguistic Review

Linguistic reviewers and admins can inspect the linguistic queue and approve, reject, or request revision. Approval moves the contribution to the ML queue.

## ML Review

ML reviewers and admins can inspect technical metadata and quality metrics. Approval marks the contribution as `APPROVED`.

## Enforcement

Review endpoints require backend role checks:

- `LINGUIST_REVIEWER` or `ADMIN` for linguistic review.
- `ML_REVIEWER` or `ADMIN` for ML review.

Frontend route hiding is not treated as security.
