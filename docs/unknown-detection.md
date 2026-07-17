# Unknown Detection

The first strategy is transparent:

- return `unknown` when max probability is below the model threshold;
- return `uncertain` when the Top-1/Top-2 margin is too small;
- return `known` only when both confidence and margin are acceptable.

Thresholds are stored per model version in `thresholds.json` and in the backend `ModelVersion.thresholds_json`.
