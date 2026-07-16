export function CaptureCountdown({ value }: { value: number | 'start' | null }) {
  if (value === null) return null;
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/45 text-white" aria-live="assertive">
      <span className="text-6xl font-bold">{value === 'start' ? 'Commencez' : value}</span>
    </div>
  );
}
