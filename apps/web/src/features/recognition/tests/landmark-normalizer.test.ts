import { describe, expect, it } from 'vitest';

import { compactFrame, FEATURE_NAMES } from '../services/landmark-normalizer.service';
import { createSyntheticFrame } from '../services/holistic.service';

describe('landmark normalizer', () => {
  it('creates fixed features and presence masks', () => {
    const compact = compactFrame(createSyntheticFrame(0, 0), 0);
    expect(compact).not.toBeNull();
    expect(compact?.features).toHaveLength(FEATURE_NAMES.length * 3);
    expect(compact?.presence_mask).toHaveLength(FEATURE_NAMES.length);
  });
});
