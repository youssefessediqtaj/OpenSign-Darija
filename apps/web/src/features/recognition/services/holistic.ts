import {
  FilesetResolver,
  HolisticLandmarker,
  type HolisticLandmarkerResult,
} from '@mediapipe/tasks-vision';

import { env } from '../../../shared/config/env';
import type { HolisticFrame, NormalizedLandmark } from '../domain/landmarks';

let landmarkerPromise: Promise<HolisticLandmarker> | null = null;

function copyLandmarks(landmarks: NormalizedLandmark[][] | undefined): NormalizedLandmark[] {
  return (landmarks?.[0] ?? []).map((landmark) => ({
    x: landmark.x,
    y: landmark.y,
    z: landmark.z,
    visibility: landmark.visibility,
    presence: landmark.presence,
  }));
}

export async function loadHolisticLandmarker(): Promise<HolisticLandmarker> {
  if (!landmarkerPromise) {
    landmarkerPromise = FilesetResolver.forVisionTasks(env.mediapipeWasmPath)
      .then(async (fileset) => {
        const options = {
          baseOptions: {
            modelAssetPath: env.mediapipeModelPath,
            delegate: 'CPU',
          },
          runningMode: 'VIDEO',
          minFaceDetectionConfidence: 0.5,
          minHandLandmarksConfidence: 0.5,
          minPoseDetectionConfidence: 0.5,
        } as const;
        return HolisticLandmarker.createFromOptions(fileset, options);
      })
      .catch((error) => {
        landmarkerPromise = null;
        throw error;
      });
  }
  return landmarkerPromise;
}

export function resultToFrame(
  result: HolisticLandmarkerResult,
  frameIndex: number,
  timestampMs: number,
  video: HTMLVideoElement,
  processingTimeMs: number,
): HolisticFrame {
  const pose = copyLandmarks(result.poseLandmarks);
  const leftHand = copyLandmarks(result.leftHandLandmarks);
  const rightHand = copyLandmarks(result.rightHandLandmarks);
  return {
    timestampMs,
    frameIndex,
    pose,
    face: [],
    leftHand,
    rightHand,
    metadata: {
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      processingTimeMs,
      faceDetected: (result.faceLandmarks?.[0]?.length ?? 0) > 0,
      leftHandDetected: leftHand.length > 0,
      rightHandDetected: rightHand.length > 0,
      poseDetected: pose.length > 0,
    },
  };
}

type SyntheticFrameKind = 'rest' | 'gesture-a' | 'gesture-b' | 'no-hands';

export const AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT = 160;

export function createSyntheticFrame(
  frameIndex: number,
  timestampMs: number,
  kind: SyntheticFrameKind = 'gesture-a',
  moving = true,
): HolisticFrame {
  const shoulderLeft = { x: 0.4, y: 0.48, z: 0, visibility: 0.98 };
  const shoulderRight = { x: 0.6, y: 0.48, z: 0, visibility: 0.98 };
  const phase = moving ? Math.sin(frameIndex * 1.3) : 0;
  const gestureOffset = kind === 'gesture-a' ? -0.2 : kind === 'gesture-b' ? 0.16 : 0;
  const handY = kind === 'rest' ? 0.78 : kind === 'gesture-a' ? 0.36 : 0.5;
  const wristLeft = {
    x: 0.38 + gestureOffset + phase * (moving ? 0.09 : 0),
    y: handY,
    z: -0.02,
    visibility: 0.9,
  };
  const wristRight = {
    x: 0.62 - gestureOffset - phase * (moving ? 0.09 : 0),
    y: handY + (kind === 'gesture-b' ? -0.16 : 0),
    z: -0.02,
    visibility: 0.9,
  };
  const pose = Array.from({ length: 33 }, () => ({ x: 0, y: 0, z: 0, visibility: 0 }));
  pose[0] = { x: 0.5, y: 0.22, z: 0, visibility: 0.95 };
  pose[11] = shoulderLeft;
  pose[12] = shoulderRight;
  pose[13] = { x: (shoulderLeft.x + wristLeft.x) / 2, y: (shoulderLeft.y + wristLeft.y) / 2, z: 0, visibility: 0.9 };
  pose[14] = { x: (shoulderRight.x + wristRight.x) / 2, y: (shoulderRight.y + wristRight.y) / 2, z: 0, visibility: 0.9 };
  pose[15] = wristLeft;
  pose[16] = wristRight;
  const leftHand = Array.from({ length: 21 }, (_, index) => ({
    x: wristLeft.x + (index % 5) * 0.012,
    y: wristLeft.y + Math.floor(index / 5) * 0.014 + (kind === 'gesture-b' ? (index % 2) * 0.025 : 0),
    z: 0,
    visibility: 0.92,
  }));
  const rightHand = Array.from({ length: 21 }, (_, index) => ({
    x: wristRight.x - (index % 5) * 0.012,
    y: wristRight.y + Math.floor(index / 5) * 0.014 + (kind === 'gesture-a' ? (index % 2) * 0.02 : 0),
    z: 0,
    visibility: 0.92,
  }));
  const noHands = kind === 'no-hands';
  return {
    timestampMs,
    frameIndex,
    pose,
    face: [{ x: 0.5, y: 0.24, z: 0, visibility: 0.95 }],
    leftHand: noHands ? [] : leftHand,
    rightHand: noHands ? [] : rightHand,
    metadata: {
      videoWidth: 1280,
      videoHeight: 720,
      processingTimeMs: 18,
      faceDetected: true,
      leftHandDetected: !noHands,
      rightHandDetected: !noHands,
      poseDetected: true,
    },
  };
}

export function createAutomaticTestFrame(frameIndex: number, timestampMs: number): HolisticFrame {
  if (frameIndex < 18) return createSyntheticFrame(frameIndex, timestampMs, 'rest', false);
  if (frameIndex < 36) return createSyntheticFrame(frameIndex, timestampMs, 'gesture-a', true);
  if (frameIndex < 48) return createSyntheticFrame(frameIndex, timestampMs, 'gesture-a', false);
  // Leave enough deterministic rest time for mocked audio, React scheduling, and
  // the production cooldown/reset gate even on a contended CI worker.
  if (frameIndex < 112) return createSyntheticFrame(frameIndex, timestampMs, 'rest', false);
  if (frameIndex < 130) return createSyntheticFrame(frameIndex, timestampMs, 'gesture-b', true);
  if (frameIndex < 143) return createSyntheticFrame(frameIndex, timestampMs, 'gesture-b', false);
  return createSyntheticFrame(frameIndex, timestampMs, 'rest', false);
}
