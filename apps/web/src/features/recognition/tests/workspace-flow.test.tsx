import { act, render, screen, waitFor } from '@testing-library/react';
import { useCallback, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { RecognitionWorkspace } from '../components/RecognitionWorkspace';
import type { HolisticFrame } from '../domain/landmarks';
import {
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
  afterEach(() => { vi.unstubAllEnvs(); window.history.replaceState({}, '', '/'); });
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

  it('shows only an unvalidated candidate in explicit local experimental mode', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue',
      calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => {
      screen.getByRole('button', { name: 'Activer la caméra' }).click();
    });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const timestampBase = performance.now() + 100;
    act(() => {
      for (let index = 0; index < 48; index += 1) {
        mocks.frameSink.current?.(createAutomaticTestFrame(index, timestampBase + index * 70));
      }
    });
    await waitFor(() => expect(screen.getByText(/Bleu — Prédiction expérimentale/)).toBeInTheDocument());
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    expect(screen.queryByText(/Bleu — Prédiction expérimentale/)).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    expect(mocks.cameraStart).toHaveBeenCalledTimes(1);
    expect(mocks.cameraStop).not.toHaveBeenCalled();
    expect(mocks.landmarkerStop).not.toHaveBeenCalled();
    vi.unstubAllEnvs();
  });

  it('invalidates a pending experimental candidate on reset', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    let finishOld!: (value: unknown) => void;
    const pending = new Promise((resolve) => { finishOld = resolve; });
    mocks.submitColor.mockReset().mockReturnValueOnce(pending);
    render(<RecognitionWorkspace />);
    await act(async () => {
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
    expect(screen.queryByText(/Bleu — Prédiction expérimentale/)).toBeNull();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent('Prêt');
    vi.unstubAllEnvs();
  });

  it.each([
    ['UNKNOWN_SIGN', null, /Signe inconnu/],
    ['MODEL_NOT_READY', null, /MODEL_NOT_READY/],
    ['UNKNOWN_SIGN', 'legacy_arabic', /Signe inconnu/],
  ])('handles %s without speaking or displaying unsupported labels', async (state, candidate, message) => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockReset().mockResolvedValue({ recognition_state: state, candidate,
      calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByText(message)).toBeInTheDocument());
    expect(screen.queryByText(/Couleur détectée/)).toBeNull();
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
  });

  it('records only local metadata and raw uncalibrated scores for a completed attempt', async () => {
    window.history.replaceState({}, '', '/?diagnostics=1');
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockReset().mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue',
      model_id: 'colors_v1_gru_experimental', experiment_id: 'gru-phase4-provisional-v1',
      model_version: '0.2.0-provisional-v1', calibration_status: 'UNCALIBRATED', experimental: true,
      diagnostics: { feature_schema_version: 'COLORS_V1_VIDEO_V1_EXPERIMENTAL', output_shape: [1, 9],
        top_three: [{ label: 'blue', raw_score: 0.1 }, { label: 'red', raw_score: -0.1 }, { label: 'pink', raw_score: -0.2 }] } });
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByText(/Bleu — Prédiction expérimentale/)).toBeInTheDocument());
    const records = JSON.parse(screen.getByTestId('attempt-diagnostics').textContent ?? '[]');
    expect(records).toHaveLength(1);
    expect(records[0]).toMatchObject({ request_status: 'response_received', completion_reason: 'stable',
      model_id: 'colors_v1_gru_experimental', experiment_id: 'gru-phase4-provisional-v1',
      model_version: '0.2.0-provisional-v1', sequence_length: 60, output_shape: [1, 9],
      top_three_raw_scores: [{ label: 'blue', raw_score: 0.1 }, { label: 'red', raw_score: -0.1 }, { label: 'pink', raw_score: -0.2 }] });
    expect(JSON.stringify(records)).not.toMatch(/landmarks|presence_mask|data:image/);
    expect(mocks.submitColor.mock.calls[0][3]).toBe(true);
  });

  it('marks a pending attempt aborted on reset and ignores its late response', async () => {
    window.history.replaceState({}, '', '/?diagnostics=1');
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    let finish!: (value: unknown) => void;
    const pending = new Promise((resolve) => { finish = resolve; });
    mocks.submitColor.mockReset().mockReturnValueOnce(pending);
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(mocks.submitColor).toHaveBeenCalledTimes(1));
    act(() => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    await act(async () => { finish({ candidate: 'blue', recognition_state: 'UNKNOWN_SIGN' }); await pending; });
    const records = JSON.parse(screen.getByTestId('attempt-diagnostics').textContent ?? '[]');
    expect(records[0]).toMatchObject({ request_status: 'aborted', reason: 'attempt_reset_or_camera_stopped' });
    expect(screen.queryByText(/Bleu — Prédiction expérimentale/)).toBeNull();
    expect(mocks.cameraStop).not.toHaveBeenCalled();
  });

  it('isolates three consecutive attempts and keeps the same camera after reset', async () => {
    window.history.replaceState({}, '', '/?diagnostics=1');
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockReset();
    for (const candidate of ['red', 'pink', 'white']) {
      mocks.submitColor.mockResolvedValueOnce({ recognition_state: 'UNKNOWN_SIGN', candidate,
        model_version: 'test', calibration_status: 'UNCALIBRATED', experimental: true });
    }
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    for (const [attempt, expected] of ['Rouge', 'Rose', 'Blanc'].entries()) {
      act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + attempt * 10_000 + i * 70)); });
      await waitFor(() => expect(screen.getByText(new RegExp(`${expected} — Prédiction expérimentale`))).toBeInTheDocument());
      act(() => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
      expect(screen.queryByText(new RegExp(`${expected} — Prédiction expérimentale`))).toBeNull();
    }
    const records = JSON.parse(screen.getByTestId('attempt-diagnostics').textContent ?? '[]');
    expect(records).toHaveLength(3);
    expect(new Set(records.map((item: { attempt_id: string }) => item.attempt_id)).size).toBe(3);
    expect(records.every((item: { request_status: string }) => item.request_status === 'response_received')).toBe(true);
    expect(mocks.submitColor).toHaveBeenCalledTimes(3);
    expect(mocks.cameraStart).toHaveBeenCalledTimes(1);
    expect(mocks.cameraStop).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
    expect(mocks.submitWord).not.toHaveBeenCalled();
  });

  it('does not expose diagnostics when the development build flag is disabled', async () => {
    window.history.replaceState({}, '', '/?diagnostics=1');
    vi.stubEnv('DEV', false);
    vi.stubEnv('VITE_COLORS_LOCAL_DIAGNOSTICS', 'false');
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    expect(screen.queryByText(/Diagnostics locaux/)).toBeNull();
  });

});
