import { useCallback, useRef, useState } from 'react';

import { speakWithBrowser } from '../services/browser-speech';
import { speechApi } from '../services/speech-api';
import type {
  RecognitionFlowState,
  VisibleRecognitionResult,
} from '../state/recognition-flow';

type SignSpeechOptions = {
  enterCooldown: () => void;
  schedule: (callback: () => void, delayMs: number) => number;
  transition: (state: RecognitionFlowState) => void;
};

export function useSignSpeech({
  enterCooldown,
  schedule,
  transition,
}: SignSpeechOptions) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const speechRunRef = useRef(0);
  const autoSpokenSegmentsRef = useRef(new Set<string>());
  const [audioMessage, setAudioMessage] = useState('');

  const cancelSpeech = useCallback(() => {
    speechRunRef.current += 1;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  const resetSpeech = useCallback(() => {
    cancelSpeech();
    autoSpokenSegmentsRef.current.clear();
    setAudioMessage('');
  }, [cancelSpeech]);

  const finishSpeech = useCallback(
    (speechRun: number, unavailable = false) => {
      if (speechRun !== speechRunRef.current) return;
      if (unavailable) setAudioMessage('Audio indisponible. Le résultat reste affiché.');
      enterCooldown();
    },
    [enterCooldown],
  );

  const playWithBrowserSpeech = useCallback(
    (text: string, speechRun: number) => {
      try {
        const utterance = speakWithBrowser(text, 1, 1);
        let finished = false;
        const finish = (unavailable = false) => {
          if (finished) return;
          finished = true;
          finishSpeech(speechRun, unavailable);
        };
        utterance.onend = () => finish();
        utterance.onerror = () => finish(true);
        schedule(() => finish(), 12_000);
      } catch {
        finishSpeech(speechRun, true);
      }
    },
    [finishSpeech, schedule],
  );

  const speakResult = useCallback(
    async (result: VisibleRecognitionResult, automatic: boolean) => {
      if (result.unknown || !result.labelKey) return;
      if (automatic && autoSpokenSegmentsRef.current.has(result.segmentId)) return;
      if (automatic) autoSpokenSegmentsRef.current.add(result.segmentId);

      cancelSpeech();
      const speechRun = speechRunRef.current;
      setAudioMessage('');
      transition('SPEAKING');

      try {
        const speech = await speechApi.createForSign(result.labelKey);
        if (speechRun !== speechRunRef.current) return;
        const audioUrl = speech.audio?.url;
        const audio = audioRef.current;
        if (!audioUrl || !audio) throw new Error('Audio indisponible');

        let playbackStarted = false;
        let playbackFinished = false;
        const finish = (unavailable = false) => {
          if (playbackFinished) return;
          playbackFinished = true;
          if (speechRun !== speechRunRef.current) return;
          audio.onended = null;
          audio.onerror = null;
          finishSpeech(speechRun, unavailable);
        };
        audio.onended = () => finish();
        audio.onerror = () => finish(true);
        audio.src = audioUrl;
        audio.load();
        try {
          await audio.play();
          playbackStarted = true;
          schedule(() => finish(), 20_000);
        } catch {
          audio.onended = null;
          audio.onerror = null;
        }
        if (!playbackStarted) playWithBrowserSpeech(result.labelAr, speechRun);
      } catch {
        if (speechRun === speechRunRef.current) {
          playWithBrowserSpeech(result.labelAr, speechRun);
        }
      }
    },
    [cancelSpeech, finishSpeech, playWithBrowserSpeech, schedule, transition],
  );

  return {
    audioRef,
    audioMessage,
    setAudioMessage,
    speakResult,
    cancelSpeech,
    resetSpeech,
  };
}
