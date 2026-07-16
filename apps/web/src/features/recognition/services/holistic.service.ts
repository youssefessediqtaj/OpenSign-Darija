import {
  FilesetResolver,
  HolisticLandmarker,
  type HolisticLandmarkerResult,
} from '@mediapipe/tasks-vision';

import { env } from '../../../config/env';
import type { HolisticFrame, NormalizedLandmark } from '../types/landmark.types';

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
    landmarkerPromise = FilesetResolver.forVisionTasks(env.mediapipeWasmPath).then((fileset) =>
      HolisticLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: env.mediapipeModelPath,
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        minFaceDetectionConfidence: 0.5,
        minHandLandmarksConfidence: 0.5,
        minPoseDetectionConfidence: 0.5,
      }),
    );
  }
  return landmarkerPromise;
}

export function resultToFrame(
  result: HolisticLandmarkerResult,
  frameIndex: number,
  timestampMs: number,
  video: HTMLVideoElement,
  processingTimeMs: number,
  averageLuminance: number,
): HolisticFrame {
  const face = copyLandmarks(result.faceLandmarks);
  const pose = copyLandmarks(result.poseLandmarks);
  const leftHand = copyLandmarks(result.leftHandLandmarks);
  const rightHand = copyLandmarks(result.rightHandLandmarks);
  return {
    timestampMs,
    frameIndex,
    pose,
    face,
    leftHand,
    rightHand,
    metadata: {
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      processingTimeMs,
      faceDetected: face.length > 0,
      leftHandDetected: leftHand.length > 0,
      rightHandDetected: rightHand.length > 0,
      poseDetected: pose.length > 0,
      averageLuminance,
    },
  };
}

export function createSyntheticFrame(frameIndex: number, timestampMs: number): HolisticFrame {
  const shoulderLeft = { x: 0.42, y: 0.48, z: 0, visibility: 0.98 };
  const shoulderRight = { x: 0.58, y: 0.48, z: 0, visibility: 0.98 };
  const wristLeft = { x: 0.38 + Math.sin(frameIndex / 5) * 0.05, y: 0.55, z: -0.02, visibility: 0.9 };
  const wristRight = { x: 0.62 + Math.cos(frameIndex / 5) * 0.05, y: 0.55, z: -0.02, visibility: 0.9 };
  const pose = Array.from({ length: 33 }, () => ({ x: 0, y: 0, z: 0, visibility: 0 }));
  pose[0] = { x: 0.5, y: 0.22, z: 0, visibility: 0.95 };
  pose[11] = shoulderLeft;
  pose[12] = shoulderRight;
  pose[13] = { x: 0.4, y: 0.52, z: 0, visibility: 0.9 };
  pose[14] = { x: 0.6, y: 0.52, z: 0, visibility: 0.9 };
  pose[15] = wristLeft;
  pose[16] = wristRight;
  const hand = Array.from({ length: 21 }, (_, index) => ({
    x: 0.45 + index * 0.002,
    y: 0.58 + Math.sin((frameIndex + index) / 6) * 0.04,
    z: 0,
    visibility: 0.92,
  }));
  return {
    timestampMs,
    frameIndex,
    pose,
    face: [{ x: 0.5, y: 0.24, z: 0, visibility: 0.95 }],
    leftHand: hand,
    rightHand: hand.map((point) => ({ ...point, x: 1 - point.x })),
    metadata: {
      videoWidth: 1280,
      videoHeight: 720,
      processingTimeMs: 18,
      faceDetected: true,
      leftHandDetected: true,
      rightHandDetected: true,
      poseDetected: true,
      averageLuminance: 140,
    },
  };
}
