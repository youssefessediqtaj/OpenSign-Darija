import { useEffect, useRef } from 'react';

import type { HolisticFrame } from '../types/landmark.types';
import { drawLandmarks } from '../utils/landmark-drawing';

export function LandmarkCanvas({
  frame,
  enabled,
}: {
  frame: HolisticFrame | null;
  enabled: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !enabled || !frame) {
      const context = canvas?.getContext('2d');
      context?.clearRect(0, 0, canvas?.width ?? 0, canvas?.height ?? 0);
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);
    drawLandmarks(canvas, frame);
  }, [enabled, frame]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden="true"
    />
  );
}
