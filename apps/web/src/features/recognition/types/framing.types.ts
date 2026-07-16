export type FramingDistance = 'too_close' | 'correct' | 'too_far';
export type LightingLevel = 'too_dark' | 'acceptable' | 'good';
export type StabilityLevel = 'unstable' | 'acceptable' | 'stable';

export type FramingWarning =
  | 'FACE_MISSING'
  | 'TORSO_MISSING'
  | 'HANDS_MISSING'
  | 'SHOULDERS_MISSING'
  | 'TOO_CLOSE'
  | 'TOO_FAR'
  | 'NOT_CENTERED'
  | 'TOO_DARK'
  | 'UNSTABLE';

export type FramingEvaluation = {
  isReady: boolean;
  faceVisible: boolean;
  torsoVisible: boolean;
  leftHandVisible: boolean;
  rightHandVisible: boolean;
  shouldersVisible: boolean;
  centered: boolean;
  distance: FramingDistance;
  lighting: LightingLevel;
  stability: StabilityLevel;
  warnings: FramingWarning[];
};
