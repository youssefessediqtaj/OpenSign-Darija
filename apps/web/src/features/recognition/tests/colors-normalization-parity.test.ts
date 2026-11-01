import { describe, expect, it } from 'vitest';
import fixture from './colors-normalization-fixture.json';
import { normalizeSchemaV1Frame } from '../domain/normalize-landmarks';
import type { HolisticFrame, NormalizedLandmark } from '../domain/landmarks';

function group(points: Record<string, number[]>, length: number): NormalizedLandmark[] {
  const result = Array<NormalizedLandmark>(length);
  for (const [index, [x, y, z]] of Object.entries(points)) result[Number(index)] = { x, y, z };
  return result;
}

describe('shared Python/browser landmark fixture', () => {
  it('uses the same coordinate transform and missing-point mask', () => {
    const frame: HolisticFrame = {
      timestampMs: 0, frameIndex: 0,
      pose: group(fixture.pose, 33), leftHand: group(fixture.left_hand, 21),
      rightHand: group(fixture.right_hand, 21), face: [],
      metadata: { videoWidth: 0, videoHeight: 0, processingTimeMs: 0, faceDetected: false,
        leftHandDetected: true, rightHandDetected: true, poseDetected: true },
    };
    const result = normalizeSchemaV1Frame(frame, 0);
    for (const [index, expected] of Object.entries(fixture.expected)) {
      expect(result.landmarks[Number(index)]).toEqual(expected);
      expect(result.presence_mask[Number(index)]).toBe(1);
    }
    expect(result.landmarks[0]).toEqual([0, 0, 0]);
    expect(result.presence_mask[0]).toBe(0);
  });
});
