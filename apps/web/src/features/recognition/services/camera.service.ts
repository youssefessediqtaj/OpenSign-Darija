import { env } from '../../../config/env';
import type { CameraDevice, CameraQuality, PerformanceMode } from '../types/camera.types';
import { mapCameraError } from '../utils/camera-errors';

const DEVICE_KEY = 'opensign.preferredCameraDeviceId';

export function isCameraSupported(): boolean {
  return Boolean(navigator.mediaDevices?.getUserMedia);
}

export function getPreferredCameraDeviceId(): string | null {
  return window.localStorage.getItem(DEVICE_KEY);
}

export function setPreferredCameraDeviceId(deviceId: string | null): void {
  if (deviceId) window.localStorage.setItem(DEVICE_KEY, deviceId);
  else window.localStorage.removeItem(DEVICE_KEY);
}

function constraintsFor(
  deviceId: string | null,
  quality: CameraQuality,
  performanceMode: PerformanceMode,
): MediaStreamConstraints {
  const lowPower = performanceMode === 'PERFORMANCE' || quality === 'LOW';
  const highQuality = performanceMode === 'QUALITY' || quality === 'HIGH';
  const width = lowPower ? 640 : highQuality ? env.cameraDefaultWidth : 960;
  const height = lowPower ? 480 : highQuality ? env.cameraDefaultHeight : 540;
  const frameRate = lowPower ? 15 : Math.min(env.cameraDefaultFps, highQuality ? 30 : 24);

  return {
    video: {
      ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'user' }),
      width: { ideal: width },
      height: { ideal: height },
      frameRate: { ideal: frameRate, max: 30 },
    },
    audio: false,
  };
}

export async function requestCameraStream(
  deviceId: string | null,
  quality: CameraQuality,
  performanceMode: PerformanceMode,
): Promise<MediaStream> {
  if (!isCameraSupported()) throw new DOMException('Unsupported mediaDevices', 'NotFoundError');
  try {
    return await navigator.mediaDevices.getUserMedia(
      constraintsFor(deviceId, quality, performanceMode),
    );
  } catch (error) {
    if (mapCameraError(error) === 'CONSTRAINT_NOT_SUPPORTED') {
      return navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    }
    throw error;
  }
}

export async function listCameraDevices(): Promise<CameraDevice[]> {
  if (!navigator.mediaDevices?.enumerateDevices) return [];
  const devices = await navigator.mediaDevices.enumerateDevices();
  return devices
    .filter((device) => device.kind === 'videoinput')
    .map((device, index) => {
      const label = device.label || `Camera ${index + 1}`;
      const normalized = label.toLowerCase();
      const facingMode = normalized.includes('back') || normalized.includes('rear')
        ? 'environment'
        : normalized.includes('front') || normalized.includes('facetime')
          ? 'user'
          : 'unknown';
      return { deviceId: device.deviceId, label, facingMode };
    });
}

export function stopCameraStream(stream: MediaStream | null): void {
  stream?.getTracks().forEach((track) => track.stop());
}
