export function SpeechSpeedControl({
  speed,
  onChange,
}: {
  speed: number;
  onChange: (speed: number) => void;
}) {
  return (
    <label className="block text-sm font-medium">
      Vitesse {speed.toFixed(2)}x
      <input
        className="mt-2 w-full"
        type="range"
        min="0.75"
        max="1.5"
        step="0.05"
        value={speed}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
