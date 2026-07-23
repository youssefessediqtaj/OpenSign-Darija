# Performance evidence

Run the deterministic browser pipeline benchmark:

```bash
cd apps/web
npm run perf:recognition
```

It writes `artifacts/reports/frontend-automatic-segmentation-benchmark.json`. The report
measures segmenter computational throughput, 60-second rest false captures, two-sign
state reset, held-pose suppression, exact V1 payload build time/size, and configured
start/end/cooldown timing. These are synthetic-landmark measurements, not physical-camera
accuracy claims.

With Docker healthy, run:

```bash
make benchmark-inference
make benchmark-speech
```

Those commands write public-API and offline-speech latency reports. The model package
also contains direct ONNX average/P95 latency and parity evidence.

Real MediaPipe FPS and drops, camera permission-to-ready time, sign-end-to-visible-text,
text-to-audible time, physical rest false captures, and lighting/framing sensitivity must
be measured with an actual target camera. Missing hardware evidence remains
`UNCONFIRMED`; configured cadence is not reported as measured physical FPS.
