import type { HolisticFrame } from '../../recognition/domain/landmarks';

export type ReadinessChecks = {
  detectorReady: boolean;
  faceVisible: boolean;
  leftHandVisible: boolean;
  rightHandVisible: boolean;
  upperBodyFramed: boolean;
  adequateLighting: boolean;
  acceptableDistance: boolean;
  stable: boolean;
  rawReady: boolean;
  dwellReady: boolean;
  guidance: string;
};

export type BodyAnchor = {
  leftShoulderX: number;
  leftShoulderY: number;
  rightShoulderX: number;
  rightShoulderY: number;
};

export const INITIAL_READINESS: ReadinessChecks = {
  detectorReady: false,
  faceVisible: false,
  leftHandVisible: false,
  rightHandVisible: false,
  upperBodyFramed: false,
  adequateLighting: false,
  acceptableDistance: false,
  stable: false,
  rawReady: false,
  dwellReady: false,
  guidance: 'Activez la caméra pour vérifier le cadrage.',
};

function validShoulder(frame: HolisticFrame, index: number) {
  const landmark = frame.pose[index];
  return landmark && (landmark.visibility ?? landmark.presence ?? 1) >= 0.5 ? landmark : null;
}

export function evaluateReadiness(
  frame: HolisticFrame,
  previousAnchor: BodyAnchor | null,
): { checks: Omit<ReadinessChecks, 'dwellReady'>; anchor: BodyAnchor | null } {
  const leftShoulder = validShoulder(frame, 11);
  const rightShoulder = validShoulder(frame, 12);
  const upperBodyFramed = Boolean(leftShoulder && rightShoulder);
  const shoulderSpan =
    leftShoulder && rightShoulder ? Math.abs(rightShoulder.x - leftShoulder.x) : 0;
  const acceptableDistance = shoulderSpan >= 0.12 && shoulderSpan <= 0.55;
  const faceVisible = frame.metadata.faceDetected;
  const leftHandVisible = frame.metadata.leftHandDetected;
  const rightHandVisible = frame.metadata.rightHandDetected;
  const adequateLighting = faceVisible && upperBodyFramed;
  const anchor =
    leftShoulder && rightShoulder
      ? {
          leftShoulderX: leftShoulder.x,
          leftShoulderY: leftShoulder.y,
          rightShoulderX: rightShoulder.x,
          rightShoulderY: rightShoulder.y,
        }
      : null;
  const stable =
    anchor !== null &&
    previousAnchor !== null &&
    Math.max(
      Math.abs(anchor.leftShoulderX - previousAnchor.leftShoulderX),
      Math.abs(anchor.leftShoulderY - previousAnchor.leftShoulderY),
      Math.abs(anchor.rightShoulderX - previousAnchor.rightShoulderX),
      Math.abs(anchor.rightShoulderY - previousAnchor.rightShoulderY),
    ) < 0.025;
  const rawReady =
    faceVisible &&
    upperBodyFramed &&
    (leftHandVisible || rightHandVisible) &&
    adequateLighting &&
    acceptableDistance &&
    stable;
  let guidance = 'Prêt à enregistrer.';
  if (!faceVisible || !upperBodyFramed) {
    guidance = 'Placez votre visage et le haut du corps dans le cadre.';
  } else if (!leftHandVisible && !rightHandVisible) {
    guidance = 'Gardez au moins une main visible.';
  } else if (!adequateLighting) {
    guidance = 'Améliorez l’éclairage.';
  } else if (shoulderSpan > 0.55) {
    guidance = 'Éloignez-vous légèrement.';
  } else if (shoulderSpan < 0.12) {
    guidance = 'Rapprochez-vous légèrement.';
  } else if (!stable) {
    guidance = 'Restez stable.';
  }
  return {
    checks: {
      detectorReady: true,
      faceVisible,
      leftHandVisible,
      rightHandVisible,
      upperBodyFramed,
      adequateLighting,
      acceptableDistance,
      stable,
      rawReady,
      guidance,
    },
    anchor,
  };
}
