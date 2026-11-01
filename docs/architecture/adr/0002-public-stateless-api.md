# ADR 0002: Public Stateless API

## Status

Accepted for the recognition path; amended by the separate contribution workflow described below.

## Decision

The recognition path remains stateless and exposes system, word-recognition,
and supported-sign speech routes. The later optional contribution workflow adds private
SQLite metadata and video quarantine, isolated from recognition and closed by default.

## Consequences

Authentication, database migrations, Redis, MinIO, admin pages, dataset management,
and message-builder runtime code are not active responsibilities. Future product
ideas should re-enter through a new design, not dormant runtime modules.
