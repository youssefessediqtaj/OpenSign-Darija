import { useEffect, useRef, useState } from 'react';

import { Button } from '../../../shared/ui/Button';
import { DARIJA_COLOR_WORDS, darijaColorAudioUrl, type DarijaColor } from '../domain/darija-colors';

type PlaybackStatus = 'idle' | 'loading' | 'playing' | 'unavailable';

/** Local WAV only. Never fall back to generic Arabic system TTS or external speech APIs. */
function release(audio: HTMLAudioElement): void {
  audio.onended = null;
  audio.onerror = null;
  audio.pause();
  audio.removeAttribute('src');
  audio.load();
}

export function DarijaColorVoicePreview({ color }: { color: DarijaColor }) {
  const playerRef = useRef<HTMLAudioElement | null>(null);
  const [status, setStatus] = useState<PlaybackStatus>('idle');

  useEffect(() => () => {
    const audio = playerRef.current;
    playerRef.current = null;
    if (audio) release(audio);
  }, [color]);

  const listen = () => {
    const previous = playerRef.current;
    playerRef.current = null;
    if (previous) release(previous);

    const audio = new Audio(darijaColorAudioUrl(color));
    audio.preload = 'auto';
    playerRef.current = audio;
    setStatus('loading');

    audio.onended = () => {
      if (playerRef.current !== audio) return;
      playerRef.current = null;
      setStatus('idle');
    };
    audio.onerror = () => {
      if (playerRef.current !== audio) return;
      playerRef.current = null;
      release(audio);
      setStatus('unavailable');
    };

    // play() is called directly from the user's click, not after an async fetch.
    void audio.play().then(() => {
      if (playerRef.current === audio) setStatus('playing');
    }).catch(() => {
      if (playerRef.current !== audio) return;
      playerRef.current = null;
      release(audio);
      setStatus('unavailable');
    });
  };

  return (
    <section aria-label="Aperçu vocal Darija" className="mt-4 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
      <p className="text-sm font-semibold">Parole en darija marocaine — aperçu manuel</p>
      <p className="mt-2 text-2xl font-bold" lang="ary" dir="rtl">{DARIJA_COLOR_WORDS[color]}</p>
      <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">
        Le candidat est expérimental : la voix ne démarre jamais automatiquement et ne valide pas la reconnaissance.
      </p>
      <Button variant="secondary" type="button" className="mt-3" disabled={status === 'loading'} onClick={listen}>
        {status === 'loading' ? 'Chargement vocal…' : status === 'playing' ? 'Réécouter en darija' : 'Écouter en darija'}
      </Button>
      {status === 'unavailable' && (
        <p className="mt-2 text-sm text-red-700 dark:text-red-300" role="status">
          Aucun enregistrement darija approuvé disponible pour cette couleur. Aucun repli en arabe standard.
        </p>
      )}
    </section>
  );
}
