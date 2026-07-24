# Dataset Quality Limitations

The local MoSL corpus is useful for a limited local baseline, but it is not sufficient
for production-grade sign-language recognition.

- The manifest contains 2,216 videos, but most normalized labels are singletons or have
  too few usable examples for train/validation/test separation.
- After checksum-collision and label-ambiguity exclusions, 11 labels / 59 samples meet
  the minimum-five training threshold.
- The active user-flow model intentionally uses only three unambiguous lexical labels:
  `اب`, `احب`, and `سوق`.
- Each active class has one validation example and one test example, so closed-set
  accuracy and F1 are unstable.
- Signer identity is absent from local filenames and manifests; signer-independent
  evaluation is therefore `UNCONFIRMED`.
- Physical-camera transfer, lighting robustness, framing robustness, and signer
  diversity are not established.
- Local redistribution rights for the copied videos remain `UNCONFIRMED` until reviewed
  against upstream license evidence.

The safest product behavior is therefore a compact known/UNKNOWN result with no claim of
general translation quality.
