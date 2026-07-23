import { describe, expect, it } from 'vitest';

import { AutomaticSignSegmenter } from '../domain/automatic-segmentation';
import {
  AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT,
  createAutomaticTestFrame,
  createSyntheticFrame,
} from '../services/holistic';
import type { RecognitionFlowState, SegmentedSign } from '../state/recognition-flow';

describe('AutomaticSignSegmenter', () => {
  it('stays waiting when hands are absent or stationary at rest', () => {
    const segmenter = new AutomaticSignSegmenter();
    const events = [
      ...Array.from({ length: 12 }, (_, index) =>
        segmenter.ingest(createSyntheticFrame(index, index * 70, 'no-hands', false), 'WAITING_FOR_SIGN'),
      ),
      ...Array.from({ length: 12 }, (_, offset) => {
        const index = offset + 12;
        return segmenter.ingest(
          createSyntheticFrame(index, index * 70, 'rest', false),
          'WAITING_FOR_SIGN',
        );
      }),
    ];

    expect(events.every((event) => event.type === 'none')).toBe(true);
  });

  it('produces zero false captures during 60 simulated seconds without hands and at rest', () => {
    const segmenter = new AutomaticSignSegmenter();
    const completedOrStarted = [];
    for (let index = 0; index < 900; index += 1) {
      const kind = index < 450 ? 'no-hands' : 'rest';
      const event = segmenter.ingest(
        createSyntheticFrame(index, index * (1000 / 15), kind, false),
        'WAITING_FOR_SIGN',
      );
      if (event.type === 'started' || event.type === 'completed') completedOrStarted.push(event);
    }
    expect(completedOrStarted).toHaveLength(0);
  });

  it('recognizes a held static sign after a jittery no-hands cold start', () => {
    const segmenter = new AutomaticSignSegmenter();
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    const completed: SegmentedSign[] = [];
    let index = 0;

    const ingest = (kind: 'no-hands' | 'gesture-a', moving: boolean) => {
      const event = segmenter.ingest(createSyntheticFrame(index, index * 70, kind, moving), state);
      index += 1;
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'completed') completed.push(event.segment);
    };

    for (let count = 0; count < 20; count += 1) ingest('no-hands', true);
    for (let count = 0; count < 35 && completed.length === 0; count += 1) {
      ingest('gesture-a', false);
    }

    expect(completed).toHaveLength(1);
    expect(completed[0].kind).toBe('static');
    expect(completed[0].frames).toHaveLength(60);
  });

  it('starts on dynamic movement, keeps capturing while moving, and ends on stability', () => {
    const segmenter = new AutomaticSignSegmenter();
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    let index = 0;
    let started = false;
    let completed: SegmentedSign | null = null;

    const ingest = (kind: 'rest' | 'gesture-a', moving: boolean) => {
      const event = segmenter.ingest(createSyntheticFrame(index, index * 70, kind, moving), state);
      index += 1;
      if (event.type === 'started') {
        started = true;
        state = 'CAPTURING';
      }
      if (event.type === 'completed') completed = event.segment;
      return event;
    };

    for (let count = 0; count < 12; count += 1) ingest('rest', false);
    for (let count = 0; count < 12; count += 1) ingest('gesture-a', true);
    expect(started).toBe(true);
    expect(state).toBe('CAPTURING');
    expect(completed).toBeNull();

    for (let count = 0; count < 15; count += 1) ingest('gesture-a', false);
    expect(completed).not.toBeNull();
  });

  it('detects two dynamic signs across rest and cooldown without manual capture', () => {
    const segmenter = new AutomaticSignSegmenter();
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    const segments: SegmentedSign[] = [];

    for (let index = 0; index < AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT; index += 1) {
      const timestamp = index * 70;
      const event = segmenter.ingest(createAutomaticTestFrame(index, timestamp), state);
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'completed') {
        segments.push(event.segment);
        segmenter.beginCooldown(timestamp);
        state = 'COOLDOWN';
      }
      if (event.type === 'reset') state = 'WAITING_FOR_SIGN';
    }

    expect(segments).toHaveLength(2);
    expect(segments.map((segment) => segment.kind)).toEqual(['dynamic', 'dynamic']);
    expect(segments.every((segment) => segment.frames.length === 60)).toBe(true);
    expect(segments.every((segment) => segment.reliable)).toBe(true);
    expect(state).toBe('WAITING_FOR_SIGN');
  });

  it('recognizes a held static pose after learning a rest baseline', () => {
    const segmenter = new AutomaticSignSegmenter();
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    const completed: SegmentedSign[] = [];
    let index = 0;

    const ingest = (kind: 'rest' | 'gesture-a', moving: boolean) => {
      const event = segmenter.ingest(createSyntheticFrame(index, index * 70, kind, moving), state);
      index += 1;
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'completed') completed.push(event.segment);
    };

    for (let count = 0; count < 12; count += 1) ingest('rest', false);
    for (let count = 0; count < 30 && completed.length === 0; count += 1) ingest('gesture-a', false);

    expect(completed).toHaveLength(1);
    expect(completed[0].kind).toBe('static');
    expect(completed[0].frames).toHaveLength(60);
  });

  it('rejects a segment that ends before the minimum duration', () => {
    const segmenter = new AutomaticSignSegmenter({
      preRollFrames: 1,
      minimumDurationMs: 1_000,
      endStableMs: 0,
      postRollFrames: 1,
    });
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    let rejection = '';

    const frames = [
      createSyntheticFrame(0, 0, 'rest', false),
      createSyntheticFrame(1, 70, 'gesture-a', true),
      createSyntheticFrame(2, 140, 'gesture-a', true),
      createSyntheticFrame(3, 210, 'gesture-a', false),
      createSyntheticFrame(4, 280, 'gesture-a', false),
    ];
    frames.forEach((frame) => {
      const event = segmenter.ingest(frame, state);
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'rejected') rejection = event.reason;
    });

    expect(rejection).toBe('too_short');
  });

  it('finalizes safely when a moving sign reaches the maximum duration', () => {
    const segmenter = new AutomaticSignSegmenter({
      preRollFrames: 1,
      minimumDurationMs: 200,
      maximumDurationMs: 700,
    });
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    const completed: SegmentedSign[] = [];

    for (let index = 0; index < 30 && completed.length === 0; index += 1) {
      const kind = index < 3 ? 'rest' : 'gesture-a';
      const event = segmenter.ingest(
        createSyntheticFrame(index, index * 70, kind, kind !== 'rest'),
        state,
      );
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'completed') completed.push(event.segment);
    }

    expect(completed).toHaveLength(1);
    expect(completed[0].endedAtMs - completed[0].startedAtMs).toBeGreaterThanOrEqual(700);
    expect(completed[0].frames).toHaveLength(60);
  });

  it('requires a real rest reset before it can detect another sign', () => {
    const segmenter = new AutomaticSignSegmenter({ cooldownMs: 300, resetStableMs: 210 });
    let state: RecognitionFlowState = 'WAITING_FOR_SIGN';
    let index = 0;
    let completed = 0;

    const ingest = (kind: 'rest' | 'gesture-a', moving: boolean) => {
      const timestamp = index * 70;
      const event = segmenter.ingest(createSyntheticFrame(index, timestamp, kind, moving), state);
      index += 1;
      if (event.type === 'started') state = 'CAPTURING';
      if (event.type === 'completed') {
        completed += 1;
        segmenter.beginCooldown(timestamp);
        state = 'COOLDOWN';
      }
      if (event.type === 'reset') state = 'WAITING_FOR_SIGN';
    };

    for (let count = 0; count < 12; count += 1) ingest('rest', false);
    for (let count = 0; count < 18; count += 1) ingest('gesture-a', true);
    for (let count = 0; count < 15; count += 1) ingest('gesture-a', false);
    expect(completed).toBe(1);
    expect(state).toBe('COOLDOWN');

    for (let count = 0; count < 30; count += 1) ingest('gesture-a', false);
    expect(completed).toBe(1);
    expect(state).toBe('COOLDOWN');

    for (let count = 0; count < 10; count += 1) ingest('rest', false);
    expect(state).toBe('WAITING_FOR_SIGN');
  });

  it('suppresses a highly similar sequence inside cooldown but not a different one', () => {
    const segmenter = new AutomaticSignSegmenter();
    const frames = Array.from({ length: 10 }, (_, index) =>
      createSyntheticFrame(index, index * 70, 'gesture-a', false),
    );
    const original: SegmentedSign = {
      id: 'original',
      kind: 'static',
      reliable: true,
      startedAtMs: 0,
      endedAtMs: 700,
      sourceFrames: frames,
      frames,
      usableFrameCount: 10,
      descriptor: [0.1, 0.2, 0.3],
    };
    segmenter.rememberRecognized(original, 1_000);
    segmenter.beginCooldown(1_000);

    expect(segmenter.shouldSuppressDuplicate({ ...original, id: 'same' }, 1_100)).toBe(true);
    expect(
      segmenter.shouldSuppressDuplicate(
        { ...original, id: 'different', descriptor: [1, 1, 1] },
        1_100,
      ),
    ).toBe(false);
  });
});
