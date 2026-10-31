import { useCallback, useEffect, useRef, useState } from 'react';

import { selectRecordingMimeType } from '../domain/recording-policy';

type RecordingPreview = {
  blob: Blob;
  url: string;
  durationSeconds: number;
  mimeType: string;
};

export function useContributionRecording(maxDurationSeconds: number) {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [preview, setPreview] = useState<RecordingPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef(0);
  const intervalRef = useRef<number | null>(null);
  const maximumTimerRef = useRef<number | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const clearTimers = useCallback(() => {
    if (intervalRef.current !== null) window.clearInterval(intervalRef.current);
    if (maximumTimerRef.current !== null) window.clearTimeout(maximumTimerRef.current);
    intervalRef.current = null;
    maximumTimerRef.current = null;
  }, []);

  const revokePreview = useCallback(() => {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = null;
  }, []);

  const discard = useCallback(() => {
    revokePreview();
    setPreview(null);
    setElapsedSeconds(0);
    setError(null);
  }, [revokePreview]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder?.state === 'recording') recorder.stop();
    clearTimers();
  }, [clearTimers]);

  const start = useCallback(
    (stream: MediaStream) => {
      const mimeType = selectRecordingMimeType();
      if (!mimeType) {
        setError('Ce navigateur ne permet pas l’enregistrement WebM requis.');
        return false;
      }
      discard();
      chunksRef.current = [];
      try {
        const recorder = new MediaRecorder(stream, { mimeType });
        recorderRef.current = recorder;
        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) chunksRef.current.push(event.data);
        };
        recorder.onstop = () => {
          clearTimers();
          const durationSeconds = Math.max(
            0,
            (performance.now() - startedAtRef.current) / 1000,
          );
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || mimeType });
          const url = URL.createObjectURL(blob);
          previewUrlRef.current = url;
          setPreview({ blob, url, durationSeconds, mimeType: blob.type });
          setElapsedSeconds(durationSeconds);
          setIsRecording(false);
          recorderRef.current = null;
        };
        recorder.onerror = () => {
          clearTimers();
          setIsRecording(false);
          setError('L’enregistrement vidéo a échoué.');
        };
        startedAtRef.current = performance.now();
        recorder.start(250);
        setIsRecording(true);
        setElapsedSeconds(0);
        intervalRef.current = window.setInterval(() => {
          setElapsedSeconds((performance.now() - startedAtRef.current) / 1000);
        }, 100);
        maximumTimerRef.current = window.setTimeout(stop, maxDurationSeconds * 1000);
        return true;
      } catch {
        setError('L’enregistrement vidéo n’a pas pu démarrer.');
        recorderRef.current = null;
        return false;
      }
    },
    [clearTimers, discard, maxDurationSeconds, stop],
  );

  useEffect(
    () => () => {
      clearTimers();
      const recorder = recorderRef.current;
      if (recorder) {
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        if (recorder.state === 'recording') recorder.stop();
      }
      recorderRef.current = null;
      chunksRef.current = [];
      revokePreview();
    },
    [clearTimers, revokePreview],
  );

  return {
    isRecording,
    elapsedSeconds,
    preview,
    error,
    start,
    stop,
    discard,
  };
}
