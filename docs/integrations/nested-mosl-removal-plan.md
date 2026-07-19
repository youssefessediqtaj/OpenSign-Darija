# Nested MoSL Removal Plan

Date: 2026-07-19

The nested `Multimodal-Moroccan-Sign-Language-Generation/` folder was removed
after all source-folder deletion gates passed. Physical-camera validation remains
manual QA for the native OpenSigne workflow, not a dependency on the deleted
nested source project.

## Completed Gates

- Source inventory generated.
- Native video migration verified by checksum.
- Native preprocessing completed for all 2,216 videos.
- Processed artifacts validated.
- Active source dependency scan reports zero active dependency matches.
- Native tests, Playwright, Docker build/start/health and Docker route smokes passed.
- Smoke model package and dev-only activation guard validated.
- Safe exact-path Python deletion completed.
- Post-deletion verification reports `nested_folder_exists: false`.

## Remaining QA

- Physical camera/manual browser validation: `UNCONFIRMED`.

## Deletion Rule Used

Deletion may be performed only after `artifacts/reports/nested-mosl-final-deletion-verification.json` reports:

```json
{
  "approved_for_deletion": true,
  "deletion_approval_status": "APPROVED"
}
```

Do not use `rm -rf`. Use an exact-path deletion command only after the approval report is true.
