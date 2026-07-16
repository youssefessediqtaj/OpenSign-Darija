import type { NormalizedLandmark } from '../types/landmark.types';

export function isVisible(landmark: NormalizedLandmark | undefined, threshold = 0.45): boolean {
  if (!landmark) return false;
  if (!Number.isFinite(landmark.x) || !Number.isFinite(landmark.y) || !Number.isFinite(landmark.z)) {
    return false;
  }
  const visibility = landmark.visibility ?? landmark.presence ?? 1;
  return visibility >= threshold && landmark.x >= -0.1 && landmark.x <= 1.1 && landmark.y >= -0.1 && landmark.y <= 1.1;
}

export function hasAnyVisible(landmarks: NormalizedLandmark[]): boolean {
  return landmarks.some((landmark) => isVisible(landmark, 0.35));
}
