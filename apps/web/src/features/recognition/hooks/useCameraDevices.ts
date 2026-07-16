import { useCallback, useEffect, useState } from 'react';

import { listCameraDevices } from '../services/camera.service';
import type { CameraDevice } from '../types/camera.types';

export function useCameraDevices(enabled: boolean) {
  const [devices, setDevices] = useState<CameraDevice[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      setDevices(await listCameraDevices());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    void refresh();
    navigator.mediaDevices?.addEventListener?.('devicechange', refresh);
    return () => navigator.mediaDevices?.removeEventListener?.('devicechange', refresh);
  }, [enabled, refresh]);

  return { devices, isLoading, refresh };
}
