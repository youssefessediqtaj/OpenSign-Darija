# OpenSign Darija Model Card

## Model

No real recognition model is active yet.

The phase 4 codebase now contains the training, evaluation, calibration, ONNX export, registry, and inference integration scaffolding for `opensign-pilot-gru`, but the current local dataset is not valid for training.

## Status

`UNTRAINED / NOT ACTIVE`

Reason:

- Dataset version `0.1.0` local manifest has zero items.
- Dataset status is not `READY` or `PUBLISHED`.
- No class meets the minimum contributor/repetition thresholds.
- No signer-independent test metrics exist.

## Intended Architecture

- Input: `features` `[batch, 30, 63]`, `float32`.
- Input: `presence_mask` `[batch, 30, 21]`, `float32`.
- Main architecture: 2-layer bidirectional GRU with masked temporal pooling.
- Output: logits, calibrated with temperature scaling.
- Decision strategy: max probability threshold plus Top-1/Top-2 margin.

## Metrics

UNCONFIRMED. No training or signer-independent evaluation has been run on a valid dataset.

## Limitations

- Isolated signs only.
- Limited pilot vocabulary only after data thresholds are met.
- No continuous phrase recognition.
- No medical/legal certification.
- No public release of weights.
