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
