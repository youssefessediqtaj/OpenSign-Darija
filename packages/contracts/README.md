# Versioned contracts

`recognition-v1.schema.json` is the language-neutral authority for the exact
browser → API 60 × 75 × 3 request and compact recognized/UNKNOWN response. Closed
objects make raw-media and unapproved metadata fields invalid.

`speech.schema.json` distinguishes the public supported-sign key from the internal
bounded local synthesis request. The browser never calls the internal service or
supplies arbitrary text.

Parity tests pin TypeScript, API Pydantic, inference Pydantic, shared fixtures, and
Playwright privacy assertions to these schemas. Code generation is intentionally
avoided because it would add more machinery than this small contract needs.

## Ownership

- Owner: cross-project architecture/contract layer.
- Importers/users: `tests/architecture/`, `tests/contracts/`, `tests/privacy/`, API
  schemas, inference schemas, frontend payload builders, and Playwright privacy checks.
- Runtime role: no package code executes in production containers; the JSON schemas are
  the review authority for the closed public contracts.
- Decision: keep `packages/contracts/` because the contracts are genuinely shared and
  not owned by a single service.
