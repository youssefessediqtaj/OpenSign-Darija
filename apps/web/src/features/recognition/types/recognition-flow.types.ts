import type { HolisticFrame } from './landmark.types';

export type RecognitionFlowState =
  | 'CAMERA_OFF'
  | 'INITIALIZING'
  | 'WAITING_FOR_SIGN'
  | 'CAPTURING'
  | 'RECOGNIZING'
  | 'DISPLAYING'
  | 'SPEAKING'
  | 'COOLDOWN'
  | 'ERROR';

export type SegmentationKind = 'dynamic' | 'static';

export type SegmentedSign = {
  id: string;
  kind: SegmentationKind;
  reliable: true;
  startedAtMs: number;
  endedAtMs: number;
  sourceFrames: HolisticFrame[];
  frames: HolisticFrame[];
  usableFrameCount: number;
  descriptor: number[];
};

export type SegmentationRejectionReason =
  | 'too_short'
  | 'insufficient_usable_frames'
  | 'unreliable_boundary';

export type SegmentationEvent =
  | { type: 'none' }
  | { type: 'started'; kind: SegmentationKind }
  | { type: 'completed'; segment: SegmentedSign }
  | { type: 'rejected'; reason: SegmentationRejectionReason }
  | { type: 'reset' };

export type PublicRecognitionResult = {
  status: 'recognized' | 'unknown';
  label_key: string | null;
  label_ar: string | null;
  confidence: number;
  unknown: boolean;
  latency_ms: number;
};
