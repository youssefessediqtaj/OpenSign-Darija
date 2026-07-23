import { useCallback, useState } from 'react';

import { cameraErrorMessage, mapCameraError } from '../services/camera-errors';
import type { CameraErrorCode, CameraStatus } from '../services/camera.types';

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
