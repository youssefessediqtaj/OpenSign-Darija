import type { CameraStatus as CameraStatusValue } from '../types/camera.types';

export function CameraStatus({ status, engineStatus }: { status: CameraStatusValue; engineStatus: string }) {
  return (
    <div className="rounded-md bg-slate-100 p-3 text-sm dark:bg-slate-800" aria-live="polite">
      Camera: <strong>{status}</strong> · Detection: <strong>{engineStatus}</strong>
    </div>
  );
}
