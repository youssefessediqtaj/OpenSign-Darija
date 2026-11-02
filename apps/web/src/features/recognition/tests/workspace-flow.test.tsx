import { act, render, screen, waitFor } from '@testing-library/react';
import { useCallback, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../../shared/api/client';
import { RecognitionWorkspace } from '../components/RecognitionWorkspace';
import type { HolisticFrame } from '../domain/landmarks';
import {
  createAutomaticTestFrame,
  createSyntheticFrame,
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

vi.mock('../services/landmark-overlay', () => ({ drawLandmarkOverlay: vi.fn() }));

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
  recognitionErrorMessage: (error: { code?: string }) => error.code === 'INCOMPATIBLE_MODEL_OUTPUT'
    ? 'Réponse incompatible du modèle couleurs.' : error.code === 'MODEL_NOT_READY'
      ? 'Modèle de reconnaissance indisponible.' : 'Reconnaissance indisponible.',
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

  it('reports actual hand counts and keeps tracking across Sign Again', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    window.history.replaceState({}, '', '/?diagnostics=1');
    mocks.submitColor.mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue', calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => { screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByText(/Bleu — Prédiction expérimentale/)).toBeInTheDocument());
    expect(screen.getByTestId('tracking-diagnostics')).toHaveTextContent('Left hand: YES; raw 21/21; valid 21/21');
    expect(screen.getByTestId('tracking-diagnostics')).toHaveTextContent('Right hand: YES; raw 21/21; valid 21/21');
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    act(() => { const frame = createAutomaticTestFrame(0, base + 4000); frame.leftHand = []; mocks.frameSink.current?.(frame); });
    expect(screen.getByTestId('tracking-diagnostics')).toHaveTextContent('Left hand: NO');
    expect(screen.getByTestId('tracking-diagnostics')).toHaveTextContent('Right hand: YES; raw 21/21; valid 21/21');
    expect(mocks.landmarkerStart).toHaveBeenCalledTimes(1);
    expect(mocks.landmarkerStop).not.toHaveBeenCalled();
  });

  it('sends a validated tracked gesture after pose-confirmed return to rest', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    window.history.replaceState({}, '', '/?diagnostics=1');
    mocks.submitColor.mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue', calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => { screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    const base = performance.now() + 100;
    act(() => {
      for (let i = 0; i < 45; i += 1) {
        const frame = createSyntheticFrame(i, base + i * 70, i < 4 ? 'rest' : i < 20 ? 'gesture-a' : 'rest', i >= 4 && i < 20);
        if (i >= 20) { frame.leftHand = []; frame.rightHand = []; frame.metadata.leftHandDetected = false; frame.metadata.rightHandDetected = false; }
        mocks.frameSink.current?.(frame);
      }
    });
    await waitFor(() => expect(mocks.submitColor).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('segmentation-outcome')).toHaveTextContent('pose_rest_after_disappearance');
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
  });

  it('restricts manual capture to local diagnostics and validates before the color request', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    window.history.replaceState({}, '', '/?diagnostics=1');
    mocks.submitColor.mockResolvedValue({ recognition_state: 'UNKNOWN_SIGN', candidate: 'blue', calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => { screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    expect(screen.queryByRole('button', { name: 'Démarrer la capture' })).toBeNull();
    await act(async () => { screen.getByRole('checkbox', { name: /Mode manuel expérimental/ }).click(); });
    await act(async () => { screen.getByRole('button', { name: 'Démarrer la capture' }).click(); });
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 12; i += 1) mocks.frameSink.current?.(createSyntheticFrame(i, base + i * 70, 'no-hands', false)); });
    await act(async () => { screen.getByRole('button', { name: 'Arrêter la capture' }).click(); });
    expect(mocks.submitColor).not.toHaveBeenCalled();
    expect(screen.getByTestId('segmentation-outcome')).toHaveTextContent('insufficient_usable_frames');
    await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    await act(async () => { screen.getByRole('button', { name: 'Démarrer la capture' }).click(); });
    act(() => { for (let i = 0; i < 25; i += 1) mocks.frameSink.current?.(createSyntheticFrame(i, base + 3000 + i * 70, 'gesture-a', true)); });
    await act(async () => { screen.getByRole('button', { name: 'Arrêter la capture' }).click(); });
    await waitFor(() => expect(mocks.submitColor).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('segmentation-outcome')).toHaveTextContent('manual');
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
  });

  it('keeps three manual attempts isolated and records the real start and stop triggers', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    window.history.replaceState({}, '', '/?diagnostics=1');
    mocks.submitColor.mockReset();
    for (const candidate of ['red', 'pink', 'white']) mocks.submitColor.mockResolvedValueOnce({ recognition_state: 'UNKNOWN_SIGN', candidate, calibration_status: 'UNCALIBRATED', experimental: true });
    render(<RecognitionWorkspace />);
    await act(async () => { screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await act(async () => { screen.getByRole('checkbox', { name: /Mode manuel expérimental/ }).click(); });
    const base = performance.now() + 100;
    // Enabled manual mode cannot start or submit just because movement is present.
    act(() => { for (let i = 0; i < 25; i += 1) mocks.frameSink.current?.(createSyntheticFrame(i, base + i * 70, 'gesture-a', true)); });
    expect(mocks.submitColor).not.toHaveBeenCalled();
    for (const [attempt, expected] of ['Rouge', 'Rose', 'Blanc'].entries()) {
      await act(async () => { screen.getByRole('button', { name: 'Démarrer la capture' }).click(); });
      act(() => { for (let i = 0; i < 24; i += 1) mocks.frameSink.current?.(createSyntheticFrame(i, base + 5000 + attempt * 4000 + i * 70, 'gesture-a', true)); });
      expect(screen.getByTestId('segmentation-diagnostics')).toHaveTextContent('Capture mode: manual');
      expect(screen.getByTestId('segmentation-diagnostics')).toHaveTextContent('Captured frames: 24');
      await act(async () => { screen.getByRole('button', { name: 'Arrêter la capture' }).click(); });
      await waitFor(() => expect(screen.getByText(new RegExp(`${expected} — Prédiction expérimentale`))).toBeInTheDocument());
      await act(async () => { screen.getByRole('button', { name: 'Refaire un signe' }).click(); });
    }
    const records = JSON.parse(screen.getByTestId('attempt-diagnostics').textContent ?? '[]');
    expect(records).toHaveLength(3);
    expect(records.every((item: { capture_mode: string; start_trigger: string; stop_trigger: string; captured_frames: number }) => item.capture_mode === 'manual' && item.start_trigger === 'manual_start' && item.stop_trigger === 'manual' && item.captured_frames === 24)).toBe(true);
    expect(mocks.submitColor).toHaveBeenCalledTimes(3);
    expect(mocks.submitWord).not.toHaveBeenCalled();
    expect(mocks.createSpeech).not.toHaveBeenCalled();
  });

  it('reports a manual timeout separately and never sends it to inference', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    window.history.replaceState({}, '', '/?diagnostics=1');
    render(<RecognitionWorkspace />);
    await act(async () => { screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await act(async () => { screen.getByRole('checkbox', { name: /Mode manuel expérimental/ }).click(); });
    await act(async () => { screen.getByRole('button', { name: 'Démarrer la capture' }).click(); });
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i <= 61; i += 1) mocks.frameSink.current?.(createSyntheticFrame(i, base + i * 100, 'gesture-a', true)); });
    expect(screen.getByTestId('segmentation-outcome')).toHaveTextContent('Mode : manual');
    expect(screen.getByTestId('segmentation-outcome')).toHaveTextContent('maximum_duration');
    expect(screen.getByText(/Capture manuelle interrompue après 6 secondes/)).toBeInTheDocument();
    expect(mocks.submitColor).not.toHaveBeenCalled();
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
    ['MODEL_NOT_READY', null, /Modèle de reconnaissance indisponible/],
    ['INCOMPATIBLE_MODEL_OUTPUT', null, /Réponse incompatible/],
    ['UNKNOWN_SIGN', 'legacy_arabic', /Réponse incompatible/],
    ['UNKNOWN_SIGN', 'toString', /Réponse incompatible/],
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

  it('handles the gateway 503 without stopping the camera or speaking', async () => {
    vi.stubEnv('VITE_COLORS_EXPERIMENTAL_TOKEN', 'local_test_token_2026');
    mocks.submitColor.mockReset().mockRejectedValue(new ApiError('', 'MODEL_NOT_READY', {}, 503));
    render(<RecognitionWorkspace />);
    await act(async () => { await screen.getByRole('button', { name: 'Activer la caméra' }).click(); });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Prêt'));
    const base = performance.now() + 100;
    act(() => { for (let i = 0; i < 48; i += 1) mocks.frameSink.current?.(createAutomaticTestFrame(i, base + i * 70)); });
    await waitFor(() => expect(screen.getByText('Modèle de reconnaissance indisponible.')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: 'Refaire un signe' })).toBeInTheDocument();
    expect(mocks.cameraStop).not.toHaveBeenCalled();
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
    expect(JSON.stringify(records)).not.toMatch(/"(?:pose|leftHand|rightHand|presence_mask)"\s*:|data:image/);
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
