# Data-subject rights process

Public deletion by contribution ID alone is forbidden. The UUID is a case
reference, not authentication.

1. The requester contacts `DATA_RIGHTS_CONTACT` and supplies the contribution ID.
2. The controller applies its approved, proportionate identity-verification
   procedure. That procedure is currently **UNCONFIRMED** and must not request
   excessive new data.
3. The operator records an access, rectification, opposition, or withdrawal case
   outside public routes. Use the local withdrawal command after authorization:
   `python -m app.cli.contributions request-withdrawal <uuid> --actor <operator>`.
4. `WITHDRAWAL_REQUESTED` immediately clears processing eligibility and excludes
   the contribution from export.
5. After the controller approves deletion, run the guarded local delete command.
   It deletes the private video, nulls name/age/city, keeps only minimal event and
   technical audit evidence, sets `DELETED`, and prevents future export.
6. Confirm completion to the requester through the controller’s approved channel.

Review states are `PENDING`, `REJECTED`, and `APPROVED_FOR_DATASET`. Data-subject
states are `ACTIVE`, `WITHDRAWAL_REQUESTED`, and `DELETED`. A rejected item is
still personal data until retention or an approved deletion action is executed.
