import { useCallback, useEffect, useRef, useState } from 'react';

import type { HolisticFrame } from '../types/landmark.types';
import type { CapturePhase } from '../types/recognition.types';
import { createLandmarkSequence, toCompactPayload, validateCompactPayload } from '../services/sequence-validator.service';
import type { CompactLandmarkSequencePayload, LandmarkSequence } from '../types/sequence.types';

export function useLandmarkRecorder(anonymousSessionId: string) {
  const bufferRef = useRef<HolisticFrame[]>([]);
  const startedAtRef = useRef<string | null>(null);
  const phaseRef = useRef<CapturePhase>('idle');
  const [phase, setPhase] = useState<CapturePhase>('idle');
  const [sequence, setSequence] = useState<LandmarkSequence | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  const addFrame = useCallback(
    (frame: HolisticFrame) => {
      if (phaseRef.current !== 'capturing') return;
      if (bufferRef.current.length < 180) bufferRef.current.push(frame);
    },
    [],
  );

  const start = useCallback(() => {
    bufferRef.current = [];
    startedAtRef.current = new Date().toISOString();
    setValidationErrors([]);
    setSequence(null);
    phaseRef.current = 'capturing';
    setPhase('capturing');
  }, []);

  const cancel = useCallback(() => {
    bufferRef.current = [];
    startedAtRef.current = null;
    setSequence(null);
    setValidationErrors([]);
    phaseRef.current = 'idle';
    setPhase('idle');
  }, []);

  const finish = useCallback((): CompactLandmarkSequencePayload | null => {
    phaseRef.current = 'validating';
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
      phaseRef.current = 'error';
      setPhase('error');
      return null;
    }
    phaseRef.current = 'submitting';
    setPhase('submitting');
    return payload;
  }, [anonymousSessionId]);

  const markComplete = useCallback(() => {
    phaseRef.current = 'complete';
    setPhase('complete');
  }, []);
  const markError = useCallback((message: string) => {
    setValidationErrors([message]);
    phaseRef.current = 'error';
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
