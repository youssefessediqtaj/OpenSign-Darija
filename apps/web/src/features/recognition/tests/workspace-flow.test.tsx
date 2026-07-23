import { act, render, screen, waitFor } from '@testing-library/react';
import { useCallback, useState } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { RecognitionWorkspace } from '../components/RecognitionWorkspace';
import type { HolisticFrame } from '../domain/landmarks';
import {
  AUTOMATIC_TEST_SEQUENCE_FRAME_COUNT,
  createAutomaticTestFrame,
} from '../services/holistic';

const mocks = vi.hoisted(() => ({
  frameSink: { current: null as ((frame: HolisticFrame) => void) | null },
  cameraStart: vi.fn(),
  landmarkerStart: vi.fn(),
  landmarkerStop: vi.fn(),
  submitWord: vi.fn(),
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
    const stop = useCallback(() => setStream(null), []);
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
  landmarkRecognitionApi: { submitWordSequence: mocks.submitWord },
  recognitionErrorMessage: () => 'Reconnaissance indisponible.',
}));

vi.mock('../services/speech-api', () => ({
  speechApi: { createForSign: mocks.createSpeech },
}));

vi.mock('../services/browser-speech', () => ({
  speakWithBrowser: mocks.browserSpeak,
}));

describe('RecognitionWorkspace automatic flow', () => {
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
