# Pre-architecture-refactor baseline

Captured on 2026-07-23 before structural changes, from commit
`a831df8fbc825a02d0b6a41753c22a89ba25d117` on branch
`refactor/professional-architecture`.

## Source state and safety

- `git status --short` was clean before the branch was created.
- `git branch --show-current` reported `main`; the working branch was then created
  with `git switch -c refactor/professional-architecture`.
- The last five commits began with `a831df8 simplify and correct the complete
  application`.
- `git diff --stat` and `git diff` were empty.
- No user work was overwritten. No commit, push, reset, clean, model training, or
  protected-asset mutation was performed.

## Automated baseline

`make test-all` passed:

| Area | Tests | Other gates |
| --- | ---: | --- |
| Public API | 54 passed | Ruff and strict MyPy passed |
| Inference | 25 passed | Ruff and strict MyPy passed |
| Offline ML | 31 passed | Ruff passed; expected Torch/ONNX warnings only |
| Speech | 8 passed | Ruff and strict MyPy passed |
| Frontend | 30 passed | ESLint, TypeScript, and Vite production build passed |
| Playwright default run | 4 passed, 1 skipped | Real-Docker fake-camera test requires an explicit Y4M path |

The production Docker Playwright gate was then run explicitly with the fixed
two-sign Y4M camera. All 5 tests passed. It observed two automatic known-sign
decisions, exactly two corresponding speech calls, UNKNOWN silence, duplicate
suppression, no forbidden/direct-service request, no raw-media field, and at least
15 capture FPS.

`make compose-check`, `docker compose build`, and `docker compose up -d` passed.
`docker compose ps` reported API, inference, and speech healthy; web and Nginx were
running; only Nginx exposed host port `8081`.

## Runtime contract

The API OpenAPI document contained exactly:

```text
/health
/api/v1/health
/api/v1/version
/api/v1/recognitions/word
/api/v1/speech/sign
```

Gateway health reported API `1.0.0` healthy with healthy inference and speech
dependencies. Inference reported the active non-mock
`mosl-isolated-sign-v1` model, version `1.0.0`, with
`OPEN_SIGNE_LANDMARK_SCHEMA_V1`. Speech reported the local `ar-MA` default and
local `ar` fallback voices.

The public routes remained `/` and `/app/recognition`. Browser MediaPipe and
segmentation produced exactly 60 frames × 75 landmarks × 3 coordinates. The
browser called only `/api`; Nginx kept inference and speech internal.

## Protected assets and canonical output

- ONNX SHA-256:
  `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`
- Model checksum-manifest SHA-256:
  `707367e05abc7840a1330fecbc8fd7d946e6decb82a88ecd0d618197e01034f6`
- Dataset manifest SHA-256:
  `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`
- Supported labels, in model order: `اب`, `احب`, `سوق`
- Input: `landmarks`, `[batch, 60, 75, 3]`, float32
- Output: `logits`, `[batch, 3]`, float32
- Dataset manifest records fully rehashed against raw files: 2,216/2,216 matched

For the fixed processed fixture
`9887333505c8b7a2b006ad55a9209c0943f0f58f712663f6c5445e30f9c7ceed.npz`,
ONNX Runtime produced logits:

```text
[-2.4934840202331543, 1.7240511178970337, -0.6624970436096191]
```

Temperature-calibrated probabilities in label order were:

```text
[0.00021525139163713902, 0.9914032816886902, 0.008381485939025879]
```

The accepted top label was `احب`; its probability was `0.9914032816886902`
and its margin was `0.9830217957496643`.

The full machine-readable evidence is in
`artifacts/reports/pre-architecture-refactor-baseline.json`; protected file-level
hashes and the canonical tensor output are in
`artifacts/reports/architecture-refactor-protected-assets.json`.

## Honest limitation

Automated Chromium used a deterministic Y4M camera through the production Docker
gateway. A person repeating the flow with the physical FaceTime HD camera remains
`UNCONFIRMED`; this architecture-only task does not claim otherwise.
