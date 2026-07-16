import type { CompactFrame, HolisticFrame, NormalizedLandmark } from '../types/landmark.types';

export const FEATURE_SCHEMA_VERSION = '1.0.0' as const;
export const COORDINATE_FORMAT = 'torso_normalized_v1' as const;
export const FEATURE_NAMES = [
  'pose.LEFT_SHOULDER',
  'pose.RIGHT_SHOULDER',
  'pose.LEFT_ELBOW',
  'pose.RIGHT_ELBOW',
  'pose.LEFT_WRIST',
  'pose.RIGHT_WRIST',
  'face.NOSE',
  'face.MOUTH_LEFT',
  'face.MOUTH_RIGHT',
  'leftHand.WRIST',
  'leftHand.THUMB_TIP',
  'leftHand.INDEX_FINGER_TIP',
  'leftHand.MIDDLE_FINGER_TIP',
  'leftHand.RING_FINGER_TIP',
  'leftHand.PINKY_TIP',
  'rightHand.WRIST',
  'rightHand.THUMB_TIP',
  'rightHand.INDEX_FINGER_TIP',
  'rightHand.MIDDLE_FINGER_TIP',
  'rightHand.RING_FINGER_TIP',
  'rightHand.PINKY_TIP',
] as const;

const POSE = {
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13,
  RIGHT_ELBOW: 14,
  LEFT_WRIST: 15,
  RIGHT_WRIST: 16,
};
const FACE = { NOSE: 1, MOUTH_LEFT: 61, MOUTH_RIGHT: 291 };
const HAND = { WRIST: 0, THUMB_TIP: 4, INDEX_FINGER_TIP: 8, MIDDLE_FINGER_TIP: 12, RING_FINGER_TIP: 16, PINKY_TIP: 20 };

function validLandmark(landmark: NormalizedLandmark | undefined): landmark is NormalizedLandmark {
  return Boolean(
    landmark &&
      Number.isFinite(landmark.x) &&
      Number.isFinite(landmark.y) &&
      Number.isFinite(landmark.z),
  );
}

function distance(a: NormalizedLandmark, b: NormalizedLandmark): number {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

function normalizePoint(
  landmark: NormalizedLandmark | undefined,
  origin: NormalizedLandmark,
  scale: number,
): { values: [number, number, number]; present: number } {
  if (!validLandmark(landmark)) return { values: [0, 0, 0], present: 0 };
  const visibility = landmark.visibility ?? landmark.presence ?? 1;
  return {
    values: [
      Number(((landmark.x - origin.x) / scale).toFixed(6)),
      Number(((landmark.y - origin.y) / scale).toFixed(6)),
      Number(((landmark.z - origin.z) / scale).toFixed(6)),
    ],
    present: visibility >= 0.35 ? 1 : 0,
  };
}

export function compactFrame(frame: HolisticFrame, outputIndex: number): CompactFrame | null {
  const leftShoulder = frame.pose[POSE.LEFT_SHOULDER];
  const rightShoulder = frame.pose[POSE.RIGHT_SHOULDER];
  if (!validLandmark(leftShoulder) || !validLandmark(rightShoulder)) return null;
  const scale = distance(leftShoulder, rightShoulder);
  if (!Number.isFinite(scale) || scale < 0.02) return null;
  const origin = {
    x: (leftShoulder.x + rightShoulder.x) / 2,
    y: (leftShoulder.y + rightShoulder.y) / 2,
    z: (leftShoulder.z + rightShoulder.z) / 2,
  };
  const selected = [
    frame.pose[POSE.LEFT_SHOULDER],
    frame.pose[POSE.RIGHT_SHOULDER],
    frame.pose[POSE.LEFT_ELBOW],
    frame.pose[POSE.RIGHT_ELBOW],
    frame.pose[POSE.LEFT_WRIST],
    frame.pose[POSE.RIGHT_WRIST],
    frame.face[FACE.NOSE],
    frame.face[FACE.MOUTH_LEFT],
    frame.face[FACE.MOUTH_RIGHT],
    frame.leftHand[HAND.WRIST],
    frame.leftHand[HAND.THUMB_TIP],
    frame.leftHand[HAND.INDEX_FINGER_TIP],
    frame.leftHand[HAND.MIDDLE_FINGER_TIP],
    frame.leftHand[HAND.RING_FINGER_TIP],
    frame.leftHand[HAND.PINKY_TIP],
    frame.rightHand[HAND.WRIST],
    frame.rightHand[HAND.THUMB_TIP],
    frame.rightHand[HAND.INDEX_FINGER_TIP],
    frame.rightHand[HAND.MIDDLE_FINGER_TIP],
    frame.rightHand[HAND.RING_FINGER_TIP],
    frame.rightHand[HAND.PINKY_TIP],
  ];
  const features: number[] = [];
  const presenceMask: number[] = [];
  selected.forEach((landmark) => {
    const normalized = normalizePoint(landmark, origin, scale);
    features.push(...normalized.values);
    presenceMask.push(normalized.present);
  });
  return {
    index: outputIndex,
    timestamp_ms: Math.round(frame.timestampMs),
    features,
    presence_mask: presenceMask,
  };
}
