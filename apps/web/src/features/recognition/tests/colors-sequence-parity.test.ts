import { expect, it } from 'vitest';
import fixture from './colors-sequence-fixture.json';
import { uniformSample } from '../domain/resample-landmark-sequence';

it('selects the same short and long sequence indices as the Python fixture', () => {
  for (const item of fixture) {
    const frames = Array.from({ length: item.count }, (_, index) => index);
    expect(uniformSample(frames, item.target)).toEqual(item.indices);
  }
});

import sequence from './colors-sequence-values.json';
import { normalizeSchemaV1Frame } from '../domain/normalize-landmarks';
import type { HolisticFrame, NormalizedLandmark } from '../domain/landmarks';

it('normalizes and resamples a full sequence with missing right hands', () => {
  const frames = sequence.hand_x.map((x, index) => {
    const pose = Array<NormalizedLandmark>(33);
    pose[11] = { x: 0.25, y: 0.5, z: 0 };
    pose[12] = { x: 0.75, y: 0.5, z: 0 };
    return { pose, leftHand: [{ x, y: 0.5, z: 0 }], rightHand: [], face: [],
      timestampMs: index * 40, frameIndex: index,
      metadata: { videoWidth: 1, videoHeight: 1, processingTimeMs: 0, faceDetected: false,
        leftHandDetected: true, rightHandDetected: false, poseDetected: true } } satisfies HolisticFrame;
  });
  const normalized = uniformSample(frames, 5).map((frame, index) => normalizeSchemaV1Frame(frame, index));
  expect(normalized.map((frame) => frame.landmarks[33][0])).toEqual(sequence.expected_normalized_hand_x);
  expect(normalized.map((frame) => frame.presence_mask[54])).toEqual([0, 0, 0, 0, 0]);
});
