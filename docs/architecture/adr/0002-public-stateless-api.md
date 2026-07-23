# ADR 0002: Public Stateless API

## Status

Accepted.

## Decision

The public FastAPI service is stateless and exposes only system, word-recognition,
and supported-sign speech routes.

## Consequences

Authentication, database migrations, Redis, MinIO, admin pages, dataset management,
and message-builder runtime code are not active responsibilities. Future product
ideas should re-enter through a new design, not dormant runtime modules.
