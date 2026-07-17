# ONNX Export

Export command:

```bash
python -m ml.export.export_onnx --checkpoint path/to/model.pt --output path/to/model.onnx
```

Validation command:

```bash
python -m ml.export.validate_onnx --checkpoint path/to/model.pt --onnx path/to/model.onnx
```

The export keeps `float32`, uses named inputs `features` and `presence_mask`, and must pass parity before registration. The current local run cannot export because no checkpoint exists.
