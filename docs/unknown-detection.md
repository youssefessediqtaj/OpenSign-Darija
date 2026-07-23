# UNKNOWN detection

OpenSigne Darija does not force every sequence into a supported class.

Before inference, the API returns UNKNOWN for invalid duration, unreliable segmentation,
too few usable hand frames, insufficient pose/hand visibility, excessive missing frames,
or inadequate movement on a dynamic segment. Static segments are exempt from the dynamic
motion rule but still require reliable browser dwell segmentation and visibility.

For usable sequences, the model applies validation-calibrated temperature scaling and
requires both:

- maximum class probability at or above `unknown_threshold`;
- Top-1 minus Top-2 probability margin at or above `margin_threshold`.

The active three-class package uses temperature `0.5`, probability threshold `0.0`, and
margin threshold `0.8492977619171143`. The zero probability threshold is not an absence of
rejection: the high Top-1/Top-2 margin requirement is the operative rejector.

The calibration report contains the exact validation-only selection rule, known
acceptance, OOV rejection, false acceptance, expected calibration error, and untouched
test evaluation. Safety is preferred over speaking a guessed word; the frontend never
sends UNKNOWN to speech.

Calibration used only three known validation examples and 68 disjoint OOV examples. The
selected point accepted 66.67% of correctly classified known validation examples, rejected
58.82% of validation OOV examples, and falsely accepted 41.18%. On the untouched test
evaluation, it accepted 66.67% of the three known examples, rejected only 44.12% of 68 OOV
examples, and falsely accepted 55.88%.

The active vocabulary is only `اب`, `احب`, and `سوق`, with one validation and one test
example per class. Those sample sizes and the weak test OOV rejection make this a limited
local baseline, **not a production safety guarantee**.
