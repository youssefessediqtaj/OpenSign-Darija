import type { HolisticFrame } from '../domain/landmarks';

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
  captureMode?: 'manual' | 'automatic';
  startTrigger?: string;
  completionReason?: 'stable' | 'pose_rest_after_disappearance' | 'manual';
  startedAtMs: number;
  endedAtMs: number;
  sourceFrames: HolisticFrame[];
  frames: HolisticFrame[];
  usableFrameCount: number;
  descriptor: number[];
};

type SegmentationRejectionReason =
  | 'too_short'
  | 'insufficient_usable_frames'
  | 'unreliable_boundary'
  | 'invalid_timestamps';

export type SegmentationEvent =
  | { type: 'none' }
  | { type: 'started'; kind: SegmentationKind }
  | { type: 'completed'; segment: SegmentedSign }
  | { type: 'rejected'; reason: SegmentationRejectionReason; attempt: { captureMode: 'manual' | 'automatic'; startTrigger: string; id: string; startedAtMs: number; endedAtMs: number; capturedFrames: number; usableFrames: number; noHandFrames: number; missingPoseFrames: number; handCoverage: number; poseCoverage: number; completionReason: 'stable' | 'maximum_duration' | 'pose_rest_after_disappearance' | 'manual' } }
  | { type: 'reset' };

export type PublicRecognitionResult = {
  status: 'recognized' | 'unknown';
  label_key: string | null;
  label_ar: string | null;
  confidence: number;
  unknown: boolean;
  latency_ms: number;
};

export type VisibleRecognitionResult = {
  segmentId: string;
  labelKey: string | null;
  labelAr: string;
  unknown: boolean;
};
