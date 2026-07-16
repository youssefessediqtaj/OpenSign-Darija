import type { CameraDevice } from '../types/camera.types';

export function CameraSelector({
  devices,
  value,
  disabled,
  onChange,
}: {
  devices: CameraDevice[];
  value: string | null;
  disabled: boolean;
  onChange: (deviceId: string | null) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium">Camera</span>
      <select
        className="mt-1 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900"
        value={value ?? ''}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value || null)}
      >
        <option value="">Camera frontale recommandee</option>
        {devices.map((device) => (
          <option key={device.deviceId} value={device.deviceId}>
            {device.label}
          </option>
        ))}
      </select>
    </label>
  );
}
