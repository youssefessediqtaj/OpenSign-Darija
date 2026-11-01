import { act, render, screen, waitFor } from '@testing-library/react';
import { useCallback, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { RecognitionWorkspace } from '../components/RecognitionWorkspace';
import type { HolisticFrame } from '../domain/landmarks';
import {
  AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT,
  createAutomaticTestFrame,
} from '../services/holistic';

const mocks = vi.hoisted(() => ({
  frameSink: { current: null as ((frame: HolisticFrame) => void) | null },
  cameraStart: vi.fn(),
  cameraStop: vi.fn(),
  landmarkerStart: vi.fn(),
  landmarkerStop: vi.fn(),
  submitWord: vi.fn(),
  submitColor: vi.fn(),
  createSpeech: vi.fn(),
  browserSpeak: vi.fn(),
}));

vi.mock('../hooks/useCameraStream', () => ({
  useCameraStream: () => {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const start = useCallback(async () => {
      mocks.cameraStart();
      const next = { getTracks: () => [] } as unknown as MediaStream;
      setStream(next);
      return next;
    }, []);
    const stop = useCallback(() => { mocks.cameraStop(); setStream(null); }, []);
    return { stream, start, stop };
  },
}));

vi.mock('../hooks/useHolisticLandmarker', () => ({
  useHolisticLandmarker: (
    _videoRef: unknown,
    enabled: boolean,
    onFrame: (frame: HolisticFrame) => void,
  ) => {
    mocks.frameSink.current = onFrame;
    return {
      status: enabled ? 'ready' : 'idle',
      error: null,
      start: mocks.landmarkerStart,
      stop: mocks.landmarkerStop,
    };
  },
}));

vi.mock('../services/recognition-api', () => ({
  landmarkRecognitionApi: { submitWordSequence: mocks.submitWord, submitColorExperiment: mocks.submitColor },
  recognitionErrorMessage: () => 'Reconnaissance indisponible.',
}));

vi.mock('../services/speech-api', () => ({
  speechApi: { createForSign: mocks.createSpeech },
}));

vi.mock('../services/browser-speech', () => ({
  speakWithBrowser: mocks.browserSpeak,
}));

describe('RecognitionWorkspace automatic flow', () => {
  afterEach(() => vi.unstubAllEnvs());
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.frameSink.current = null;
    mocks.submitWord
      .mockResolvedValueOnce({
        status: 'recognized',
        label_key: 'HELLO',
        label_ar: 'سلام',
        confidence: 0.94,
        unknown: false,
        latency_ms: 25,
      })
      .mockResolvedValueOnce({
        status: 'unknown',
        label_key: null,
        label_ar: null,
        confidence: 0.24,
        unknown: true,
        latency_ms: 27,
      });
    mocks.createSpeech.mockResolvedValue({
      generation_id: 'speech-1',
      status: 'ready',
      audio: { url: '/generated.wav', mime_type: 'audio/wav' },
    });
    vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  });

  it('initializes, submits two signs automatically, speaks known once, and never speaks UNKNOWN', async () => {
    render(<RecognitionWorkspace />);
    await act(async () => {
      await screen.getByRole('button', { name: 'Activer la caméra' }).click();
    });

    expect(mocks.cameraStart).toHaveBeenCalledOnce();
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt — Faites un signe'));
    expect(screen.queryByRole('button', { name: /Commencer|Terminer|Envoyer|Reconnaître/i })).toBeNull();

    const timestampBase = performance.now() + 100;
    act(() => {
      for (let index = 0; index < 48; index += 1) {
        mocks.frameSink.current?.(createAutomaticTestFrame(index, timestampBase + index * 70));
      }
    });

    await waitFor(() => expect(screen.getByTestId('arabic-result')).toHaveTextContent('سلام'));
    await waitFor(() => expect(mocks.createSpeech).toHaveBeenCalledOnce());
    expect(mocks.createSpeech).toHaveBeenCalledWith('HELLO');
    expect(mocks.submitWord).toHaveBeenCalledTimes(1);

    act(() => {
      document.querySelector('audio')?.dispatchEvent(new Event('ended'));
      for (let index = 48; index < AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT; index += 1) {
        mocks.frameSink.current?.(createAutomaticTestFrame(index, timestampBase + index * 70));
      }
    });

    await waitFor(() =>
      expect(screen.getByTestId('arabic-result')).toHaveTextContent('الإشارة غير معروفة'),
    );
    expect(mocks.submitWord).toHaveBeenCalledTimes(2);
    expect(mocks.createSpeech).toHaveBeenCalledTimes(1);
    expect(mocks.browserSpeak).not.toHaveBeenCalled();

    const firstPayload = mocks.submitWord.mock.calls[0][0];
    expect(firstPayload.frames).toHaveLength(60);
    expect(firstPayload.frames[0].landmarks).toHaveLength(75);
    expect(firstPayload).not.toHaveProperty('anonymous_session_id');
    expect(firstPayload).not.toHaveProperty('video');
    expect(firstPayload).not.toHaveProperty('image');
    expect(firstPayload).not.toHaveProperty('audio');
  });

  it('clears a recognized result and starts a fresh attempt without restarting the camera', async () => {
    mocks.submitWord.mockReset().mockResolvedValueOnce({
      status: 'recognized', label_key: 'HELLO', label_ar: 'سلام', confidence: 0.94, unknown: false, latency_ms: 25,
    }).mockResolvedValueOnce({
      status: 'unknown', label_key: null, label_ar: null, confidence: 0.2, unknown: true, latency_ms: 25,
    });
    render(<RecognitionWorkspace />);
    expect(screen.queryByRole('button', { name: 'Refaire un signe' })).toBeNull();
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByTestId('arabic-result')).toHaveTextContent('سلام'));
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(screen.queryByTestId('arabic-result')).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    expect(mocks.cameraStart).toHaveBeenCalledTimes(1);
    expect(mocks.cameraStop).not.toHaveBeenCalled();
    expect(mocks.landmarkerStart).toHaveBeenCalledTimes(1);
    expect(mocks.landmarkerStop).not.toHaveBeenCalled();
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + 10_000 + i * 70)); });
    await waitFor(() => expect(screen.getByTestId('arabic-result')).toHaveTextContent('الإشارة غير معروفة'));
    expect(mocks.submitWord).toHaveBeenCalledTimes(2);
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(screen.queryByTestId('arabic-result')).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
  });

  it('aborts and ignores an old response even if reset is clicked repeatedly', async () => {
    let finishOld!: (value: unknown) => void;
    const old = new Promise((resolve) => { finishOld = resolve; });
    mocks.submitWord.mockReset().mockReturnValueOnce(old).mockResolvedValueOnce({
      status: 'recognized', label_key: 'NEW', label_ar: 'جديد', confidence: 0.8, unknown: false, latency_ms: 10,
    });
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(mocks.submitWord).toHaveBeenCalledTimes(1));
    const signal = mocks.submitWord.mock.calls[0][1] as AbortSignal;
    const button = screen.getByRole('button', { name: 'Refaire un signe' });
    act(() => { button.click(); button.click(); });
    expect(signal.aborted).toBe(true);
    await act(async () => { finishOld({ status: 'recognized', label_key: 'OLD', label_ar: 'قديم', confidence: 0.9, unknown: false, latency_ms: 1 }); await old; });
    expect(screen.queryByTestId('arabic-result')).toBeNull();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + 10_000 + i * 70)); });
    await waitFor(() => expect(screen.getByTestId('arabic-result')).toHaveTextContent('جديد'));
    expect(mocks.cameraStart).toHaveBeenCalledTimes(1);
    expect(mocks.cameraStop).not.toHaveBeenCalled();
  });

  it('does not start fallback speech if audio playback rejects after reset', async () => {
    let rejectPlayback!: (reason: Error) => void;
    const pendingPlayback = new Promise<void>((_resolve, reject) => { rejectPlayback = reject; });
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockReturnValueOnce(pendingPlayback);
    mocks.submitWord.mockReset().mockResolvedValueOnce({
      status: 'recognized', label_key: 'HELLO', label_ar: 'سلام', confidence: 0.9, unknown: false, latency_ms: 1,
    });
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(HTMLMediaElement.prototype.play).toHaveBeenCalled());
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    await act(async () => { rejectPlayback(new Error('late playback failure')); await pendingPlayback.catch(() => undefined); });
    expect(mocks.browserSpeak).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
  });

  it('clears an inference error and returns to ready', async () => {
    mocks.submitWord.mockReset().mockRejectedValueOnce(new Error('offline'));
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByText('offline')).toBeInTheDocument());
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(screen.queryByText('offline')).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
  });

  it('shows only an unvalidated candidate in explicit local experimental mode', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue',
      calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => {
      screen.getByLabelText(/Mode couleurs expérimental local/).click();
      screen.getByRole('button', { name: 'Activer la caméra' }).click();
    });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const timestampBase = performance.now() + 100;
    act(() => {
      for (let index = 0; index < 48; index += 1) {
        mocks.frameSink.current?.(createAutomaticTestFrame(index, timestampBase + index * 70));
      }
    });
    await waitFor(() => expect(screen.getByText(/Candidat expérimental non validé : blue/)).toBeInTheDocument());
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(screen.queryByText(/Candidat expérimental non validé/)).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    expect(mocks.cameraStart).toHaveBeenCalledTimes(1);
    vi.unstubAllEnvs();
  });

  it('invalidates a pending experimental candidate on reset', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    let finishOld!: (value: unknown) => void;
    const pending = new Promise((resolve) => { finishOld = resolve; });
    mocks.submitColor.mockReset().mockReturnValueOnce(pending);
    render(<RecognitionWorkspace />);
    await act(async () => {
      screen.getByLabelText(/Mode couleurs expérimental local/).click();
      screen.getByRole('button', { name: 'Activer la caméra' }).click();
    });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(mocks.submitColor).toHaveBeenCalledTimes(1));
    const signal = mocks.submitColor.mock.calls[0][2] as AbortSignal;
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(signal.aborted).toBe(true);
    await act(async () => {
      finishOld({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue', calibration_status: 'UNCALIBRATED', experimental: true });
      await pending;
    });
    expect(screen.queryByText(/Candidat expérimental/)).toBeNull();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    vi.unstubAllEnvs();
  });

  it('keeps recognized text visible and offers one retry when speech is unavailable', async () => {
    mocks.createSpeech.mockReset().mockRejectedValueOnce(new Error('speech unavailable'));
    mocks.browserSpeak.mockImplementationOnce(() => {
      throw new Error('browser voice unavailable');
    });
    render(<RecognitionWorkspace />);
    await act(async () => {
      await screen.getByRole('button', { name: 'Activer la caméra' }).click();
    });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));

    const timestampBase = performance.now() + 100;
    act(() => {
      for (let index = 0; index < 48; index += 1) {
        mocks.frameSink.current?.(createAutomaticTestFrame(index, timestampBase + index * 70));
      }
    });

    await waitFor(() => expect(screen.getByTestId('arabic-result')).toHaveTextContent('سلام'));
    await waitFor(() => expect(screen.getByText(/Audio indisponible/i)).toBeInTheDocument());
    expect(screen.getByRole('button', { name: 'Répéter l’audio' })).toBeEnabled();
    expect(mocks.createSpeech).toHaveBeenCalledOnce();
    expect(mocks.browserSpeak).toHaveBeenCalledOnce();
  });
});
