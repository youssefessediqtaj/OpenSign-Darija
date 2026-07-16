import { describe, expect, it } from 'vitest';

import { createSyntheticFrame } from '../services/holistic.service';
import { createLandmarkSequence, toCompactPayload, validateCompactPayload } from '../services/sequence-validator.service';
import { uniformSample } from '../utils/sequence-sampling';
import { calculateSequenceQuality } from '../utils/sequence-statistics';

describe('sequence utilities', () => {
  it('uniformly samples to a fixed frame count', () => {
    expect(uniformSample([1, 2, 3], 5)).toHaveLength(5);
  });

  it('calculates quality and compact payload', () => {
    const frames = Array.from({ length: 35 }, (_, index) => createSyntheticFrame(index, index * 70));
    const quality = calculateSequenceQuality(frames, 2200);
    expect(quality.detectedHandRatio).toBeGreaterThan(0.9);
    const sequence = createLandmarkSequence(frames, '2026-07-16T12:00:00Z');
    const payload = toCompactPayload(sequence, 'guest-test');
    expect(payload.frames).toHaveLength(30);
    expect(validateCompactPayload(payload)).toEqual([]);
  });
});
