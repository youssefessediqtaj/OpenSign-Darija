# Inference log checklist

Inspect:

```bash
docker compose logs -f inference
```

Look for:

- model loading errors
- ONNX Runtime errors
- checksum errors
- schema mismatch
- prediction exceptions
- repeated reloads
- request latency spikes
- accidental landmark dumps

Landmark arrays must never be logged.
