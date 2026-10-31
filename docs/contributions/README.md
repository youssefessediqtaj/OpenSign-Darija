# Community video contributions

The `/contribute` feature is an optional, isolated workflow for adult volunteers
to record one of five server-controlled signs. It does not share state, storage,
routes, or lifecycle actions with automatic recognition.

Public collection status is **closed by default**. `CONTRIBUTION_COLLECTION_ENABLED`
alone is insufficient: every controller, purpose, recipient, retention, rights,
CNDP, notice-version, and reference-video approval value must also be configured.
The current repository contains no approved reference MP4 and therefore must not
be opened for public collection.

| Key | Arabic | Reference identifier | Duration |
| --- | --- | --- | --- |
| `salam` | سلام | `opensigne-reference-salam-v1` | 2–10 s |
| `chokran` | شكرا | `opensigne-reference-chokran-v1` | 2–10 s |
| `tabib` | طبيب | `opensigne-reference-tabib-v1` | 2–10 s |
| `mosaada` | مساعدة | `opensigne-reference-mosaada-v1` | 2–10 s |
| `maa` | ماء | `opensigne-reference-maa-v1` | 2–10 s |

Operational documents:

- [Architecture](architecture.md)
- [Data flow](data-flow.md)
- [Privacy notice template](privacy-notice-template.md)
- [CNDP readiness checklist](cndp-readiness-checklist.md)
- [Data-subject rights process](data-subject-rights-process.md)
- [Reference-video provenance](reference-video-provenance.md)
- [Recording quality](recording-quality.md)
- [Review process](review-process.md)
- [Model-development boundary](model-development-boundary.md)
- [Retention policy template](retention-policy-template.md)
- [Security review](security-review.md)
- [Testing](testing.md)

This documentation is engineering support, not a determination of the applicable
CNDP procedure. The controller must confirm declaration versus prior authorization
with the CNDP or qualified Moroccan counsel.
