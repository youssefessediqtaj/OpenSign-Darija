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
  averageLuminance: number;
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

export type CompactFrame = {
  index: number;
  timestamp_ms: number;
  features: number[];
  presence_mask: number[];
};
