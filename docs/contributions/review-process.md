# Local review process

There is no public admin interface. Review occurs on a secured operator host.

1. `make contributions-list-pending`
2. `make contributions-inspect ID=<uuid>`
3. Inspect the private video and verify: label matches the sign; face/hands and
   quality are adequate; consent is active; age is adult; no unrelated person,
   unsafe content, duplicate, or withdrawal is present.
4. Approve only after every check:
   `make contributions-approve ID=<uuid> REVIEWER=<operator> CONFIRM_REVIEW=YES`
5. Or reject with a non-PII reason:
   `make contributions-reject ID=<uuid> REVIEWER=<operator> REASON='<reason>'`

Approval only sets `APPROVED_FOR_DATASET`; it does not copy the video or start ML.
An explicit immutable staging release requires:

`make contributions-export-approved VERSION=<version> CONFIRM_EXPORT=YES`

The release contains UUID filenames, manifest, checksums, provenance, consent
status, and review status. It excludes full name, city, and age. Withdrawn or
deleted records are excluded by the repository query.
