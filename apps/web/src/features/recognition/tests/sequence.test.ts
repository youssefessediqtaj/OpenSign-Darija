import { describe, expect, it } from 'vitest';

import { createSyntheticFrame } from '../services/holistic.service';
import { normalizeSchemaV1Frame } from '../services/landmark-schema-v1-normalizer.service';
import {
  createLandmarkSequence,
  finalizeWordRecognitionPayloadV1,
  toCompactPayload,
  toWordLandmarkPayload,
  validateCompactPayload,
  validateWordLandmarkPayload,
  validateWordRecognitionPayloadV1,
} from '../services/sequence-validator.service';
import fixtureExpected from './fixtures/schema-v1-expected.json';
import fixtureInput from './fixtures/schema-v1-input.json';
import validWordFixture from '../test-fixtures/word-recognition-v1-valid.json';
import type { HolisticFrame, NormalizedLandmark } from '../types/landmark.types';
import type { WordLandmarkSequencePayload } from '../types/sequence.types';
import { uniformSample } from '../utils/sequence-sampling';
import { calculateSequenceQuality } from '../utils/sequence-statistics';

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
      averageLuminance: 0.5,
    },
  };
}

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
    expect(payload.frames).toHaveLength(60);
    expect(validateCompactPayload(payload)).toEqual([]);
  });

  it('creates schema v1 word payloads with 75 ordered landmarks', () => {
    const frames = Array.from({ length: 35 }, (_, index) => createSyntheticFrame(index, index * 70));
    const sequence = createLandmarkSequence(frames, '2026-07-16T12:00:00Z');
    const payload = toWordLandmarkPayload(sequence, 'guest-test');
    expect(payload.feature_schema_version).toBe('OPEN_SIGNE_LANDMARK_SCHEMA_V1');
    expect(payload.recognition_mode).toBe('WORD_ISOLATED');
    expect(payload.landmark_count).toBe(75);
    expect(payload.coordinate_count).toBe(3);
    expect(payload.frames).toHaveLength(60);
    expect(payload.frames[0].landmarks).toHaveLength(75);
    expect(payload.frames[0].landmarks[0]).toHaveLength(3);
    expect(validateWordLandmarkPayload(payload)).toEqual([]);
  });

  it('uses valid UUIDs, ISO timestamps and relative frame timestamps for word payloads', () => {
    const frames = Array.from({ length: 35 }, (_, index) => createSyntheticFrame(index, 20_000 + index * 70));
    const sequence = createLandmarkSequence(frames, new Date('2026-07-19T16:00:00.000Z').toISOString());
    const payload = finalizeWordRecognitionPayloadV1(sequence, 'guest-test');
    expect(payload.sequence_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
    expect(Date.parse(payload.captured_at)).toBeGreaterThan(0);
    expect(payload.frames[0].timestamp_ms).toBe(0);
    expect(payload.frames[payload.frames.length - 1]?.timestamp_ms).toBeLessThanOrEqual(10_000);
    expect(validateWordRecognitionPayloadV1(payload, { rawFrameCount: 35, validFrameCount: 35 }).valid).toBe(true);
  });

  it('validates the shared word recognition fixture', () => {
    const result = validateWordRecognitionPayloadV1(validWordFixture as WordLandmarkSequencePayload);
    expect(result.valid).toBe(true);
    expect(validWordFixture.frames).toHaveLength(60);
    expect(validWordFixture.frames[0].landmarks).toHaveLength(75);
    expect(validWordFixture.frames[0].landmarks[0]).toHaveLength(3);
    expect(validWordFixture.frames[0].presence_mask).toHaveLength(75);
  });

  it('rejects malformed word payload shapes and non-finite coordinates', () => {
    const frames = Array.from({ length: 35 }, (_, index) => createSyntheticFrame(index, index * 70));
    const payload = toWordLandmarkPayload(createLandmarkSequence(frames, '2026-07-16T12:00:00Z'), 'guest-test');
    const invalidFrameCount = { ...payload, frames: payload.frames.slice(0, 59) };
    expect(validateWordRecognitionPayloadV1(invalidFrameCount).errors.map((error) => error.code)).toContain(
      'invalid_frame_count',
    );
    const invalidLandmarkCount = {
      ...payload,
      frames: [{ ...payload.frames[0], landmarks: payload.frames[0].landmarks.slice(0, 74) }, ...payload.frames.slice(1)],
    };
    expect(validateWordRecognitionPayloadV1(invalidLandmarkCount).errors.map((error) => error.code)).toContain(
      'invalid_landmark_count',
    );
    const invalidCoordinateCount = {
      ...payload,
      frames: [
        {
          ...payload.frames[0],
          landmarks: [[0.1, 0.2], ...payload.frames[0].landmarks.slice(1)],
        },
        ...payload.frames.slice(1),
      ],
    };
    expect(validateWordRecognitionPayloadV1(invalidCoordinateCount).errors.map((error) => error.code)).toContain(
      'invalid_coordinate_count',
    );
    const invalidMask = {
      ...payload,
      frames: [{ ...payload.frames[0], presence_mask: [2, ...payload.frames[0].presence_mask.slice(1)] }, ...payload.frames.slice(1)],
    };
    expect(validateWordRecognitionPayloadV1(invalidMask).errors.map((error) => error.code)).toContain(
      'invalid_presence_mask',
    );
    const nonFinite = {
      ...payload,
      frames: [
        {
          ...payload.frames[0],
          landmarks: [[Number.NaN, 0, 0], ...payload.frames[0].landmarks.slice(1)],
        },
        ...payload.frames.slice(1),
      ],
    };
    expect(validateWordRecognitionPayloadV1(nonFinite).errors.map((error) => error.code)).toContain(
      'non_finite_coordinate',
    );
    const infinite = {
      ...payload,
      frames: [
        {
          ...payload.frames[0],
          landmarks: [[Number.POSITIVE_INFINITY, 0, 0], ...payload.frames[0].landmarks.slice(1)],
        },
        ...payload.frames.slice(1),
      ],
    };
    expect(validateWordRecognitionPayloadV1(infinite).errors.map((error) => error.code)).toContain(
      'non_finite_coordinate',
    );
    const undefinedCoordinate = {
      ...payload,
      frames: [
        {
          ...payload.frames[0],
          landmarks: [[undefined as unknown as number, 0, 0], ...payload.frames[0].landmarks.slice(1)],
        },
        ...payload.frames.slice(1),
      ],
    };
    expect(validateWordRecognitionPayloadV1(undefinedCoordinate).errors.map((error) => error.code)).toContain(
      'non_finite_coordinate',
    );
  });

  it('matches the shared schema v1 normalization fixture', () => {
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
    Object.entries(fixtureExpected.selected_presence).forEach(([index, value]) => {
      expect(frame.presence_mask[Number(index)]).toBe(value);
    });
  });
});
