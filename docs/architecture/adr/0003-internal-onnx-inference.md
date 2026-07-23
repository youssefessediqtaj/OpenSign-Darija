# ADR 0003: Internal ONNX Inference

## Status

Accepted.

## Decision

ONNX Runtime is isolated in the internal inference service.

## Consequences

The API validates public requests and calls inference through a typed client.
Inference validates the package, warms the model when configured, bounds
concurrency, performs calibrated UNKNOWN rejection, and fails closed when the
package is invalid.
