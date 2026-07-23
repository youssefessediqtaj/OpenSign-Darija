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
