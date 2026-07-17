import { useEffect, useRef, useState } from 'react';

import type { SpeechGeneration } from '../../../types/api';
import type { SpeechState } from '../types/speech.types';

export function useSpeechPlayer(generation: SpeechGeneration | null, volume: number, speed: number) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<SpeechState>('IDLE');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !generation?.audio?.url) return;
    audio.src = generation.audio.url;
    audio.volume = volume;
    audio.playbackRate = speed;
    setState('READY');
  }, [generation, speed, volume]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => setProgress(audio.duration ? audio.currentTime / audio.duration : 0);
    const onEnded = () => setState('STOPPED');
    const onError = () => setState('ERROR');
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('error', onError);
    return () => {
      audio.pause();
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('error', onError);
    };
  }, []);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed;
  }, [speed]);

  return {
    audioRef,
    state,
    progress,
    play: async () => {
      if (!audioRef.current) return;
      await audioRef.current.play();
      setState('PLAYING');
    },
    pause: () => {
      audioRef.current?.pause();
      setState('PAUSED');
    },
    stop: () => {
      if (!audioRef.current) return;
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setState('STOPPED');
    },
    replay: async () => {
      if (!audioRef.current) return;
      audioRef.current.currentTime = 0;
      await audioRef.current.play();
      setState('PLAYING');
    },
  };
}
