import { describe, expect, it } from 'vitest';

import { evaluateWordCaptureGate } from '../services/capture-state.service';
import type { FramingEvaluation } from '../types/framing.types';

const readyEvaluation: FramingEvaluation = {
  isReady: true,
  faceVisible: true,
  torsoVisible: true,
  leftHandVisible: true,
  rightHandVisible: false,
  shouldersVisible: true,
  centered: true,
  distance: 'correct',
  lighting: 'good',
  stability: 'stable',
  warnings: [],
};

describe('word capture state gate', () => {
  it('blocks capture while detector is loading', () => {
    const gate = evaluateWordCaptureGate({
      mode: 'word',
      cameraReady: true,
      detectorStatus: 'loading',
      evaluation: readyEvaluation,
      recorderPhase: 'idle',
      isSubmitting: false,
      mockCamera: false,
    });
    expect(gate.canCapture).toBe(false);
    expect(gate.reason).toMatch(/moteur de detection/i);
  });

  it('allows capture only when camera, detector and framing are ready', () => {
    const gate = evaluateWordCaptureGate({
      mode: 'word',
      cameraReady: true,
      detectorStatus: 'ready',
      evaluation: readyEvaluation,
      recorderPhase: 'idle',
      isSubmitting: false,
      mockCamera: false,
    });
    expect(gate.canCapture).toBe(true);
  });
});
