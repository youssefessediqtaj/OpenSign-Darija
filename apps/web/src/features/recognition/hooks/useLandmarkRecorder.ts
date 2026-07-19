import { useCallback, useEffect, useRef, useState } from 'react';

import type { HolisticFrame } from '../types/landmark.types';
import type { CapturePhase } from '../types/recognition.types';
import {
  createLandmarkSequence,
  toWordLandmarkPayload,
  validateWordRecognitionPayloadV1,
  wordValidationErrorMessage,
} from '../services/sequence-validator.service';
import type { LandmarkSequence, WordLandmarkSequencePayload } from '../types/sequence.types';

export function useLandmarkRecorder(anonymousSessionId: string) {
  const bufferRef = useRef<HolisticFrame[]>([]);
  const startedAtRef = useRef<string | null>(null);
  const phaseRef = useRef<CapturePhase>('idle');
  const [phase, setPhase] = useState<CapturePhase>('idle');
  const [sequence, setSequence] = useState<LandmarkSequence | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [diagnostics, setDiagnostics] = useState<Record<string, number>>({});

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
    setDiagnostics({});
    setSequence(null);
    phaseRef.current = 'capturing';
    setPhase('capturing');
  }, []);

  const cancel = useCallback(() => {
    bufferRef.current = [];
    startedAtRef.current = null;
    setSequence(null);
    setValidationErrors([]);
    setDiagnostics({});
    phaseRef.current = 'idle';
    setPhase('idle');
  }, []);

  const finish = useCallback((): WordLandmarkSequencePayload | null => {
    phaseRef.current = 'validating';
    setPhase('validating');
    const nextSequence = createLandmarkSequence(
      [...bufferRef.current],
      startedAtRef.current ?? new Date().toISOString(),
    );
    setSequence(nextSequence);
    const payload = toWordLandmarkPayload(nextSequence, anonymousSessionId);
    const validation = validateWordRecognitionPayloadV1(payload, {
      rawFrameCount: nextSequence.rawFrameCount,
      validFrameCount: nextSequence.validFrameCount,
    });
    setDiagnostics({
      rawFrameCount: nextSequence.rawFrameCount,
      validFrameCount: nextSequence.validFrameCount,
      outputFrameCount: validation.diagnostics.outputFrameCount,
      payloadByteSize: validation.diagnostics.payloadByteSize ?? 0,
    });
    const errors = validation.errors.map(wordValidationErrorMessage);
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
    diagnostics,
    frameCount: bufferRef.current.length,
    addFrame,
    start,
    finish,
    cancel,
    markComplete,
    markError,
  };
}
