import type { CameraErrorCode } from '../types/camera.types';

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
    UNSUPPORTED: "Ce navigateur ne permet pas d'utiliser la camera.",
    INSECURE_CONTEXT: 'La camera necessite une connexion HTTPS ou localhost.',
    PERMISSION_DENIED: "L'acces a la camera a ete refuse.",
    NOT_FOUND: "Aucune camera compatible n'a ete detectee.",
    IN_USE: 'La camera est utilisee par une autre application.',
    CONSTRAINT_NOT_SUPPORTED: 'Cette camera ne supporte pas la qualite demandee.',
    INTERRUPTED: 'Le flux camera a ete interrompu.',
    SYSTEM_ERROR: 'Une erreur systeme a empeche l’ouverture de la camera.',
  };
  return messages[code];
}
