# Retention policy template

`DATA_RETENTION_DAYS` has no repository default because a legal retention period
must be approved by the controller. The maintenance target is report-only:

`make contributions-retention-check`

It writes a timestamped report under `artifacts/reports/` and never deletes.
Execution exists only in the lower-level CLI and requires both `--execute` and
`--approved-execution`, an accountable actor, and prior controller approval.
Contribution-specific retention reports are ignored by Git because they contain
pseudonymous contribution references. The report omits private object keys;
operators must use the secured repository for execution details.

| State | Retention decision | Current status |
| --- | --- | --- |
| pending | maximum review wait and abandonment handling | UNCONFIRMED |
| rejected | short post-review retention or prompt deletion | UNCONFIRMED |
| withdrawal requested | immediate exclusion and verified deletion SLA | UNCONFIRMED |
| approved quarantine | period before versioned release | UNCONFIRMED |
| versioned dataset release | release retention, lineage, withdrawal propagation | UNCONFIRMED |
| minimal deletion audit | lawful minimum fields and duration | UNCONFIRMED |

Approved dataset releases are excluded from automatic retention execution because
their lineage and downstream handling need a distinct controller-approved policy.
