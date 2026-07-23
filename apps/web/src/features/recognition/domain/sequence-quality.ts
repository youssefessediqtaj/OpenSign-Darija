import type { HolisticFrame } from './landmarks';
import type { SequenceQuality } from './recognition-contract';

function ratio(count: number, total: number): number {
  return total === 0 ? 0 : Number((count / total).toFixed(3));
}

export function movementScore(frames: HolisticFrame[]): number {
  if (frames.length < 2) return 0;
  let total = 0;
  let comparisons = 0;
  for (let index = 1; index < frames.length; index += 1) {
    const previous = frames[index - 1];
    const current = frames[index];
    const previousWrist = previous.leftHand[0] ?? previous.rightHand[0] ?? previous.pose[15];
    const currentWrist = current.leftHand[0] ?? current.rightHand[0] ?? current.pose[15];
    if (previousWrist && currentWrist) {
      total += Math.hypot(currentWrist.x - previousWrist.x, currentWrist.y - previousWrist.y);
      comparisons += 1;
    }
  }
  return comparisons === 0 ? 0 : Number(Math.min(total / comparisons / 0.08, 1).toFixed(3));
}

export function calculateSequenceQuality(frames: HolisticFrame[], durationMs: number): SequenceQuality {
  const total = frames.length;
  const handFrames = frames.filter(
    (frame) => frame.metadata.leftHandDetected || frame.metadata.rightHandDetected,
  ).length;
  const faceFrames = frames.filter((frame) => frame.metadata.faceDetected).length;
  const poseFrames = frames.filter((frame) => frame.metadata.poseDetected).length;
  const missingFrames = frames.filter(
    (frame) =>
      !frame.metadata.poseDetected &&
      !frame.metadata.leftHandDetected &&
      !frame.metadata.rightHandDetected,
  ).length;
  const movement = movementScore(frames);
  const averageProcessingMs =
    total === 0
      ? 0
      : frames.reduce((sum, frame) => sum + frame.metadata.processingTimeMs, 0) / total;
  const averageProcessingFps =
    averageProcessingMs <= 0 ? 0 : Number((1000 / averageProcessingMs).toFixed(1));
  const detectedHandRatio = ratio(handFrames, total);
  const detectedFaceRatio = ratio(faceFrames, total);
  const detectedPoseRatio = ratio(poseFrames, total);
  const warnings: string[] = [];
  if (durationMs < 500) warnings.push('sequence_too_short');
  if (durationMs > 8000) warnings.push('sequence_too_long');
  if (detectedHandRatio < 0.35) warnings.push('insufficient_hand_visibility');
  if (detectedPoseRatio < 0.45) warnings.push('insufficient_pose_visibility');
  if (movement < 0.03) warnings.push('insufficient_movement');

  const score = Number(
    Math.min(
      detectedHandRatio * 0.35 +
        detectedFaceRatio * 0.15 +
        detectedPoseRatio * 0.25 +
        movement * 0.25,
      1,
    ).toFixed(3),
  );

  return {
    valid: warnings.length === 0,
    score,
    detectedHandRatio,
    detectedFaceRatio,
    detectedPoseRatio,
    averageProcessingFps,
    missingFrameRatio: total === 0 ? 1 : ratio(missingFrames, total),
    movementScore: movement,
    warnings,
  };
}
