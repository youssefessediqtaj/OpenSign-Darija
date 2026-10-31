# Model-development boundary

The enforced lifecycle is:

```text
COLLECT → HUMAN REVIEW → APPROVED RELEASE → DATASET VERSION
→ PREPROCESSING → TRAINING → EVALUATION → MODEL REVIEW → MANUAL ACTIVATION
```

Upload code has no import or command path to `ml`, preprocessing, training,
evaluation, ONNX export, model packages, supported vocabulary, or activation.
Review approval only changes quarantined metadata. Export creates a new ignored
staging release under `ml/data/contributions/releases/<version>/`; it never writes
the protected local MoSL dataset or active model directory.

Every later arrow requires an explicit human-run action, reproducibility evidence,
signer-independent evaluation, privacy review, model review, and manual activation.
The current active ONNX, package, vocabulary, checksums, and evaluation metrics
remain authoritative and unchanged.
