import { useCallback, useEffect, useRef, useState } from 'react';

import { env } from '../../../config/env';
import { loadHolisticLandmarker, resultToFrame, createSyntheticFrame } from '../services/holistic.service';
import type { HolisticFrame } from '../types/landmark.types';

function estimateLuminance(video: HTMLVideoElement, canvas: HTMLCanvasElement): number {
  const context = canvas.getContext('2d', { willReadFrequently: true });
  if (!context || video.videoWidth === 0) return 120;
  canvas.width = 32;
  canvas.height = 18;
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
  let total = 0;
  for (let index = 0; index < pixels.length; index += 4) {
    total += pixels[index] * 0.2126 + pixels[index + 1] * 0.7152 + pixels[index + 2] * 0.0722;
  }
  return total / (pixels.length / 4);
}

export function useHolisticLandmarker(
  videoRef: React.RefObject<HTMLVideoElement>,
  enabled: boolean,
  onFrame: (frame: HolisticFrame) => void,
  performanceMode: 'AUTO' | 'QUALITY' | 'BALANCED' | 'PERFORMANCE',
) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'fallback' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastRunRef = useRef(0);
  const frameIndexRef = useRef(0);
  const luminanceCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const stop = useCallback(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
  }, []);

  const start = useCallback(async () => {
    if (!enabled) return;
    setStatus('loading');
    setError(null);
    let landmarker: Awaited<ReturnType<typeof loadHolisticLandmarker>> | null = null;
    if (location.search.includes('mockCamera')) {
      setStatus('fallback');
    } else {
      try {
        landmarker = await Promise.race([
          loadHolisticLandmarker(),
          new Promise<never>((_, reject) => {
            window.setTimeout(() => reject(new Error('MediaPipe timeout')), 12000);
          }),
        ]);
        setStatus('ready');
      } catch (loadError) {
        setStatus('fallback');
        setError(loadError instanceof Error ? loadError.message : 'MediaPipe indisponible');
      }
    }
    const targetFps = performanceMode === 'PERFORMANCE' ? 10 : performanceMode === 'QUALITY' ? 20 : 15;
    const minInterval = 1000 / targetFps;
    const tick = (timestamp: number) => {
      const video = videoRef.current;
      if (video && timestamp - lastRunRef.current >= minInterval) {
        lastRunRef.current = timestamp;
        if (!luminanceCanvasRef.current) luminanceCanvasRef.current = document.createElement('canvas');
        const luminance = landmarker ? estimateLuminance(video, luminanceCanvasRef.current) : 140;
        if (landmarker && video.videoWidth > 0) {
          const started = performance.now();
          const result = landmarker.detectForVideo(video, timestamp);
          onFrame(
            resultToFrame(
              result,
              frameIndexRef.current,
              timestamp,
              video,
              performance.now() - started,
              luminance,
            ),
          );
        } else if (!landmarker && (env.enablePerformanceMetrics || location.search.includes('mockCamera'))) {
          onFrame(createSyntheticFrame(frameIndexRef.current, timestamp));
        }
        frameIndexRef.current += 1;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [enabled, onFrame, performanceMode, videoRef]);

  useEffect(() => stop, [stop]);

  return { status, error, start, stop };
}
