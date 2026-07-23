# OpenSigne Darija recognition model card

The active runtime package is `artifacts/models/mosl-isolated-sign-v1/`; its bundled
`model-card.md`, metrics, calibration, schema, and checksums are authoritative.

- architecture: lightweight Transformer encoder
- input: `[batch, 60, 75, 3]` float32 landmarks
- parameters: 85,699
- recorded local training duration: 1.789 seconds
- minimum-five eligible scope: 11 labels / 59 samples, split 37/11/11
- active scope: 3 labels / 15 samples, split 9/3/3
- active labels: `اب` (أَبٌ), `احب` (أَحَبَّ), `سوق` (سُوقٌ)
- held-out closed-set Top-1: 0.6667 on **three** examples
- held-out Top-3: 1.0000 on **three** examples
- held-out macro F1: 0.5556
- held-out balanced accuracy: 0.6667
- held-out OOV rejection: 44.12% on 68 OOV examples
- held-out OOV false acceptance: 55.88%
- held-out known-correct acceptance: 66.67% on three known examples
- ONNX size: 411,736 bytes
- ONNX SHA-256: `24678fc01c86bb64a47f832ae800bd475e788a91c5b103122115a37fcdd6ad54`
- ONNX parity max absolute error: `1.1920928955078125e-7`; Top-K match: true
- local CPU ONNX latency: 0.647 ms mean / 0.735 ms P95 over 40 runs
- status: limited local baseline, **not production-ready**

Scope/architecture/calibration were selected from validation only. Signer identities are
unavailable, and each active class has exactly one validation and one test example. The
100% validation closed-set score therefore represents only three samples and is not a
generalization claim. Calibration uses temperature 0.5 and margin threshold
0.8492977619 (maximum-probability threshold 0.0). It accepted 66.67% of known examples
while rejecting 58.82% of 68 OOV examples on validation; untouched test OOV rejection fell
to 44.12%. This is isolated-sign recognition, not continuous translation, and it is not
certified for medical, legal, financial, emergency, or production use.

`mosl-word-smoke-v1` is `TECHNICAL_SMOKE_ONLY`, `NOT_USER_MODEL`, and
`NOT_PRODUCTION_READY`.
