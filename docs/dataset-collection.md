# Dataset Collection

OpenSign Darija phase 3 adds a contribution workflow for Moroccan Sign Language data.

## Scope

- Contributors join an active campaign, select a target sign, and submit repetitions.
- The platform accepts landmark-only submissions by default.
- Video upload is optional and blocked unless video recording and video storage consents are both granted.
- Audio is not captured, stored, or exported.
- Raw files live in MinIO object storage. PostgreSQL stores metadata, object keys, checksums, review decisions, and audit events.

## Main Commands

```bash
make seed-dataset
make test-dataset
make dataset-build
make dataset-validate
make dataset-stats
make cleanup-uploads
```

`make test-dataset` is available through `make test-backend` for the API test suite and dataset workflow tests.

## Development Accounts

Seed data creates these local accounts with password `OpenSignDemo123!`:

- `contributor@example.test`
- `linguist@example.test`
- `ml-reviewer@example.test`
- `admin@example.test`

These accounts are for local development only.
