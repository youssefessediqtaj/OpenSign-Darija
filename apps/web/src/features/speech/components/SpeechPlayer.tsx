import { Download, Pause, Play, RotateCcw, Square } from 'lucide-react';

import type { SpeechGeneration } from '../../../types/api';
import { useSpeechPlayer } from '../hooks/useSpeechPlayer';

export function SpeechPlayer({
  generation,
  volume,
  speed,
  onVolume,
}: {
  generation: SpeechGeneration;
  volume: number;
  speed: number;
  onVolume: (volume: number) => void;
}) {
  const player = useSpeechPlayer(generation, volume, speed);
  const duration = generation.audio ? `${(generation.audio.duration_ms / 1000).toFixed(1)}s` : '';
  return (
    <div className="space-y-3 rounded-md border border-slate-200 p-3 dark:border-slate-800">
      <audio ref={player.audioRef} preload="metadata">
        <track kind="captions" />
      </audio>
      <div className="flex flex-wrap items-center gap-2">
        <button aria-label="Lire" className="rounded-md border p-2" type="button" onClick={player.play}>
          <Play size={16} />
        </button>
        <button aria-label="Pause" className="rounded-md border p-2" type="button" onClick={player.pause}>
          <Pause size={16} />
        </button>
        <button aria-label="Arrêter" className="rounded-md border p-2" type="button" onClick={player.stop}>
          <Square size={16} />
        </button>
        <button aria-label="Rejouer" className="rounded-md border p-2" type="button" onClick={player.replay}>
          <RotateCcw size={16} />
        </button>
        {generation.audio && (
          <a
            aria-label="Télécharger l’audio"
            className="rounded-md border p-2"
            download={`opensign-message-${generation.generation_id.slice(0, 8)}.wav`}
            href={generation.audio.url}
          >
            <Download size={16} />
          </a>
        )}
        <span className="text-xs text-slate-600 dark:text-slate-300">{player.state} · {duration}</span>
      </div>
      <progress aria-label="Progression audio" className="h-2 w-full" value={player.progress} max={1} />
      <label className="block text-sm font-medium">
        Volume {Math.round(volume * 100)}%
        <input
          className="mt-2 w-full"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={volume}
          onChange={(event) => onVolume(Number(event.target.value))}
        />
      </label>
      {generation.cache_hit && <p className="text-xs text-emerald-700">Audio servi depuis le cache sécurisé.</p>}
      {generation.fallback_used && <p className="text-xs text-amber-700">Voix arabe de secours utilisée.</p>}
    </div>
  );
}
