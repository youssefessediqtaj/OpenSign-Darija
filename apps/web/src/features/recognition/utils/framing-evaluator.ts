import type { FramingEvaluation, FramingWarning, LightingLevel, StabilityLevel } from '../types/framing.types';
import type { HolisticFrame } from '../types/landmark.types';
import { hasAnyVisible, isVisible } from './landmark-visibility';

const POSE = {
  NOSE: 0,
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_WRIST: 15,
  RIGHT_WRIST: 16,
};

export function lightingFromLuminance(value: number): LightingLevel {
  if (value < 55) return 'too_dark';
  if (value < 115) return 'acceptable';
  return 'good';
}

export function stabilityFromMovement(movement: number): StabilityLevel {
  if (movement > 0.09) return 'unstable';
  if (movement > 0.045) return 'acceptable';
  return 'stable';
}

export function evaluateFraming(frame: HolisticFrame | null, movement = 0): FramingEvaluation {
  const warnings: FramingWarning[] = [];
  const faceVisible = Boolean(frame?.metadata.faceDetected || isVisible(frame?.pose[POSE.NOSE]));
  const leftShoulder = frame?.pose[POSE.LEFT_SHOULDER];
  const rightShoulder = frame?.pose[POSE.RIGHT_SHOULDER];
  const shouldersVisible = isVisible(leftShoulder) && isVisible(rightShoulder);
  const torsoVisible = shouldersVisible;
  const leftHandVisible = hasAnyVisible(frame?.leftHand ?? []) || isVisible(frame?.pose[POSE.LEFT_WRIST]);
  const rightHandVisible = hasAnyVisible(frame?.rightHand ?? []) || isVisible(frame?.pose[POSE.RIGHT_WRIST]);
  const centerX = shouldersVisible && leftShoulder && rightShoulder ? (leftShoulder.x + rightShoulder.x) / 2 : 0.5;
  const centered = centerX > 0.34 && centerX < 0.66;
  const shoulderDistance = shouldersVisible && leftShoulder && rightShoulder ? Math.abs(leftShoulder.x - rightShoulder.x) : 0;
  const distance = shoulderDistance > 0.48 ? 'too_close' : shoulderDistance < 0.16 ? 'too_far' : 'correct';
  const lighting = lightingFromLuminance(frame?.metadata.averageLuminance ?? 0);
  const stability = stabilityFromMovement(movement);

  if (!faceVisible) warnings.push('FACE_MISSING');
  if (!torsoVisible) warnings.push('TORSO_MISSING');
  if (!leftHandVisible && !rightHandVisible) warnings.push('HANDS_MISSING');
  if (!shouldersVisible) warnings.push('SHOULDERS_MISSING');
  if (distance === 'too_close') warnings.push('TOO_CLOSE');
  if (distance === 'too_far') warnings.push('TOO_FAR');
  if (!centered) warnings.push('NOT_CENTERED');
  if (lighting === 'too_dark') warnings.push('TOO_DARK');
  if (stability === 'unstable') warnings.push('UNSTABLE');

  return {
    isReady: faceVisible && torsoVisible && (leftHandVisible || rightHandVisible) && centered && lighting !== 'too_dark',
    faceVisible,
    torsoVisible,
    leftHandVisible,
    rightHandVisible,
    shouldersVisible,
    centered,
    distance,
    lighting,
    stability,
    warnings,
  };
}

export function framingInstruction(evaluation: FramingEvaluation): string {
  if (evaluation.warnings.includes('TOO_CLOSE')) return 'Reculez legerement.';
  if (evaluation.warnings.includes('TOO_FAR')) return 'Rapprochez-vous de la camera.';
  if (evaluation.warnings.includes('HANDS_MISSING')) return 'Placez au moins une main dans le cadre.';
  if (evaluation.warnings.includes('FACE_MISSING')) return 'Votre visage doit rester visible.';
  if (evaluation.warnings.includes('TOO_DARK')) return "Ameliorez l'eclairage.";
  if (evaluation.warnings.includes('UNSTABLE')) return 'Restez immobile quelques secondes.';
  if (evaluation.warnings.includes('NOT_CENTERED')) return 'Centrez votre haut du corps dans le cadre.';
  return 'Vous etes correctement positionne.';
}
