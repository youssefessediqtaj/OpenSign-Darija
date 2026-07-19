import type { CompactFrame, HolisticFrame } from './landmark.types';

export type SequenceQuality = {
  valid: boolean;
  score: number;
  detectedHandRatio: number;
  detectedFaceRatio: number;
  detectedPoseRatio: number;
  averageProcessingFps: number;
  missingFrameRatio: number;
  movementScore: number;
  warnings: string[];
};

export type LandmarkSequence = {
  id: string;
  startedAt: string;
  durationMs: number;
  sourceFps: number;
  targetFrameCount: number;
  frames: HolisticFrame[];
  rawFrameCount: number;
  validFrameCount: number;
  quality: SequenceQuality;
};

export type CompactLandmarkSequencePayload = {
  sequence_id: string;
  captured_at: string;
  duration_ms: number;
  source_fps: number;
  target_frame_count: number;
  coordinate_format: 'torso_normalized_v1';
  feature_schema_version: '1.0.0';
  frames: CompactFrame[];
  quality: {
    detected_hand_ratio: number;
    detected_face_ratio: number;
    detected_pose_ratio: number;
    missing_frame_ratio: number;
    movement_score: number;
  };
  anonymous_session_id?: string;
};

export type MoslLandmarkFrame = {
  index: number;
  timestamp_ms: number;
  landmarks: number[][];
  presence_mask: number[];
};

export type WordLandmarkSequencePayload = {
  sequence_id: string;
  captured_at: string;
  recognition_mode: 'WORD_ISOLATED';
  duration_ms: number;
  source_fps: number;
  target_frame_count: number;
  landmark_count: 75;
  coordinate_count: 3;
  coordinate_format: 'shoulder_centered_v1';
  feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1';
  frames: MoslLandmarkFrame[];
  quality: CompactLandmarkSequencePayload['quality'];
  anonymous_session_id?: string;
};

export type RecognitionSequencePayload = CompactLandmarkSequencePayload | WordLandmarkSequencePayload;

export type WordRecognitionPayloadValidationCode =
  | 'invalid_sequence_id'
  | 'invalid_captured_at'
  | 'invalid_recognition_mode'
  | 'invalid_schema'
  | 'invalid_target_frame_count'
  | 'invalid_landmark_count'
  | 'invalid_coordinate_count'
  | 'invalid_coordinate_format'
  | 'invalid_duration'
  | 'invalid_source_fps'
  | 'invalid_quality'
  | 'invalid_frame_count'
  | 'invalid_frame_index'
  | 'invalid_timestamp'
  | 'non_monotonic_timestamp'
  | 'invalid_presence_mask'
  | 'non_finite_coordinate'
  | 'insufficient_valid_frames'
  | 'detector_not_ready';

export type WordRecognitionPayloadValidationError = {
  code: WordRecognitionPayloadValidationCode;
  field: string;
  message: string;
  expected?: number | string;
  received?: number | string;
};

export type WordRecognitionPayloadValidationResult = {
  valid: boolean;
  errors: WordRecognitionPayloadValidationError[];
  diagnostics: {
    rawFrameCount?: number;
    validFrameCount?: number;
    outputFrameCount: number;
    payloadByteSize?: number;
  };
};
