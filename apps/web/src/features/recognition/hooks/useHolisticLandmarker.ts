import { useCallback, useEffect, useRef, useState } from 'react';

import type { HolisticFrame } from '../domain/landmarks';
import { createAutomaticTestFrame, loadHolisticLandmarker, resultToFrame } from '../services/holistic';

// 24 FPS quantizes to every third frame on a 60 Hz display, leaving enough
// headroom for the measured capture cadence to remain at or above 15 FPS.
const DETECTOR_TARGET_FPS = 24;

export function useHolisticLandmarker(
  videoRef: React.RefObject<HTMLVideoElement>,
  enabled: boolean,
  onFrame: (frame: HolisticFrame) => void,
) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'fallback' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const rafRef = useRef<number | null>(null);
  const runIdRef = useRef(0);
  const runningRef = useRef(false);
  const onFrameRef = useRef(onFrame);
  const lastRunRef = useRef(0);
  const frameIndexRef = useRef(0);

  useEffect(() => {
    onFrameRef.current = onFrame;
  }, [onFrame]);

  const stop = useCallback(() => {
    runningRef.current = false;
    runIdRef.current += 1;
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
  }, []);

  const start = useCallback(async () => {
    if (!enabled) return;
    if (runningRef.current) return;
    runningRef.current = true;
    const runId = runIdRef.current + 1;
    runIdRef.current = runId;
    setStatus('loading');
    setError(null);
    frameIndexRef.current = 0;
    lastRunRef.current = 0;
    const useAutomaticTestFrames =
      import.meta.env.DEV && new URLSearchParams(window.location.search).has('mockCamera');
    let landmarker: Awaited<ReturnType<typeof loadHolisticLandmarker>> | null = null;
    if (useAutomaticTestFrames) {
      if (!runningRef.current || runIdRef.current !== runId) return;
      setStatus('ready');
    } else {
      try {
        landmarker = await Promise.race([
          loadHolisticLandmarker(),
          new Promise<never>((_, reject) => {
            window.setTimeout(() => reject(new Error('MediaPipe timeout')), 12000);
          }),
        ]);
        // React Strict Mode and route teardown can overlap async MediaPipe startup; the
        // run ID prevents a stale detector from reviving a stopped camera loop.
        if (!runningRef.current || runIdRef.current !== runId) return;
        setStatus('ready');
      } catch (loadError) {
        if (runIdRef.current !== runId) return;
        runningRef.current = false;
        setStatus('error');
        setError(loadError instanceof Error ? loadError.message : 'MediaPipe indisponible');
        return;
      }
    }
    const minInterval = 1000 / DETECTOR_TARGET_FPS;
    const tick = (timestamp: number) => {
      if (!runningRef.current || runIdRef.current !== runId) return;
      const video = videoRef.current;
      if (video && timestamp - lastRunRef.current >= minInterval) {
        lastRunRef.current = timestamp;
        if (landmarker && video.videoWidth > 0) {
          try {
            const started = performance.now();
            const result = landmarker.detectForVideo(video, timestamp);
            onFrameRef.current(
              resultToFrame(
                result,
                frameIndexRef.current,
                timestamp,
                video,
                performance.now() - started,
              ),
            );
          } catch (detectionError) {
            runningRef.current = false;
            setStatus('error');
            setError(
              detectionError instanceof Error
                ? detectionError.message
                : 'La détection des mouvements a échoué.',
            );
            return;
          }
        } else if (!landmarker && useAutomaticTestFrames) {
          onFrameRef.current(createAutomaticTestFrame(frameIndexRef.current, timestamp));
        }
        frameIndexRef.current += 1;
      }
      if (runningRef.current && runIdRef.current === runId) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [enabled, videoRef]);

  useEffect(() => stop, [stop]);

  return { status, error, start, stop };
}
