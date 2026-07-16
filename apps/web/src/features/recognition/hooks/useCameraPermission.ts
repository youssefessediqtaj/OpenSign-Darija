import { useCallback, useState } from 'react';

import type { CameraErrorCode, CameraStatus } from '../types/camera.types';
import { cameraErrorMessage, mapCameraError } from '../utils/camera-errors';

export function useCameraPermission() {
  const [status, setStatus] = useState<CameraStatus>('IDLE');
  const [errorCode, setErrorCode] = useState<CameraErrorCode | null>(null);

  const markRequesting = useCallback(() => {
    setStatus('REQUESTING_PERMISSION');
    setErrorCode(null);
  }, []);

  const markGranted = useCallback(() => {
    setStatus('PERMISSION_GRANTED');
    setErrorCode(null);
  }, []);

  const markError = useCallback((error: unknown) => {
    const code = mapCameraError(error);
    setErrorCode(code);
    setStatus(code === 'PERMISSION_DENIED' ? 'PERMISSION_DENIED' : code === 'UNSUPPORTED' ? 'UNSUPPORTED' : 'ERROR');
  }, []);

  return {
    status,
    setStatus,
    errorCode,
    errorMessage: errorCode ? cameraErrorMessage(errorCode) : null,
    markRequesting,
    markGranted,
    markError,
  };
}
