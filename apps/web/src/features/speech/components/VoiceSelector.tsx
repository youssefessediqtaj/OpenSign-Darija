import type { SpeechVoice } from '../../../types/api';

export function VoiceSelector({
  voices,
  value,
  onChange,
}: {
  voices: SpeechVoice[];
  value: string;
  onChange: (voiceId: string) => void;
}) {
  return (
    <label className="block text-sm font-medium">
      Voix
      <select
        className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {voices.map((voice) => (
          <option key={voice.id} value={voice.id}>
            {voice.display_name}
          </option>
        ))}
      </select>
    </label>
  );
}
