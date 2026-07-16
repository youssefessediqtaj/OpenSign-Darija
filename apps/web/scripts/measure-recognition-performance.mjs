import { performance } from 'node:perf_hooks';

const targetFrames = 30;
const featureCount = 63;
const presenceCount = 21;

const started = performance.now();
const frames = Array.from({ length: targetFrames }, (_, index) => ({
  index,
  timestamp_ms: index * 66,
  features: Array.from({ length: featureCount }, (_, featureIndex) =>
    Number((Math.sin(index + featureIndex) * 0.25).toFixed(6)),
  ),
  presence_mask: Array.from({ length: presenceCount }, () => 1),
}));
const payload = {
  sequence_id: '123e4567-e89b-12d3-a456-426614174000',
  captured_at: new Date().toISOString(),
  duration_ms: 1980,
  source_fps: 15,
  target_frame_count: targetFrames,
  coordinate_format: 'torso_normalized_v1',
  feature_schema_version: '1.0.0',
  frames,
  quality: {
    detected_hand_ratio: 1,
    detected_face_ratio: 1,
    detected_pose_ratio: 1,
    missing_frame_ratio: 0,
    movement_score: 0.5,
  },
};
const json = JSON.stringify(payload);
const elapsed = performance.now() - started;

console.table({
  targetFrames,
  featureCount,
  payloadBytes: Buffer.byteLength(json),
  syntheticBuildMs: Number(elapsed.toFixed(3)),
});
