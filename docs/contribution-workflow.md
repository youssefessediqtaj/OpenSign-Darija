# Contribution Workflow

1. Contributor logs in.
2. Contributor creates or updates their contributor profile.
3. Contributor reviews consent templates and grants separate consents.
4. Contributor chooses an active campaign and target sign.
5. Contributor captures a repetition.
6. Backend creates recording metadata and returns presigned object-storage upload targets.
7. Client uploads landmarks, and optionally video when video consent is present.
8. Client confirms upload with checksums.
9. Contributor submits the contribution for review.

## Status Flow

`DRAFT -> READY_TO_SUBMIT -> SUBMITTED -> PENDING_LINGUIST_REVIEW -> PENDING_ML_REVIEW -> APPROVED`

Rejected or revision paths:

- `LINGUIST_REJECTED`
- `ML_REJECTED`
- `REVISION_REQUESTED`
- `AUTOMATIC_CHECK_FAILED`
- `REVOKED`

Phase 3 currently includes a synthetic frontend capture path for dataset submissions. The phase 2 real camera and MediaPipe recognition path remains available at `/app/recognition`.
