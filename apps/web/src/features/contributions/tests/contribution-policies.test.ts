import { describe, expect, it } from 'vitest';

import { createSyntheticFrame } from '../../recognition/services/holistic';
import {
  CONTRIBUTION_SIGN_KEYS,
  DISABLED_PREVIEW_SIGNS,
  isContributionSignKey,
  validateServerCatalog,
} from '../domain/contribution-words';
import { evaluateReadiness } from '../domain/readiness-policy';
import { PREFERRED_RECORDING_MIME_TYPES } from '../domain/recording-policy';

describe('contribution policies', () => {
  it('accepts only the exact five stable sign keys', () => {
    expect(CONTRIBUTION_SIGN_KEYS).toEqual(['salam', 'chokran', 'tabib', 'mosaada', 'maa']);
    expect(isContributionSignKey('salam')).toBe(true);
    expect(isContributionSignKey('arbitrary')).toBe(false);
    expect(validateServerCatalog(DISABLED_PREVIEW_SIGNS)).toHaveLength(5);
    expect(() => validateServerCatalog(DISABLED_PREVIEW_SIGNS.slice(0, 4))).toThrow();
  });

  it('requires face, upper body, one hand, distance and short-term stability', () => {
    const firstFrame = createSyntheticFrame(1, 1000, 'gesture-a', false);
    const first = evaluateReadiness(firstFrame, null);
    expect(first.checks.faceVisible).toBe(true);
    expect(first.checks.leftHandVisible || first.checks.rightHandVisible).toBe(true);
    expect(first.checks.rawReady).toBe(false);
    expect(first.checks.guidance).toBe('Restez stable.');

    const stable = evaluateReadiness(
      createSyntheticFrame(2, 1100, 'gesture-a', false),
      first.anchor,
    );
    expect(stable.checks.rawReady).toBe(true);

    const noHands = evaluateReadiness(
      createSyntheticFrame(3, 1200, 'no-hands', false),
      stable.anchor,
    );
    expect(noHands.checks.rawReady).toBe(false);
    expect(noHands.checks.guidance).toBe('Gardez au moins une main visible.');

    const noFaceFrame = createSyntheticFrame(4, 1300, 'gesture-a', false);
    noFaceFrame.metadata.faceDetected = false;
    const noFace = evaluateReadiness(noFaceFrame, stable.anchor);
    expect(noFace.checks.rawReady).toBe(false);
    expect(noFace.checks.guidance).toMatch(/visage/);
  });

  it('prefers VP9 then VP8 then generic WebM', () => {
    expect(PREFERRED_RECORDING_MIME_TYPES).toEqual([
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8',
      'video/webm',
    ]);
  });
});
