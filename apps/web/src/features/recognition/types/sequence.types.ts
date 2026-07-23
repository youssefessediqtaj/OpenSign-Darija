import type { HolisticFrame } from './landmark.types';
import type { SegmentationKind } from './recognition-flow.types';

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
  frames: HolisticFrame[];
  rawFrameCount: number;
  validFrameCount: number;
  quality: SequenceQuality;
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
  segmentation_kind: SegmentationKind;
  segmentation_reliable: boolean;
  usable_frame_count: number;
  frames: MoslLandmarkFrame[];
  quality: {
    detected_hand_ratio: number;
    detected_face_ratio: number;
    detected_pose_ratio: number;
    missing_frame_ratio: number;
    movement_score: number;
  };
  anonymous_session_id?: string;
};

export type WordRecognitionPayloadValidationCode =
  | 'invalid_sequence_id'
  | 'invalid_captured_at'
  | 'invalid_recognition_mode'
  | 'invalid_schema'
  | 'invalid_target_frame_count'
  | 'invalid_landmark_count'
  | 'invalid_coordinate_count'
  | 'invalid_coordinate_format'
  | 'invalid_segmentation_kind'
  | 'unreliable_segmentation'
  | 'invalid_usable_frame_count'
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
