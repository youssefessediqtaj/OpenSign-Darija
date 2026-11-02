# COLORS_V1 GRU learning diagnostics — 2026-11-02

## Findings and scope

The historical GRU's all-green output is reproducible on its original feature set and on
the newly cleaned set. Its input and label wiring are consistent; its gradients are finite
and nonzero. With the same architecture, the new bounded experiment fits all ten current
examples after 105 full-batch updates. The strongest supported explanation is that the
one-update smoke checkpoint was severely undertrained and inherited a seed-dependent output
bias. This experiment does not prove a unique cause for the green logit, assess unseen
signers, or establish a practical recognition model. No model was promoted or activated.

## Dataset and source version

The active manifest is `ml/data/colors_v1/source_v1/manifest.json`, SHA-256
`634b7acde5d19f5c5d49a7ecd110aacda4cfa0b0a3715b37c36b0d1a56b1ea90`. The ten current
MP4 SHA-256 hashes equal the manifest and the matching `features_clean_v2/*.npz` embedded
source hashes; all also reference the current MediaPipe asset SHA-256
`e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8`. No feature
regeneration was needed. Full per-video checksums are in
[the cleaned-video audit](colors-v1-clean-video-update-2026-11.md). The old `features_v1`
cache and the active runtime registry's old one-epoch checkpoint refer to manifest
`7b8c4a6c6f6b2084676b63328f5504793fa094ad9c43982eb4f476efa061220e`; they were not
used for training the new model. The old source filenames are absent from the active source
directory; the historical manifest is retained separately, and old feature files remain.
The old checkpoint was loaded only for comparative
probing, and existing checkpoints, videos and legacy research were preserved. The prior
clean-v2 one-epoch checkpoint uses the current fingerprint but also ranks green first on
all ten cleaned inputs.

All source mappings, boundaries and labels are provisional; technical and linguistic
review, signer identity, source lineage, rights and consent remain pending or unconfirmed.
The user authorized local experimental fitting; no recordings were published. The
controlled script requires a separate explicit `--allow-pending-review` override for
owner-authorized diagnostics and rejects unauthorized, changed, invalid or stale inputs.

## Feature diagnostics

Every row below uses dataset fingerprint `634b7acd…` above, represents 60 × 75 × 3
finite float32 values and a 60 × 75 binary mask, and was checked against the source hash,
label, variant, feature version and MediaPipe asset. Coverage/missing percentages are
landmark-mask fractions, not video-frame detection rates. Missing landmarks are zero;
all sequences have shoulders and at least one hand. Every 60-frame tensor has valid
landmarks and no all-zero frame. Repeated frames come from uniform temporal resampling,
not zero-padding. The entire clip was processed with unreviewed boundaries.

| File | Label / variant | Source SHA-256 prefix | Distinct source frames / repeated | Coverage / missing | Min / max | Mean / std | Nonzero coordinates |
|---|---|---|---:|---:|---:|---:|---:|
| 03_noir.mp4 | black / black_variant_01 | `1bd47cf3541a` | 48 / 12 | 72.00% / 28.00% | -4.872 / 4.363 | -0.022 / 1.163 | 9720 |
| 08_bleu_1.mp4 | blue / blue_variant_01 | `a06d08525311` | 35 / 25 | 72.00% / 28.00% | -5.162 / 4.287 | -0.045 / 1.173 | 9720 |
| 09_bleu_2.mp4 | blue / blue_variant_02 | `662a5765d4c0` | 24 / 36 | 72.00% / 28.00% | -4.820 / 4.184 | -0.022 / 1.167 | 9720 |
| 07_marron.mp4 | brown / brown_variant_01 | `c312b5d4d052` | 59 / 1 | 72.00% / 28.00% | -4.543 / 4.041 | 0.135 / 1.100 | 9720 |
| 05_vert.mp4 | green / green_variant_01 | `81e01862cd57` | 40 / 20 | 72.00% / 28.00% | -4.511 / 4.101 | 0.145 / 1.089 | 9720 |
| 10_orange.mp4 | orange / orange_variant_01 | `2e645eba0d37` | 33 / 27 | 92.07% / 7.93% | -4.313 / 4.005 | 0.054 / 1.096 | 12429 |
| 06_rose.mp4 | pink / pink_variant_01 | `0838580ae80d` | 43 / 17 | 72.00% / 28.00% | -4.446 / 3.909 | 0.164 / 0.943 | 9720 |
| 04_rouge.mp4 | red / red_variant_01 | `6e3a68e26818` | 40 / 20 | 72.00% / 28.00% | -4.666 / 4.106 | 0.082 / 1.123 | 9720 |
| 02_blanc.mp4 | white / white_variant_01 | `602a872e4998` | 40 / 20 | 72.00% / 28.00% | -4.532 / 4.098 | -0.005 / 1.142 | 9720 |
| 01_jaune.mp4 | yellow / yellow_variant_01 | `9b7a3782fa44` | 43 / 17 | 72.00% / 28.00% | -4.522 / 4.012 | 0.098 / 1.153 | 9720 |

No tensor was all zero, non-finite, wrong-shaped, or an exact duplicate. Most masks have
28% missing points because one of the two 21-point hand groups is absent; this does not
mean no hands were detected. Orange has both hands for part of the sampled sequence.
Distinct sampled times range from 24 to 59; the remaining frames are repeated samples.
Each processed clip had 24–59 usable detector frames. No temporal mask identifies those
repeats as duplicates. Flattened raw cosine similarity was 0.9962 for the two blue variants,
0.9947 for brown versus green and 0.9947 for blue variant 02 versus white. These high
similarities include shared pose and zero-filled coordinates; they do not prove duplicated
performances or incorrect labels, but are reasons to inspect hand-specific variation.

## Encoding and architecture

The verified unique label-to-output indices are:

| Index | Semantic class | Index | Semantic class | Index | Semantic class |
|---:|---|---:|---|---:|---|
| 0 | black | 3 | green | 6 | red |
| 1 | blue (both variants) | 4 | orange | 7 | white |
| 2 | brown | 5 | pink | 8 | yellow |

The data loader, configuration, checkpoint labels, inference ONNX decoding, API allowed
labels and frontend candidate vocabulary are checked by regression tests. This does not
establish that provisional human labels are linguistically correct.

The model flattens 75 × 3 = 225 coordinates per frame, projects 225→16, applies LayerNorm,
GELU and dropout 0.1, then uses a one-layer bidirectional GRU (16 units per direction)
and a 32→9 linear logits head. The head uses masked mean pooling of frames whose whole
coordinate tensor is nonzero. Masks are not passed to the GRU; repeated samples and zero
landmarks remain numeric inputs, and recurrence is not packed/masked. In this dataset
all 60 frames are nonzero. PyTorch default initialization is reproducibly seeded at 42.
The smoke trainer used full batch 10, cross entropy on raw logits, AdamW, learning rate
0.001, weight decay 0.01, and exactly **one** update. It used no independent validation.

On original historical source features, the seeded initial network ranked green first
for seven examples and red for three; after the one update it ranked green first for all
ten. Its evaluation cross entropy moved from 2.23191 to 2.21175 and the parameter update
L2 norm was 0.084865. Historical per-class logit standard deviations ranged 0.0096–0.0549,
so outputs varied slightly but rankings collapsed. On the current clean features, both
the historical and clean-smoke checkpoints selected green for all ten; cross entropy was
2.21237 and 2.21285 respectively. Historical and clean-smoke gradient norms were finite
and nonzero (1.0592 and 0.7963 on the measured dropout passes), with gradients in all 14
parameter tensors. This rules out a complete gradient disconnection on those probes,
but not all potential generalization or preprocessing defects. Previous browser/offline
parity and segmentation limitations remain open; see
[real-camera diagnostics](colors-v1-real-camera-debug-2026-11.md).

## Controlled training: in-sample only

Starting from a freshly seeded network and using only current, verified cleaned features,
the predeclared bounded run used 120 maximum epochs, one batch of 10, AdamW learning rate
0.003 and weight decay 0.01, cross entropy and dropout 0.1. It checked deterministic
in-sample evaluation every five epochs and stopped after three checks each had all 10
examples correct and loss <0.25. This stopping condition is solely for a memorization
sanity check, not an unknown threshold or a validation metric. The run stopped at epoch
105; initial evaluation loss was 2.232184, final evaluation loss 0.123278, and all ten
training examples had their own semantic label as argmax. The first and last stochastic
training losses were 2.201403 and 0.146100. Recorded gradient norms on evaluation-check
epochs ranged 0.6220–4.6056; each step was checked for finite loss and finite, nonzero
gradients, and all 14 parameter tensors received gradients in the measured probes.
Training loss, per-check predictions and every final raw score are retained in the local
experiment report. No frame-level train/test split was manufactured.

A repeated run with identical seed and inputs stopped at the same epoch with identical loss
history and logits (maximum difference 0.0); its ONNX SHA-256 matched the first run on this
machine. A final reproduction added per-example predictions at each checkpoint and explicit
parity checks for batches 1, 2 and 10; its loss history, logits and ONNX hash also matched. This reproducibility observation is not a guarantee across platforms.

### In-sample examples and scores

Raw logits are listed in the fixed index order `[black, blue, brown, green, orange, pink,
red, white, yellow]`, rounded to three decimals. They are **not probabilities or
confidence scores**. All rows are from the training inputs.

| Source video | Expected | Argmax | Correct in sample | Raw logits in index order |
|---|---|---|---|---|
| 03_noir.mp4 | black | black | yes | `5.618, 2.360, -1.748, -1.179, -1.587, -2.651, 0.135, -0.887, -2.497` |
| 08_bleu_1.mp4 | blue | blue | yes | `1.231, 5.396, -4.686, -3.771, 0.756, -2.757, -0.954, 0.762, -0.301` |
| 09_bleu_2.mp4 | blue | blue | yes | `0.425, 5.255, -4.864, -3.710, 0.696, -2.524, -0.988, 1.132, 0.474` |
| 07_marron.mp4 | brown | brown | yes | `-0.434, -4.235, 5.681, 4.512, -2.266, 1.284, 2.148, -1.656, 0.160` |
| 05_vert.mp4 | green | green | yes | `-0.363, -3.470, 2.755, 4.266, -0.459, 2.698, 0.439, -2.632, 0.633` |
| 10_orange.mp4 | orange | orange | yes | `-0.958, 1.386, -2.735, -0.126, 5.692, 2.083, -2.715, -2.523, -0.387` |
| 06_rose.mp4 | pink | pink | yes | `-1.368, -2.165, -0.081, 2.026, 1.723, 5.168, -1.591, -2.932, 0.229` |
| 04_rouge.mp4 | red | red | yes | `-0.332, -0.596, 1.165, 0.525, -2.751, -1.403, 4.396, 1.065, 0.333` |
| 02_blanc.mp4 | white | white | yes | `-1.799, 2.161, -1.663, -2.851, -1.725, -3.288, 1.637, 5.060, 0.812` |
| 01_jaune.mp4 | yellow | yellow | yes | `-2.266, 0.108, -1.807, 0.456, 0.000, 0.568, -0.506, -0.478, 5.348` |

## Template and temporal baselines

The existing mask-aware weighted template matcher self-matches every source at distance
zero. That is an identity check, not independent accuracy. We also compared each clip's
nearest **other** clip; a one-per-class dataset makes most of those alternatives necessarily
another class, so they are diagnostic similarity observations only. A simple unconstrained
dynamic-time-warping (DTW) comparison used the same per-landmark shared-mask squared
distance and normalizes the minimum accumulated path cost by its path length. Neither
method has a calibrated acceptance threshold; neither was selected as the runtime model.

| Variant | Nearest other: uniform template | Nearest other: temporal DTW |
|---|---|---|
| black_variant_01 | blue_variant_01 (0.1442) | blue_variant_01 (0.1442) |
| blue_variant_01 | blue_variant_02 (0.0464) | blue_variant_02 (0.0258) |
| blue_variant_02 | blue_variant_01 (0.0464) | blue_variant_01 (0.0258) |
| brown_variant_01 | green_variant_01 (0.0575) | green_variant_01 (0.0397) |
| green_variant_01 | brown_variant_01 (0.0575) | brown_variant_01 (0.0397) |
| orange_variant_01 | red_variant_01 (0.6338) | red_variant_01 (0.6820) |
| pink_variant_01 | green_variant_01 (0.2920) | green_variant_01 (0.1811) |
| red_variant_01 | yellow_variant_01 (0.0981) | yellow_variant_01 (0.0823) |
| white_variant_01 | blue_variant_02 (0.0656) | blue_variant_02 (0.0470) |
| yellow_variant_01 | red_variant_01 (0.0981) | red_variant_01 (0.0823) |

DTW can explain time alignment and both methods need little training, but both may match
unrelated signs, exploit missingness, overfit one signer and lack a known rejection rule.
The GRU can memorize these inputs but also has no independent evidence. This comparison
is not an architecture leaderboard and does not justify replacing the runtime.

## Checkpoint, ONNX and stale-model gate

The experiment writes new owner-only files under
`artifacts/colors_v1/experimental/gru-learning-clean-v2-final-20261102/`: a checkpoint,
ONNX model and detailed JSON report. Its metadata explicitly says `EXPERIMENTAL_INACTIVE`,
`NO_INDEPENDENT_EVALUATION`, and calibration `UNAVAILABLE`; there is no promotion or
speech. Strict checkpoint reload reproduced the PyTorch logits. ONNX Runtime and PyTorch
matched all decoded argmax labels: maximum absolute error was 4.7684e-07 (batch 1) and
9.5368e-07 (batches 2 and 10). This checks tensor/numerical compatibility only.

A fail-closed source-code guard now requires an explicit current dataset manifest and
checks its SHA-256 against the selected experimental registry before loading. The local
Compose configuration mounts the manifest read-only. This task did not rebuild or restart
the application. During the work, the inference container was nonetheless recreated by an
external process, outside the commands run for this task. The observed process now has the
manifest gate: calling its loader with the default historical registry returns
`model dataset fingerprint does not match current manifest`, so that stale model is not
ready in the observed container. No checkpoint produced by this task was selected or
activated. The runtime check compares manifest bytes; it does not hash each source video
on every request. If a source file is modified without updating the manifest, repeat the
full source/feature verification before any future selection. This safeguard is not model
validation or authorization to promote.

To reproduce locally in a new output directory, with the private artifacts present:

```bash
ml/.venv/bin/python -m ml.datasets.colors_v1.learning_diagnostics \
  --manifest ml/data/colors_v1/source_v1/manifest.json \
  --source-root ml/data/colors_v1/source_v1 \
  --features ml/data/colors_v1/features_clean_v2 \
  --asset ml/assets/mediapipe/holistic_landmarker.task \
  --output artifacts/colors_v1/experimental/YOUR_NEW_EXPERIMENT_ID \
  --old-checkpoint artifacts/colors_v1/experimental/gru-smoke-v1/checkpoint.pt \
  --clean-smoke-checkpoint artifacts/colors_v1/experimental/gru-smoke-clean-v2/checkpoint.pt \
  --allow-pending-review
```

Replace `YOUR_NEW_EXPERIMENT_ID` with a new unused directory name. The script refuses to
overwrite any output directory and verifies current sources,
feature/source/asset hashes, schema, masks and mapping before training. A pending-review
override only permits the explicitly authorized local diagnostic; it does not approve
rights, consent or linguistic validity.

## Recommendation and remaining work

Continue to use the GRU **as an inactive research candidate** and retain both template
methods as interpretable diagnostic baselines. Collect multiple independent, consented
performances per variant from multiple signers, plus unknown signs; review labels and
source lineage, use signer-disjoint and lineage-grouped train/validation/test sets, and
measure browser versus offline preprocessing on matching captures. Evaluate independently
before selecting an architecture, calibrating unknown rejection, enabling speech or
activating a new model. The present dataset cannot support an independent evaluation.

## Verification

`make test-all SKIP_WEB_BUILD=1` passed: architecture/contracts/privacy 14, API 81,
inference 35, ML 58, speech 9, frontend 54, browser 8 passed and one real-camera fixture
was skipped. API, inference and speech Ruff/MyPy and frontend/ML lint passed. The
`SKIP_WEB_BUILD=1` opt-out was added so the requested test target runs without the
frontend production rebuild that the user prohibited; the default target still builds.
`docker compose ... config` passed without starting or rebuilding any services. The stale
historical registry was rejected against the current manifest in a direct source-code
check and by the observed running container after its external recreation.
