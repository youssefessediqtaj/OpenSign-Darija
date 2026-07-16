import { env } from '../../../config/env';
import type { HolisticFrame } from '../types/landmark.types';
import type { CompactLandmarkSequencePayload, LandmarkSequence } from '../types/sequence.types';
import { compactFrame, COORDINATE_FORMAT, FEATURE_SCHEMA_VERSION } from './landmark-normalizer.service';
import { uniformSample } from '../utils/sequence-sampling';
import { calculateSequenceQuality } from '../utils/sequence-statistics';

export function createLandmarkSequence(frames: HolisticFrame[], startedAt: string): LandmarkSequence {
  const first = frames[0];
  const last = frames[frames.length - 1];
  const durationMs = first && last ? Math.max(last.timestampMs - first.timestampMs, 0) : 0;
  const sourceFps = durationMs > 0 ? Number(((frames.length / durationMs) * 1000).toFixed(1)) : 0;
  const quality = calculateSequenceQuality(frames, durationMs);
  return {
    id: crypto.randomUUID(),
    startedAt,
    durationMs,
    sourceFps,
    targetFrameCount: env.landmarkTargetFrames,
    frames,
    quality,
  };
}

export function toCompactPayload(
  sequence: LandmarkSequence,
  anonymousSessionId: string,
): CompactLandmarkSequencePayload {
  const sampled = uniformSample(sequence.frames, sequence.targetFrameCount);
  const frames = sampled
    .map((frame, index) => compactFrame(frame, index))
    .filter((frame): frame is NonNullable<typeof frame> => frame !== null);
  return {
    sequence_id: sequence.id,
    captured_at: sequence.startedAt,
    duration_ms: Math.round(sequence.durationMs),
    source_fps: sequence.sourceFps,
    target_frame_count: sequence.targetFrameCount,
    coordinate_format: COORDINATE_FORMAT,
    feature_schema_version: FEATURE_SCHEMA_VERSION,
    frames,
    quality: {
      detected_hand_ratio: sequence.quality.detectedHandRatio,
      detected_face_ratio: sequence.quality.detectedFaceRatio,
      detected_pose_ratio: sequence.quality.detectedPoseRatio,
      missing_frame_ratio: sequence.quality.missingFrameRatio,
      movement_score: sequence.quality.movementScore,
    },
    anonymous_session_id: anonymousSessionId,
  };
}

export function validateCompactPayload(payload: CompactLandmarkSequencePayload): string[] {
  const warnings: string[] = [];
  if (payload.duration_ms < 500) warnings.push('La sequence est trop courte.');
  if (payload.duration_ms > 8000) warnings.push('La sequence est trop longue.');
  if (payload.frames.length !== payload.target_frame_count) warnings.push('Le reechantillonnage a echoue.');
  if (payload.quality.detected_hand_ratio < 0.35) warnings.push('Aucune main suffisamment visible.');
  if (payload.quality.movement_score < 0.03) warnings.push('Le mouvement est insuffisant.');
  return warnings;
}
