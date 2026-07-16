import { describe, expect, it } from 'vitest';

import { evaluateFraming } from '../utils/framing-evaluator';
import { createSyntheticFrame } from '../services/holistic.service';

describe('framing evaluator', () => {
  it('accepts a centered synthetic frame', () => {
    const evaluation = evaluateFraming(createSyntheticFrame(1, 100));
    expect(evaluation.isReady).toBe(true);
    expect(evaluation.leftHandVisible).toBe(true);
  });

  it('warns when lighting is too dark', () => {
    const frame = createSyntheticFrame(1, 100);
    frame.metadata.averageLuminance = 20;
    const evaluation = evaluateFraming(frame);
    expect(evaluation.warnings).toContain('TOO_DARK');
  });
});
