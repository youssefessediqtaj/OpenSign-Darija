import { env } from '../../../shared/config/env';
import { mapCameraError } from './camera-errors';

function isCameraSupported(): boolean {
  return Boolean(navigator.mediaDevices?.getUserMedia);
}

function defaultConstraints(): MediaStreamConstraints {
  return {
    video: {
      facingMode: 'user',
      width: { ideal: env.cameraDefaultWidth },
      height: { ideal: env.cameraDefaultHeight },
      frameRate: { ideal: Math.min(env.cameraDefaultFps, 24), max: 30 },
    },
    audio: false,
  };
}

export async function requestCameraStream(): Promise<MediaStream> {
  if (!isCameraSupported()) throw new DOMException('Unsupported mediaDevices', 'NotFoundError');
  try {
    return await navigator.mediaDevices.getUserMedia(defaultConstraints());
  } catch (error) {
    if (mapCameraError(error) === 'CONSTRAINT_NOT_SUPPORTED') {
      return navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    }
    throw error;
  }
}

export function stopCameraStream(stream: MediaStream | null): void {
  stream?.getTracks().forEach((track) => track.stop());
}
