import { useCallback, useEffect, useRef, useState } from 'react';

import { useCameraStream } from '../../recognition/hooks/useCameraStream';
import { useHolisticLandmarker } from '../../recognition/hooks/useHolisticLandmarker';
import { cameraErrorMessage, mapCameraError } from '../../recognition/services/camera-errors';
import {
  evaluateReadiness,
  INITIAL_READINESS,
  type BodyAnchor,
  type ReadinessChecks,
} from '../domain/readiness-policy';
import type { HolisticFrame } from '../../recognition/domain/landmarks';

export function useContributionCamera(
  videoRef: React.RefObject<HTMLVideoElement>,
  canActivate: boolean,
  dwellMs: number,
) {
  const [error, setError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<ReadinessChecks>(INITIAL_READINESS);
  const anchorRef = useRef<BodyAnchor | null>(null);
  const dwellStartedAtRef = useRef<number | null>(null);

  const onCameraError = useCallback((value: unknown) => {
    setError(cameraErrorMessage(mapCameraError(value)));
  }, []);
  const { stream, start: startStream, stop: stopStream } = useCameraStream(onCameraError);

  const handleFrame = useCallback(
    (frame: HolisticFrame) => {
      const { checks, anchor } = evaluateReadiness(frame, anchorRef.current);
      anchorRef.current = anchor;
      if (!checks.rawReady) {
        dwellStartedAtRef.current = null;
        setReadiness({ ...checks, dwellReady: false });
        return;
      }
      if (dwellStartedAtRef.current === null) {
        dwellStartedAtRef.current = frame.timestampMs;
      }
      const dwellReady = frame.timestampMs - dwellStartedAtRef.current >= dwellMs;
      setReadiness({
        ...checks,
        dwellReady,
        guidance: dwellReady ? 'Prêt à enregistrer.' : 'Restez stable.',
      });
    },
    [dwellMs],
  );

  const {
    status: detectorStatus,
    error: detectorError,
    start: startDetector,
    stop: stopDetector,
  } = useHolisticLandmarker(videoRef, Boolean(stream), handleFrame);

  const stop = useCallback(() => {
    stopDetector();
    stopStream();
    anchorRef.current = null;
    dwellStartedAtRef.current = null;
    setReadiness(INITIAL_READINESS);
  }, [stopDetector, stopStream]);

  const activate = useCallback(async () => {
    if (!canActivate) {
      setError('Complétez le formulaire et acceptez la notice avant d’activer la caméra.');
      return null;
    }
    setError(null);
    setReadiness(INITIAL_READINESS);
    return startStream();
  }, [canActivate, startStream]);

  useEffect(() => {
    if (stream) void startDetector();
  }, [startDetector, stream]);

  useEffect(() => {
    if (detectorStatus === 'loading') {
      setReadiness((current) => ({ ...current, guidance: 'Initialisation de la détection…' }));
    } else if (detectorStatus === 'error') {
      setError(detectorError ?? 'La vérification du cadrage est indisponible.');
    }
  }, [detectorError, detectorStatus]);

  return {
    stream,
    cameraActive: Boolean(stream),
    detectorStatus,
    readiness,
    error,
    activate,
    stop,
  };
}
