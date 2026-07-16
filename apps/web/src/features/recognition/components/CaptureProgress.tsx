export function CaptureProgress({
  phase,
  frameCount,
  maxSeconds = 8,
}: {
  phase: string;
  frameCount: number;
  maxSeconds?: number;
}) {
  const estimatedSeconds = frameCount / 15;
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900">
      <p>
        Capture: <strong>{phase}</strong>
      </p>
      <p className="mt-1">Temps estime: {estimatedSeconds.toFixed(1)} s / {maxSeconds} s</p>
    </div>
  );
}
