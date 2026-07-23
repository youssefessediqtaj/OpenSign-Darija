export type NormalizedLandmark = {
  x: number;
  y: number;
  z: number;
  visibility?: number;
  presence?: number;
};

export type FrameMetadata = {
  videoWidth: number;
  videoHeight: number;
  processingTimeMs: number;
  faceDetected: boolean;
  leftHandDetected: boolean;
  rightHandDetected: boolean;
  poseDetected: boolean;
};

export type HolisticFrame = {
  timestampMs: number;
  frameIndex: number;
  pose: NormalizedLandmark[];
  face: NormalizedLandmark[];
  leftHand: NormalizedLandmark[];
  rightHand: NormalizedLandmark[];
  metadata: FrameMetadata;
};
