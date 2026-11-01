# COLORS_V1 experimental feature contract

Version: `COLORS_V1_VIDEO_V1_EXPERIMENTAL`; input geometry remains
`OPEN_SIGNE_LANDMARK_SCHEMA_V1`. This version describes the isolated color experiment,
not a replacement for the active legacy package.

The local source extractor uses MediaPipe Holistic 0.10.35 VIDEO mode and the same
`holistic_landmarker.task` SHA-256 `e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8`
as the browser; both request a CPU delegate and 0.5 pose/hand detection confidence.
Python decodes video with OpenCV and samples based on FFprobe presentation timestamps at
up to 24 detector calls/second. Timestamps passed to MediaPipe are strictly increasing
milliseconds. Browser scheduling uses animation-frame timestamps and a 24 fps target;
its effective rate and decoded camera frames vary. Manual interval bounds require a
source-hash-bound technical approval; otherwise extraction is explicitly provisional.

Frames retain 33 pose points followed by 21 left-hand and 21 right-hand points, XYZ in
MediaPipe normalized image coordinates; facial landmarks are excluded. No mirroring or
hand swapping is performed in the tensor path (the camera preview can be mirrored by
CSS). Shoulders 11 and 12 define the midpoint origin and 3D distance scale; missing
shoulders fall back to origin zero/scale one, although frames with missing shoulders or
both hands are excluded before final sampling. Missing points become zero with a zero
presence mask. Six-decimal normalization is used, and finite points retain their original
left/right block. A uniform, index-based, JavaScript-rounded selection produces 60 frames;
short inputs repeat samples. The tensor is float32 `[batch,60,75,3]`, with a separate
`[60,75]` mask and recorded source timestamps/count for repeated inputs. Index-based
sampling is not temporal interpolation and is sensitive to different input cadences.

On 12 identical PNG frames from a single source, at matching synthetic detector
timestamps, Python and Chromium detected pose on 12/12 frames and the right hand on 7/12;
neither detected the left hand. Across 1,629 common raw coordinates, mean absolute
Python/browser difference was 0.00168, P95 0.00764 and maximum 0.05023. Both paths
selected seven valid frames and the resampled masks matched; final 60×75×3 tensors had
mean absolute difference 0.00416, P95 0.01647 and maximum 0.07111. These numbers are
observations, not acceptance thresholds. Input selection used locally extracted PNGs and
fixed timestamps, so this does not test real camera capture, live segmentation, frame-rate
effects, or generalize to other recordings/devices. It does not establish equivalence.

The reproducible local harness consists of `python -m ml.datasets.colors_v1.parity_prepare`
for a new ignored output directory, then `node scripts/colors-browser-parity.mjs` and
`node scripts/colors-sequence-compare.mjs` from `apps/web` with a local Vite server,
followed by `python -m ml.datasets.colors_v1.parity_compare` from the repository root.
Private frames and detector output must remain outside Git. See the phase-three report
for exact test conditions and the remaining limitations.
