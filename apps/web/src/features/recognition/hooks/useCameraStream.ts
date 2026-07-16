import { useCallback, useEffect, useRef, useState } from 'react';

import { requestCameraStream, stopCameraStream } from '../services/camera.service';
import type { CameraQuality, PerformanceMode } from '../types/camera.types';

export function useCameraStream(
  deviceId: string | null,
  quality: CameraQuality,
  performanceMode: PerformanceMode,
  onError: (error: unknown) => void,
) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stop = useCallback(() => {
    stopCameraStream(streamRef.current);
    streamRef.current = null;
    setStream(null);
  }, []);

  const start = useCallback(async () => {
    stop();
    try {
      const nextStream = await requestCameraStream(deviceId, quality, performanceMode);
      streamRef.current = nextStream;
      setStream(nextStream);
      return nextStream;
    } catch (error) {
      onError(error);
      return null;
    }
  }, [deviceId, onError, performanceMode, quality, stop]);

  useEffect(() => stop, [stop]);

  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'hidden') stop();
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [stop]);

  return { stream, start, stop };
}
