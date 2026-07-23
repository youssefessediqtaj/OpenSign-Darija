import type { HolisticFrame, NormalizedLandmark } from './landmarks';
import type { MoslLandmarkFrame } from './recognition-contract';

export const OPEN_SIGNE_LANDMARK_SCHEMA_VERSION = 'OPEN_SIGNE_LANDMARK_SCHEMA_V1' as const;
export const OPEN_SIGNE_COORDINATE_FORMAT = 'shoulder_centered_v1' as const;
export const OPEN_SIGNE_LANDMARK_COUNT = 75 as const;
export const OPEN_SIGNE_COORDINATE_COUNT = 3 as const;

const POSE_LANDMARKS = 33;
const HAND_LANDMARKS = 21;
const LEFT_SHOULDER = 11;
const RIGHT_SHOULDER = 12;

function finiteLandmark(landmark: NormalizedLandmark | undefined): landmark is NormalizedLandmark {
  return Boolean(
    landmark &&
      Number.isFinite(landmark.x) &&
      Number.isFinite(landmark.y) &&
      Number.isFinite(landmark.z),
  );
}

function groupToTriples(group: NormalizedLandmark[], expected: number): number[][] {
  return Array.from({ length: expected }, (_, index) => {
    const landmark = group[index];
    return finiteLandmark(landmark) ? [landmark.x, landmark.y, landmark.z] : [0, 0, 0];
  });
}

function groupMask(group: NormalizedLandmark[], expected: number): number[] {
  return Array.from({ length: expected }, (_, index) => (finiteLandmark(group[index]) ? 1 : 0));
}

function normalizeTriplet(values: number[], origin: number[], scale: number): number[] {
  return values.map((value, index) => Number(((value - origin[index]) / scale).toFixed(6)));
}

export function normalizeSchemaV1Frame(
  frame: HolisticFrame,
  outputIndex: number,
  relativeTimestampMs = frame.timestampMs,
): MoslLandmarkFrame {
  const pose = groupToTriples(frame.pose, POSE_LANDMARKS);
  const left = groupToTriples(frame.leftHand, HAND_LANDMARKS);
  const right = groupToTriples(frame.rightHand, HAND_LANDMARKS);
  const mask = [
    ...groupMask(frame.pose, POSE_LANDMARKS),
    ...groupMask(frame.leftHand, HAND_LANDMARKS),
    ...groupMask(frame.rightHand, HAND_LANDMARKS),
  ];
  const leftShoulder = frame.pose[LEFT_SHOULDER];
  const rightShoulder = frame.pose[RIGHT_SHOULDER];
  let origin = [0, 0, 0];
  let scale = 1;
  if (finiteLandmark(leftShoulder) && finiteLandmark(rightShoulder)) {
    origin = [
      (leftShoulder.x + rightShoulder.x) / 2,
      (leftShoulder.y + rightShoulder.y) / 2,
      (leftShoulder.z + rightShoulder.z) / 2,
    ];
    const distance = Math.hypot(
      leftShoulder.x - rightShoulder.x,
      leftShoulder.y - rightShoulder.y,
      leftShoulder.z - rightShoulder.z,
    );
    if (Number.isFinite(distance) && distance >= 1e-6) scale = distance;
  }
  const landmarks = [...pose, ...left, ...right].map((values, index) =>
    mask[index] === 1 ? normalizeTriplet(values, origin, scale) : [0, 0, 0],
  );
  return {
    index: outputIndex,
    timestamp_ms: Math.max(0, Math.round(relativeTimestampMs)),
    landmarks,
    presence_mask: mask,
  };
}
