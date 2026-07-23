import { describe, expect, it } from 'vitest';

import { createSyntheticFrame } from '../services/holistic.service';
import { normalizeSchemaV1Frame } from '../services/landmark-schema-v1-normalizer.service';
import {
  createLandmarkSequence,
  finalizeWordRecognitionPayloadV1,
  toWordLandmarkPayload,
  validateWordLandmarkPayload,
  validateWordRecognitionPayloadV1,
} from '../services/sequence-validator.service';
import validWordFixture from '../test-fixtures/word-recognition-v1-valid.json';
import type { HolisticFrame, NormalizedLandmark } from '../types/landmark.types';
import type { WordLandmarkSequencePayload } from '../types/sequence.types';
import { uniformSample } from '../utils/sequence-sampling';
import { calculateSequenceQuality } from '../utils/sequence-statistics';
import fixtureExpected from './fixtures/schema-v1-expected.json';
import fixtureInput from './fixtures/schema-v1-input.json';

const DYNAMIC_SEGMENTATION = {
  kind: 'dynamic' as const,
  reliable: true,
  usableFrameCount: 35,
};

function landmarksFromSparse(source: Record<string, number[]>, expected: number): NormalizedLandmark[] {
  return Array.from({ length: expected }, (_, index) => {
    const values = source[String(index)];
    return values
      ? { x: values[0], y: values[1], z: values[2] }
      : { x: Number.NaN, y: Number.NaN, z: Number.NaN };
  });
}

function fixtureFrame(): HolisticFrame {
  return {
    timestampMs: 120,
    frameIndex: 0,
    pose: landmarksFromSparse(fixtureInput.pose, 33),
    face: [],
    leftHand: landmarksFromSparse(fixtureInput.left_hand, 21),
    rightHand: landmarksFromSparse(fixtureInput.right_hand, 21),
    metadata: {
      videoWidth: 640,
      videoHeight: 480,
      processingTimeMs: 3,
      faceDetected: false,
      leftHandDetected: true,
      rightHandDetected: false,
      poseDetected: true,
    },
  };
}

function validPayload() {
  const frames = Array.from({ length: 35 }, (_, index) =>
    createSyntheticFrame(index, index * 70),
  );
  return toWordLandmarkPayload(
    createLandmarkSequence(frames, '2026-07-16T12:00:00Z'),
    undefined,
    DYNAMIC_SEGMENTATION,
  );
}

describe('word sequence contract', () => {
  it('uniformly samples to a fixed frame count', () => {
    expect(uniformSample([1, 2, 3], 60)).toHaveLength(60);
  });

  it('reports genuinely missing detector frames instead of hard-coding zero', () => {
    const visible = createSyntheticFrame(0, 0, 'rest', false);
    const missing: HolisticFrame = {
      ...createSyntheticFrame(1, 70, 'no-hands', false),
      pose: [],
      metadata: {
        ...visible.metadata,
        poseDetected: false,
        leftHandDetected: false,
        rightHandDetected: false,
      },
    };
    expect(calculateSequenceQuality([visible, missing], 70).missingFrameRatio).toBe(0.5);
  });

  it('creates an anonymous schema-v1 payload with automatic boundary metadata', () => {
    const payload = validPayload();
    expect(payload).toMatchObject({
      recognition_mode: 'WORD_ISOLATED',
      feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1',
      target_frame_count: 60,
      landmark_count: 75,
      coordinate_count: 3,
      segmentation_kind: 'dynamic',
      segmentation_reliable: true,
      usable_frame_count: 35,
    });
    expect(payload).not.toHaveProperty('anonymous_session_id');
    expect(payload.frames).toHaveLength(60);
    expect(payload.frames.every((frame) => frame.landmarks.length === 75)).toBe(true);
    expect(payload.frames.every((frame) => frame.landmarks.every((point) => point.length === 3))).toBe(true);
    expect(validateWordLandmarkPayload(payload)).toEqual([]);
  });

  it('uses a UUID, ISO capture time, and relative monotonic timestamps', () => {
    const frames = Array.from({ length: 35 }, (_, index) =>
      createSyntheticFrame(index, 20_000 + index * 70),
    );
    const sequence = createLandmarkSequence(
      frames,
      new Date('2026-07-19T16:00:00.000Z').toISOString(),
    );
    const payload = finalizeWordRecognitionPayloadV1(
      sequence,
      undefined,
      DYNAMIC_SEGMENTATION,
    );
    expect(payload.sequence_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
    expect(Date.parse(payload.captured_at)).toBeGreaterThan(0);
    expect(payload.frames[0].timestamp_ms).toBe(0);
    expect(payload.frames[payload.frames.length - 1]?.timestamp_ms).toBeLessThanOrEqual(10_000);
    expect(
      payload.frames.every(
        (frame, index) => index === 0 || frame.timestamp_ms > payload.frames[index - 1].timestamp_ms,
      ),
    ).toBe(true);
    expect(validateWordRecognitionPayloadV1(payload, { rawFrameCount: 35, validFrameCount: 35 }).valid).toBe(true);
  });

  it('accepts reliable static signs even when movement is low', () => {
    const frames = Array.from({ length: 20 }, (_, index) =>
      createSyntheticFrame(index, index * 70, 'gesture-a', false),
    );
    const payload = toWordLandmarkPayload(
      createLandmarkSequence(frames, '2026-07-16T12:00:00Z'),
      undefined,
      { kind: 'static', reliable: true, usableFrameCount: 20 },
    );
    expect(payload.quality.movement_score).toBe(0);
    expect(validateWordRecognitionPayloadV1(payload).valid).toBe(true);
  });

  it('validates the shared word fixture', () => {
    const result = validateWordRecognitionPayloadV1(validWordFixture as WordLandmarkSequencePayload);
    expect(result.valid).toBe(true);
    expect(validWordFixture.frames).toHaveLength(60);
  });

  it('rejects malformed shape, boundary metadata, masks, and non-finite coordinates', () => {
    const payload = validPayload();
    const codes = (candidate: WordLandmarkSequencePayload) =>
      validateWordRecognitionPayloadV1(candidate).errors.map((error) => error.code);

    expect(codes({ ...payload, frames: payload.frames.slice(0, 59) })).toContain('invalid_frame_count');
    expect(codes({ ...payload, segmentation_reliable: false })).toContain('unreliable_segmentation');
    expect(codes({ ...payload, usable_frame_count: 2 })).toContain('invalid_usable_frame_count');
    expect(
      codes({
        ...payload,
        frames: [
          { ...payload.frames[0], landmarks: payload.frames[0].landmarks.slice(0, 74) },
          ...payload.frames.slice(1),
        ],
      }),
    ).toContain('invalid_landmark_count');
    expect(
      codes({
        ...payload,
        frames: [
          {
            ...payload.frames[0],
            presence_mask: [2, ...payload.frames[0].presence_mask.slice(1)],
          },
          ...payload.frames.slice(1),
        ],
      }),
    ).toContain('invalid_presence_mask');
    expect(
      codes({
        ...payload,
        frames: [
          {
            ...payload.frames[0],
            landmarks: [[Number.NaN, 0, 0], ...payload.frames[0].landmarks.slice(1)],
          },
          ...payload.frames.slice(1),
        ],
      }),
    ).toContain('non_finite_coordinate');
  });

  it('matches the shared schema-v1 normalization fixture', () => {
    const frame = normalizeSchemaV1Frame(fixtureFrame(), 0);
    expect([frame.landmarks.length, frame.landmarks[0].length]).toEqual(fixtureExpected.frame_shape);
    expect(frame.presence_mask.slice(0, 33).reduce((sum, value) => sum + value, 0)).toBe(
      fixtureExpected.presence_sums.pose,
    );
    expect(frame.presence_mask.slice(33, 54).reduce((sum, value) => sum + value, 0)).toBe(
      fixtureExpected.presence_sums.left_hand,
    );
    expect(frame.presence_mask.slice(54).reduce((sum, value) => sum + value, 0)).toBe(
      fixtureExpected.presence_sums.right_hand,
    );
    Object.entries(fixtureExpected.selected_landmarks).forEach(([index, values]) => {
      expect(frame.landmarks[Number(index)]).toEqual(values);
    });
  });
});
