export type CameraStatus =
  | 'IDLE'
  | 'REQUESTING_PERMISSION'
  | 'PERMISSION_GRANTED'
  | 'PERMISSION_DENIED'
  | 'STARTING'
  | 'READY'
  | 'CAPTURING'
  | 'PROCESSING'
  | 'STOPPED'
  | 'ERROR'
  | 'UNSUPPORTED';

export type CameraErrorCode =
  | 'UNSUPPORTED'
  | 'INSECURE_CONTEXT'
  | 'PERMISSION_DENIED'
  | 'NOT_FOUND'
  | 'IN_USE'
  | 'CONSTRAINT_NOT_SUPPORTED'
  | 'INTERRUPTED'
  | 'SYSTEM_ERROR';

export type CameraDevice = {
  deviceId: string;
  label: string;
  facingMode: 'user' | 'environment' | 'unknown';
};

export type CameraQuality = 'LOW' | 'STANDARD' | 'HIGH';

export type PerformanceMode = 'AUTO' | 'QUALITY' | 'BALANCED' | 'PERFORMANCE';

export type CameraPreferences = {
  preferredDeviceId: string | null;
  showLandmarks: boolean;
  cameraQuality: CameraQuality;
  performanceMode: PerformanceMode;
  batterySaver: boolean;
  reduceMotion: boolean;
  theme: 'light' | 'dark' | 'system';
  language: 'fr' | 'ar' | 'en';
};
