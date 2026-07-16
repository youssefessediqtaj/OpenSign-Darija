# Performance

Run a synthetic payload measurement:

```bash
cd apps/web
npm run perf:recognition
```

Current local synthetic result on this workspace:

- 30 frames;
- 63 features per frame;
- payload size: 21,351 bytes;
- synthetic payload construction: 1.427 ms.

Real MediaPipe load time, FPS, memory use, and camera latency must be measured on target devices with a webcam enabled. Do not claim production FPS without those measurements.
