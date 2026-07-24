# MoSL Isolated Sign V1

- Supported signs: **3**
- Selected architecture: `lightweight_transformer`
- Active vocabulary scope: `lexical_min5`
- Minimum-five eligible labels audited: **11**
- Input: `60 x 75 x 3` shoulder-centered landmarks
- Dataset: only the native local OpenSigne MoSL video copy
- Status: limited local baseline; not signer-validated production recognition
- Held-out Top-1: **0.667**
- Held-out macro F1: **0.556**
- Held-out out-of-vocabulary rejection: **0.441**

## Honest limitations

Signer identity is unavailable, so signer-independent performance cannot be measured. 
Each supported class has only five or six independent videos and exactly one test sample. 
Metrics are therefore highly uncertain. Confidence thresholds were selected on validation 
only, using a documented safety Pareto trade-off. Out-of-vocabulary rejection remains below 
a production safety bar, so this package must not be promoted as production-ready. Excluded 
labels are not claimed as recognized vocabulary. This is isolated-sign classification, not 
continuous sign language translation.
