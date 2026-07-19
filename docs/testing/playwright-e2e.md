# Playwright E2E

Date: 2026-07-19

Playwright runs from the existing frontend config:

```bash
cd apps/web
npm run test:e2e
```

Current suite result:

```text
9 passed
```

Recognition coverage includes:

- Camera permission denial.
- Missing camera error.
- Mock camera word capture.
- `WORD_ISOLATED` request route `/api/v1/recognitions/word`.
- Word request payload shape: 60 frames, 75 landmarks, 3 coordinates, no raw video/image/audio fields.
- Alphabet request route `/api/v1/recognitions/alphabet`.
- Alphabet request payload shape: 63 features, 21 presence-mask values, no raw video/image/audio fields.
- Local rejection of too-short sequences.
- Backend-unavailable recovery while keeping camera controls usable.

This does not replace human physical-camera validation.
