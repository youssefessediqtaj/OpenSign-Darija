import type { RecognitionResponse } from '../../../types/api';

export type CapturePhase =
  | 'idle'
  | 'countdown'
  | 'capturing'
  | 'validating'
  | 'submitting'
  | 'complete'
  | 'error';

export type RecognitionResult = RecognitionResponse;
