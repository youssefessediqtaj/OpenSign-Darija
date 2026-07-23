import type { CameraErrorCode } from './camera.types';

export function mapCameraError(error: unknown): CameraErrorCode {
  if (!navigator.mediaDevices?.getUserMedia) return 'UNSUPPORTED';
  if (!window.isSecureContext && location.hostname !== 'localhost') return 'INSECURE_CONTEXT';
  if (!(error instanceof DOMException)) return 'SYSTEM_ERROR';

  switch (error.name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'PERMISSION_DENIED';
    case 'NotFoundError':
    case 'DevicesNotFoundError':
      return 'NOT_FOUND';
    case 'NotReadableError':
    case 'TrackStartError':
      return 'IN_USE';
    case 'OverconstrainedError':
    case 'ConstraintNotSatisfiedError':
      return 'CONSTRAINT_NOT_SUPPORTED';
    case 'AbortError':
      return 'INTERRUPTED';
    default:
      return 'SYSTEM_ERROR';
  }
}

export function cameraErrorMessage(code: CameraErrorCode): string {
  const messages: Record<CameraErrorCode, string> = {
    UNSUPPORTED: "Ce navigateur ne permet pas d’utiliser la caméra.",
    INSECURE_CONTEXT: 'La caméra nécessite une connexion HTTPS ou localhost.',
    PERMISSION_DENIED: "L’accès à la caméra a été refusé.",
    NOT_FOUND: "Aucune caméra compatible n’a été détectée.",
    IN_USE: 'La caméra est utilisée par une autre application.',
    CONSTRAINT_NOT_SUPPORTED: 'Cette caméra ne supporte pas la qualité demandée.',
    INTERRUPTED: 'Le flux caméra a été interrompu.',
    SYSTEM_ERROR: 'Une erreur système a empêché l’ouverture de la caméra.',
  };
  return messages[code];
}
