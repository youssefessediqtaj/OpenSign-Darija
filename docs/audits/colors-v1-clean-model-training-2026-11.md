# COLORS_V1 clean learning diagnostic — 2026-11-02

## Dataset and evidence

The ten active clean MP4s were validated and decoded, all source SHA-256 values matched the manifest, and all ten feature files matched source hashes, labels, feature schema and MediaPipe asset. Both blue variants map to blue. Active manifest SHA-256: `634b7acde5d19f5c5d49a7ecd110aacda4cfa0b0a3715b37c36b0d1a56b1ea90`. The previous manifest and all prior artifacts remain separate. The data and labels remain pending review; owner authorization is limited to local experiments.

## Feature diagnostics

Tensor shape is 60 × 75 × 3 for every clip; masks are 60 × 75. Missing percentage counts landmark slots (not missing whole frames). Hand coverage is detected frames / detector frames, measured before resampling. Repeated positions are uniform resampling of valid observations, not zero padding. Variance includes zero-filled absent landmarks; temporal variance averages per-coordinate variance across the 60 samples. Source hash values appear in the clean-video inventory and private feature diagnostic JSON.

| Video / label | Variant | Valid | Hand frames | Missing % | Variance | Temporal variance | Range | Duration s | Repeats |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| 01_jaune.mp4 / yellow | yellow_variant_01 | 43 | 43/71 | 28.0 | 1.330 | 0.00637 | -4.52…4.01 | 2.96 | 17 |
| 02_blanc.mp4 / white | white_variant_01 | 40 | 40/74 | 28.0 | 1.304 | 0.00457 | -4.53…4.10 | 3.09 | 20 |
| 03_noir.mp4 / black | black_variant_01 | 48 | 48/100 | 28.0 | 1.352 | 0.00672 | -4.87…4.36 | 4.17 | 12 |
| 04_rouge.mp4 / red | red_variant_01 | 40 | 40/81 | 28.0 | 1.260 | 0.00363 | -4.67…4.11 | 3.38 | 20 |
| 05_vert.mp4 / green | green_variant_01 | 40 | 40/86 | 28.0 | 1.186 | 0.01021 | -4.51…4.10 | 3.59 | 20 |
| 06_rose.mp4 / pink | pink_variant_01 | 43 | 43/75 | 28.0 | 0.889 | 0.04526 | -4.45…3.91 | 3.13 | 17 |
| 07_marron.mp4 / brown | brown_variant_01 | 59 | 59/100 | 28.0 | 1.209 | 0.00374 | -4.54…4.04 | 4.17 | 1 |
| 08_bleu_1.mp4 / blue | blue_variant_01 | 35 | 35/88 | 28.0 | 1.376 | 0.00966 | -5.16…4.29 | 3.67 | 25 |
| 09_bleu_2.mp4 / blue | blue_variant_02 | 24 | 24/62 | 28.0 | 1.361 | 0.00630 | -4.82…4.18 | 2.59 | 36 |
| 10_orange.mp4 / orange | orange_variant_01 | 33 | 33/76 | 7.9 | 1.201 | 0.04983 | -4.31…4.00 | 3.17 | 27 |

No NaNs, infinities, empty/all-zero sequences or invalid shapes were found. Missing points are zeroed. Nine clips have zero left-hand mask and full right-hand mask among selected samples; orange has left/right coverage of 88.3% / 83.3%. This is detector output, not independent verification of anatomical handedness. Code uses the established pose/left/right ordering, but an independent anatomical audit and full camera parity remain outstanding. Variance is nonzero in every clip; the model can distinguish these inputs, but this does not prove it learned linguistically relevant movement. Full-clip extraction and all suggested boundaries remain unreviewed. The run explicitly used the local-only `--allow-pending-review` override, recorded in its report.


### Source fingerprints

| Video | SHA-256 |
|---|---|
| 01_jaune.mp4 | `9b7a3782fa44b656ef347cb0497d9863864715356c10a557ab2f5bfcd097d826` |
| 02_blanc.mp4 | `602a872e499876a4bdaaef060599f4d035ae539d3a4d34874868bdc8b8bbfcab` |
| 03_noir.mp4 | `1bd47cf3541ac3d10c43bed11840589a3706a8e984b1717abe2d5c0bd291af2c` |
| 04_rouge.mp4 | `6e3a68e26818b5ffbc270d974e6c2ad13ce21fda56f17a7fba967bd40836626e` |
| 05_vert.mp4 | `81e01862cd579a61c52cea889dbe067547c7dbaace85d1b06fdbc6c9e4d8be29` |
| 06_rose.mp4 | `0838580ae80da6cdc0dbbcb7378622602d6a6a7a4591aa7cd5462da4f9c6954a` |
| 07_marron.mp4 | `c312b5d4d05263e1ee985769991bcc721130d9409b3776937f18ca9029ab4e92` |
| 08_bleu_1.mp4 | `a06d085253114987bdd4e33851060664652ac41cd5b9f39348cb7430f790878a` |
| 09_bleu_2.mp4 | `662a5765d4c0fe4a5360a186ea3bdbd9334473ba041c6d0a4ebd6d7bf71fade3` |
| 10_orange.mp4 | `2e645eba0d3726936713fa31530e6463f7ebae2b95fa60b292597f052526ad0a` |

## Collapse investigation

On all ten cleaned tensors, both the historical one-epoch checkpoint and the cleaned one-epoch checkpoint rank green first (1/10 correct in-sample each). The historical checkpoint has a different manifest fingerprint and now fails the current-dataset runtime gate. The green result is a real argmax, not an output-index mapping defect: sorted nine-class labels agree across configuration, checkpoints, runtime and gateway. The model uses 60×75×3 input, one bidirectional GRU with hidden size 16 and nine logits; cross-entropy, AdamW, batch 10 and gradient checks are operational. In the controlled run, all 14 trainable parameter tensors received finite nonzero gradients, initial global gradient norm 0.911431. One-epoch underfitting is supported by successful longer fitting, but it is not proven to be the sole cause of the old camera behavior; detector transfer, boundaries and real inputs remain unverified.

## IN-SAMPLE LEARNING DIAGNOSTICS

Fixed seed 42, AdamW learning rate 0.003, weight decay 0.01, cross-entropy, batch size 10, dropout 0.1, hidden size 16; 105 epochs out of a maximum of 120. Initial evaluation loss 2.232184, final 0.123278. Early stopping required three checks with 10/10 and loss below 0.25. This is memorization of the training inputs, not independent accuracy.

| Video | Expected | Predicted | In-sample result |
|---|---|---|---|
| 01_jaune.mp4 | yellow | yellow | Correct |
| 02_blanc.mp4 | white | white | Correct |
| 03_noir.mp4 | black | black | Correct |
| 04_rouge.mp4 | red | red | Correct |
| 05_vert.mp4 | green | green | Correct |
| 06_rose.mp4 | pink | pink | Correct |
| 07_marron.mp4 | brown | brown | Correct |
| 08_bleu_1.mp4 | blue | blue | Correct |
| 09_bleu_2.mp4 | blue | blue | Correct |
| 10_orange.mp4 | orange | orange | Correct |

## Template baseline and ONNX

The existing weighted template matcher has zero self-distance for all ten samples and nearest-other distances 0.046416–0.633789. This proves only distinguishability from these exact samples; neither self-matching nor the optional dynamic-time-warp comparison establishes generalization. The template matcher is the simpler useful local reference, with unknown threshold uncalibrated. The trained GRU reached 10/10 in-sample, also without independent evaluation.

The new checkpoint and ONNX are under `artifacts/colors_v1/experimental/gru-phase4-provisional-v1/`. ONNX input `[batch,60,75,3]`, output `[batch,9]`; all ten outputs matched PyTorch with maximum absolute error 9.53674316e-07 and identical argmax. A repeated ONNX batch was bit-identical on this machine. Dynamic-GRU export emits a batch-size warning; parity was actually checked for batch 10 as well as export batch 1. The selected runtime handles batch 1; other batch sizes remain outside that tested evidence.

## Local diagnostic selection

The immutable registry `artifacts/colors_v1/registry-gru-phase4-provisional-v1.json` identifies version `0.2.0-provisional-v1`, experiment `gru-phase4-provisional-v1`, clean manifest fingerprint, uncalibrated and inactive status. It is not automatically selected. The configured version and registry must agree, the feature schema and label order must match, and the manifest fingerprint must match the registry; failures return `MODEL_NOT_READY` without falling back. File hashes are checked before each cached lookup so a changed registry or active manifest is revalidated. Ordinary routes do not enable the experiment.

After the affected local services have been built, explicitly select the model for this local diagnostic stack with:

```bash
COLORS_EXPERIMENTAL_REGISTRY_FILE=registry-gru-phase4-provisional-v1.json \
COLORS_EXPERIMENTAL_MODEL_VERSION=0.2.0-provisional-v1 \
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --no-deps --force-recreate inference
```

Open `http://localhost:8081/app/recognition?diagnostics=1`. Attempts display model and experiment identifiers, top-three raw logits, capture diagnostics and status. The underlying result remains `UNKNOWN_SIGN`, and the candidate is experimental and never spoken. Restarting without explicit selection returns to the historical configuration, which is rejected against the clean manifest.

## Limitations and next experiment

No signer-independent held-out data, qualified linguistic approval, verified sign intervals, rights/consent verification, calibrated unknown detection, or physical-camera generalization has been established. Collect independently consented original recordings across multiple known signers, obtain separate linguistic and boundary reviews, keep signer-disjoint held-out splits, and evaluate unknown gestures and browser/video preprocessing before choosing between templates and GRU.

The reproducible local run used:

```bash
ml/.venv/bin/python -m ml.datasets.colors_v1.learning_diagnostics \
  --manifest ml/data/colors_v1/source_v1/manifest.json \
  --source-root ml/data/colors_v1/source_v1 \
  --features ml/data/colors_v1/features_clean_v2 \
  --asset ml/assets/mediapipe/holistic_landmarker.task \
  --output artifacts/colors_v1/experimental/gru-phase4-provisional-v1 \
  --old-checkpoint artifacts/colors_v1/experimental/gru-smoke-v1/checkpoint.pt \
  --clean-smoke-checkpoint artifacts/colors_v1/experimental/gru-smoke-clean-v2/checkpoint.pt \
  --allow-pending-review
```

The tool refuses to overwrite an experiment; use a new output directory for a repeat. Private feature tensors remain in the feature directory; their hashes, logits, loss history and gradient checks are recorded in the local experiment report.

## Tests and local gateway

`make test-all` passed with the full frontend production build: architecture 14, API 81, inference 35, ML 58, speech 9, frontend unit 54, and Playwright 8 passed / 1 skipped. Ruff, MyPy and ESLint passed. The skipped Playwright case requires a validated fake-camera video. The source-video validation command decoded all ten videos without errors. Focused tests also covered explicit version selection, a changed manifest invalidating the cached model, label mapping, feature provenance, nonzero gradients, ONNX export and fail-closed model loading.

A local TestClient run selected the clean registry and returned red for its red training tensor with `UNKNOWN_SIGN`; the stale registry returned `MODEL_NOT_READY`. The explicitly selected clean model was also tested through the Docker gateway: HTTP 200, version `0.2.0-provisional-v1`, experiment `gru-phase4-provisional-v1`, red candidate, `UNKNOWN_SIGN`, and output shape `[1,9]`. The default selection was then restored and returned `MODEL_NOT_READY` because the old registry fingerprint does not match the cleaned manifest. This was an in-sample payload check, not a physical-camera evaluation.

The initial temporary Docker overlay attempt failed while Docker read an unrelated `/private/tmp` socket lock. Retrying the overlay Dockerfile via standard input succeeded; source hashes inside the final inference container matched the workspace before the gateway retest. No persistent volume was deleted.
