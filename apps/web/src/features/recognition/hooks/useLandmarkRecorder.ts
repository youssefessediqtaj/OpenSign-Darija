import { useCallback, useRef, useState } from 'react';

import type { HolisticFrame } from '../types/landmark.types';
import type { CapturePhase } from '../types/recognition.types';
import { createLandmarkSequence, toCompactPayload, validateCompactPayload } from '../services/sequence-validator.service';
import type { CompactLandmarkSequencePayload, LandmarkSequence } from '../types/sequence.types';

export function useLandmarkRecorder(anonymousSessionId: string) {
  const bufferRef = useRef<HolisticFrame[]>([]);
  const startedAtRef = useRef<string | null>(null);
  const [phase, setPhase] = useState<CapturePhase>('idle');
  const [sequence, setSequence] = useState<LandmarkSequence | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const addFrame = useCallback(
    (frame: HolisticFrame) => {
      if (phase !== 'capturing') return;
      if (bufferRef.current.length < 180) bufferRef.current.push(frame);
    },
    [phase],
  );

  const start = useCallback(() => {
    bufferRef.current = [];
    startedAtRef.current = new Date().toISOString();
    setValidationErrors([]);
    setSequence(null);
    setPhase('capturing');
  }, []);

  const cancel = useCallback(() => {
    bufferRef.current = [];
    startedAtRef.current = null;
    setSequence(null);
    setValidationErrors([]);
    setPhase('idle');
  }, []);

  const finish = useCallback((): CompactLandmarkSequencePayload | null => {
    setPhase('validating');
    const nextSequence = createLandmarkSequence(
      [...bufferRef.current],
      startedAtRef.current ?? new Date().toISOString(),
    );
    setSequence(nextSequence);
    const payload = toCompactPayload(nextSequence, anonymousSessionId);
    const errors = nextSequence.quality.valid ? validateCompactPayload(payload) : nextSequence.quality.warnings;
    setValidationErrors(errors);
    bufferRef.current = [];
    if (errors.length > 0) {
      setPhase('error');
      return null;
    }
    setPhase('submitting');
    return payload;
  }, [anonymousSessionId]);

  const markComplete = useCallback(() => setPhase('complete'), []);
  const markError = useCallback((message: string) => {
    setValidationErrors([message]);
    setPhase('error');
  }, []);

  return {
    phase,
    sequence,
    validationErrors,
    frameCount: bufferRef.current.length,
    addFrame,
    start,
    finish,
    cancel,
    markComplete,
    markError,
  };
}
