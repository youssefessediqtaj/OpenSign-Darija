# ADR 0005: Automatic Isolated Sign Flow

## Status

Accepted.

## Decision

The public product uses automatic sign-start and sign-end detection rather than
manual capture buttons.

## Consequences

The UI has one camera activation action, then waits for signs. Known results may
trigger speech once; UNKNOWN is never spoken. Cooldown and duplicate suppression
prevent repeated recognition of the same held sign.
