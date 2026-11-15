import { useCallback, useEffect, useRef, useState } from 'react';

import { darijaColorAudioUrl } from '../domain/darija-colors';

export type VoiceStatus = 'stopped' | 'loading' | 'playing' | 'unavailable';

function release(audio: HTMLAudioElement) {
  audio.onended = null;
  audio.onerror = null;
  audio.pause();
  audio.removeAttribute('src');
  audio.load();
}

/** Playback is started only by a user gesture; stale media events are ignored. */
export function useDarijaColorAudio(color: string) {
  const player = useRef<HTMLAudioElement | null>(null);
  const [status, setStatus] = useState<VoiceStatus>('stopped');
  const dispose = useCallback(() => {
    const audio = player.current;
    player.current = null;
    if (audio) release(audio);
  }, []);
  useEffect(() => {
    setStatus('stopped');
    return dispose;
  }, [color, dispose]);
  const stop = useCallback(() => {
    dispose();
    setStatus('stopped');
  }, [dispose]);
  const play = useCallback(() => {
    dispose();
    const url = darijaColorAudioUrl(color);
    if (!url) { setStatus('unavailable'); return; }
    const audio = new Audio(url);
    player.current = audio;
    audio.preload = 'auto';
    setStatus('loading');
    const finish = (next: VoiceStatus) => {
      if (player.current !== audio) return;
      dispose();
      setStatus(next);
    };
    audio.onended = () => finish('stopped');
    audio.onerror = () => finish('unavailable');
    try {
      void audio.play().then(() => {
        if (player.current === audio) setStatus('playing');
      }).catch(() => finish('unavailable'));
    } catch {
      finish('unavailable');
    }
  }, [color, dispose]);
  return { status, play, stop };
}
