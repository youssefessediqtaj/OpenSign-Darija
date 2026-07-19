import type { FramingEvaluation } from '../types/framing.types';

export type DetectorStatus = 'idle' | 'loading' | 'ready' | 'fallback' | 'error';

export type WordCaptureGateInput = {
  mode: 'word' | 'alphabet';
  cameraReady: boolean;
  detectorStatus: DetectorStatus;
  evaluation: FramingEvaluation;
  recorderPhase: string;
  isSubmitting: boolean;
  mockCamera: boolean;
};

export type WordCaptureGate = {
  canCapture: boolean;
  reason: string | null;
};

export function detectorReadyForCapture(status: DetectorStatus, mockCamera = false): boolean {
  return status === 'ready' || (mockCamera && status === 'fallback');
}

export function evaluateWordCaptureGate(input: WordCaptureGateInput): WordCaptureGate {
  if (input.mode !== 'word') return { canCapture: false, reason: 'Mode alphabet actif.' };
  if (!input.cameraReady) return { canCapture: false, reason: 'Activez la camera.' };
  if (input.detectorStatus === 'loading') {
    return { canCapture: false, reason: 'Attendez que le moteur de detection soit pret.' };
  }
  if (input.detectorStatus === 'error') {
    return { canCapture: false, reason: 'Le moteur de detection a rencontre une erreur.' };
  }
  if (!detectorReadyForCapture(input.detectorStatus, input.mockCamera)) {
    return { canCapture: false, reason: 'Le moteur de detection n’est pas pret.' };
  }
  if (input.recorderPhase === 'capturing') {
    return { canCapture: false, reason: 'Capture en cours.' };
  }
  if (input.isSubmitting) {
    return { canCapture: false, reason: 'Reconnaissance en cours.' };
  }
  if (!input.evaluation.torsoVisible) {
    return { canCapture: false, reason: 'Placez votre corps face a la camera.' };
  }
  if (!input.evaluation.leftHandVisible && !input.evaluation.rightHandVisible) {
    return { canCapture: false, reason: 'Gardez au moins une main visible.' };
  }
  if (input.evaluation.distance === 'too_close') {
    return { canCapture: false, reason: 'Eloignez-vous legerement de la camera.' };
  }
  if (input.evaluation.distance === 'too_far') {
    return { canCapture: false, reason: 'Rapprochez-vous legerement de la camera.' };
  }
  if (input.evaluation.stability !== 'stable') {
    return { canCapture: false, reason: 'Stabilisez votre position avant de commencer.' };
  }
  if (!input.evaluation.isReady) {
    return { canCapture: false, reason: 'Ajustez votre cadrage avant de commencer.' };
  }
  return { canCapture: true, reason: null };
}
