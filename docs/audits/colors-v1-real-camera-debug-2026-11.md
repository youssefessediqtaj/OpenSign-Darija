# COLORS_V1 real-camera debugging — 2026-11

## Scope and evidence

The user reported red, pink and white attempts in a 47-second camera recording and a green
candidate. Earlier descriptions of the short recording differ; individual gesture labels
and exact boundaries in the recordings are **UNCONFIRMED**. The recordings show the preview,
capture, some rejected attempts and a green diagnostic candidate. They do not contain the
original network payloads, so they cannot establish which frames entered that request or
prove whether attempts were merged. No video or landmark sequences were retained by this
investigation or included in Git. Screenshots and temporary cropped clips were processed
locally and deleted after measurement.

## Confirmed findings

1. The existing one-epoch, nine-output GRU ranks `green` first on **all ten existing
   in-sample source feature sequences**. Registry label order and ONNX shape are checked;
   `green` is the actual highest logit, not an index-to-label mapping error. This is a
   diagnostic observation on training data, not generalization accuracy. Raw scores are
   logits, not calibrated probabilities.
2. Three approximate screen-recording crops, decoded locally after cropping the mirrored
   on-screen preview and flipping it back, also rank `green` first. These are reconstructed
   crops with different decoding, extraction, timestamps and hand visibility; they are
   **not** the browser's original recorded input tensors or isolated verified gestures.
3. At the maximum capture duration, the segmenter previously returned a `reliable` segment
   even when no stable end was detected. It now rejects that attempt as an unreliable
   boundary. This is a confirmed code defect, not proof that it caused the recorded result.
4. A locally rejected payload previously raised a generic error and switched the UI to
   “Service momentanément indisponible”; it was possible to show an outage for insufficient
   visible hands/body. All HTTP errors were also prefixed `MODEL_NOT_READY`. The UI now
   reports capture problems separately and distinguishes gateway errors, network errors,
   timeouts, invalid input, model loading and model inference states. Historical recordings
   contain no original error trace, so the particular cause of each observed outage remains
   **UNCONFIRMED**.
5. Backend schemas enforce normalized coordinates within ±20; the browser previously
   checked only finiteness, allowing an avoidable 422. Browser validation now enforces the
   existing backend boundary, without changing the feature contract.

## Model observations

Each source row below is an input used to build the smoke training package; the first three
names are raw-logit rank order, and numbers are uncalibrated raw logits. The two blue
variants are separate inputs mapped to the same semantic class.

| Source label / variant | First | Second | Third |
|---|---|---|---|
| black | green 0.4145 | red 0.2773 | orange 0.1383 |
| blue 01 | green 0.4090 | red 0.2855 | orange 0.1533 |
| blue 02 | green 0.4089 | red 0.2875 | orange 0.1623 |
| brown | green 0.3709 | red 0.2692 | orange 0.1604 |
| green | green 0.3616 | red 0.2671 | orange 0.1594 |
| orange | green 0.5152 | red 0.2894 | blue 0.2205 |
| pink | green 0.3797 | red 0.2675 | orange 0.1851 |
| red | green 0.4230 | red 0.2716 | orange 0.1629 |
| white | green 0.3934 | red 0.2658 | orange 0.1042 |
| yellow | green 0.3767 | red 0.2610 | orange 0.1284 |

Approximate screen crops (top-three logits; unverified boundaries and labels):

| Recording / crop seconds | Usable / detector frames | Top three (raw logits) | Tensor mean / std / range |
|---|---:|---|---|
| Long / 1–6 | 28/75 | green 0.5591, red 0.3311, blue 0.3177 | 0.212 / 1.372 / -4.071…7.159 |
| Long / 11–17 | 27/90 | green 0.5054, red 0.3478, blue 0.2989 | 0.175 / 1.359 / -4.351…7.243 |
| Short / 11–17 | 17/90 | green 0.5458, red 0.3419, blue 0.2983 | 0.139 / 1.436 / -3.807…7.886 |

Source tensors had means -0.041…0.173, standard deviations 0.992…1.232 and overall
extrema -4.890…4.724. These descriptive ranges do not establish a statistical shift or
explain causality; crops contain recording/scaling/preview artifacts and limited samples.
The visible camera traces and the in-sample collapse are consistent with a broken model,
but segmentation quality and real-camera transfer still require direct evidence.

## Segmentation and feature compatibility

The segmenter keeps pre-roll, triggers on motion or stable signing-zone dwell, ends after
stable energy and post-roll, and requires a rest/cooldown before another automatic sign.
A maximum-duration capture now fails closed. Reset clears pre-roll, captured frames and
baseline, aborts the request and increments the session generation; tests cover stale
responses, camera continuity and reset isolation. Stability is a heuristic, not proof
that a whole linguistic sign was captured; gestures may still end early or merge if no
rest is detected, and this has not been verified for the supplied recording. Detection
requires both visible shoulders and a hand. No-hand, inadequate input, uncertain boundary
and model failures must not become confirmed color decisions.

Both paths use MediaPipe Holistic VIDEO mode, 33 pose + 21 left-hand + 21 right-hand
points, shoulder-center origin and 3D shoulder-width scaling, zero-filled missing points,
binary masks, valid-frame filtering and uniform sampling/repetition to 60 × 75 × 3.
The ONNX input is float32 and the output is [batch, 9]. The browser sends the video element
unmirrored to MediaPipe; CSS mirrors only the preview. Screen-recording reconstructions
were flipped back, but preview crop, aspect ratio and screen/video codecs make handedness
and tensor equality unproven. Missing masks gate input validity; the GRU takes landmarks
only, so masks themselves are not ONNX inputs. Source clips use full unreviewed boundaries
and offline extraction; the browser uses online segmentation. The prior matched 12-frame
comparison measured tensor mean absolute difference 0.00416, p95 0.01647 and max 0.07111,
without a defined acceptance tolerance. See `colors-v1-phase3-reliability-2026-11.md`.

## Local attempt diagnostics and manual procedure

Start the local stack with `make up`, then open
`http://localhost:8081/app/recognition?diagnostics=1`. The diagnostic panel is available
only with the local experimental build/token on a loopback same-origin page. It retains at
most 30 attempts in component memory; reload clears them. No raw landmarks, frames,
video, session identity or personal information are recorded or automatically transmitted
by this panel. Each completed or rejected capture records an ephemeral attempt ID, relative
segment times, captured/usable counts, hand/pose coverage, sequence length, completion and
rejection reason, request state, schema/model version and, when inference ran, [1,9] shape
and the top three raw uncalibrated scores. Rejected or aborted attempts cannot supply
model output. Copy the panel only intentionally; its timing and diagnostic data are local.

For an actual physical-camera check, perform each reference RED three times independently,
pressing **Refaire un signe** after each result; then do the same for PINK and WHITE. Keep
shoulders and hands in view, return to rest between attempts, and wait for each result.
Inspect one new attempt record per capture and note rejection, completion, model version,
raw ranking and whether adjacent attempts overlap. Do not assume a given sign is correct
without a qualified linguistic review. Reset should retain the camera, abort a pending
request, record its abort and prevent a late response from replacing the new result.
A test fixture or screen replay does not prove physical-camera accuracy.

## Remaining work and next experiment

No model was retrained, promoted or made to speak; legacy weights remain untouched. The
ten source clips, single-epoch training and unreviewed boundaries cannot support a credible
signer-independent recognition claim. Collect more consented, independently performed,
linguistically reviewed repetitions and negative examples; document lineage and split by
signer before tuning or calibration. First verify individual real-camera segmentation and
browser/offline preprocessing on the same timestamped sequences, then compare a simple
baseline against a small retrained candidate on held-out signers. Evaluate rejection and
out-of-vocabulary behavior before choosing any threshold. More data alone does not prove
reliability. Physical-camera nine-attempt testing remains pending.

## Verification

`make test-all` passed: architecture/contracts/privacy 14, API 81, inference 33,
ML 52, speech 9, frontend 54, Playwright 8 passed and one physical-camera-fixture test
skipped. Ruff, MyPy, frontend lint and production build passed as part of the target. After a final diagnostic
bookkeeping adjustment, the nine focused workspace tests, frontend lint and build passed again.
Synthetic browser tests exercise three separate reset attempts, late response cancellation,
local diagnostic fields and no speech; they are not camera-accuracy tests.

Local Docker API, inference and web were rebuilt; health is healthy. A valid landmark
fixture through the actual gateway returned `UNKNOWN_SIGN`, ONNX output shape [1,9] and
three raw logits with tracing enabled; tracing disabled returned no ranked details and
legacy word inference returned 404. A Chromium fake-device check confirmed that the
local Docker diagnostics panel opens with camera preview. It did not demonstrate
physical-camera segmentation or correct color recognition.
