import { CameraOff, RotateCcw } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { env } from '../../../shared/config/env';
import { Button } from '../../../shared/ui/Button';
import { SkipLink } from '../../../shared/ui/SkipLink';
import { CameraPermissionPanel } from './CameraPermissionPanel';
import { CameraPreview } from './CameraPreview';
import { useCameraPermission } from '../hooks/useCameraPermission';
import { useCameraStream } from '../hooks/useCameraStream';
import { useHolisticLandmarker } from '../hooks/useHolisticLandmarker';
import { AutomaticSignSegmenter } from '../domain/automatic-segmentation';
import type { HolisticFrame } from '../domain/landmarks';
import type { AttemptDiagnostic } from '../domain/attempt-diagnostics';
import { ApiError } from '../../../shared/api/client';
import {
  createLandmarkSequence,
  toWordLandmarkPayload,
  validateWordRecognitionPayloadV1,
  wordValidationErrorMessage,
} from '../domain/build-recognition-payload';
import { landmarkRecognitionApi, recognitionErrorMessage } from '../services/recognition-api';
import type {
  RecognitionFlowState,
  SegmentedSign,
} from '../state/recognition-flow';

const FLOW_LABELS: Record<RecognitionFlowState, string> = {
  CAMERA_OFF: 'Caméra éteinte',
  INITIALIZING: 'Initialisation de la caméra…',
  WAITING_FOR_SIGN: 'Prêt — Faites un signe',
  CAPTURING: 'Signe détecté…',
  RECOGNIZING: 'Reconnaissance en cours…',
  DISPLAYING: 'Résultat disponible',
  SPEAKING: 'Lecture audio…',
  COOLDOWN: 'Revenez en position de repos',
  ERROR: 'Analyse interrompue',
};

const REJECTION_MESSAGES = {
  too_short: 'Signe trop court. Réessayez naturellement.',
  insufficient_usable_frames: 'Gardez au moins une main et le haut du corps visibles.',
  unreliable_boundary: 'Le début ou la fin du signe n’est pas assez net.',
} as const;

const COLOR_LABELS: Record<string, string> = {
  black: '⚫ Noir', blue: '🔵 Bleu', brown: '🟤 Marron', green: '🟢 Vert',
  orange: '🟠 Orange', pink: '🩷 Rose', red: '🔴 Rouge', white: '⚪ Blanc', yellow: '🟡 Jaune',
};

export function RecognitionWorkspace() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const segmenterRef = useRef(new AutomaticSignSegmenter());
  const flowStateRef = useRef<RecognitionFlowState>('CAMERA_OFF');
  const recognizeSegmentRef = useRef<(segment: SegmentedSign) => void>(() => undefined);
  const sessionRef = useRef(0);
  const recognitionRequestRef = useRef<AbortController | null>(null);
  const hadCameraStreamRef = useRef(false);
  const timerRefs = useRef(new Set<number>());
  const [flowState, setFlowState] = useState<RecognitionFlowState>('CAMERA_OFF');
  const pendingAttemptRef = useRef<string | null>(null);
  const [attempts, setAttempts] = useState<AttemptDiagnostic[]>([]);
  const [candidate, setCandidate] = useState<string | null>(null);
  const [detailMessage, setDetailMessage] = useState('');
  const colorsToken = import.meta.env.VITE_COLORS_EXPERIMENTAL_TOKEN ?? '';
  let localHost = false;
  try {
    localHost = ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname) &&
      new URL(env.apiBaseUrl || window.location.origin, window.location.origin).origin === window.location.origin;
  } catch { /* Invalid API configuration is unavailable. */ }
  const diagnosticsEnabled = (import.meta.env.DEV || import.meta.env.VITE_COLORS_LOCAL_DIAGNOSTICS === 'true') &&
    localHost && colorsToken.length >= 16 &&
    new URLSearchParams(window.location.search).get('diagnostics') === '1';
  const recordAttempt = useCallback((record: AttemptDiagnostic) => {
    if (diagnosticsEnabled) setAttempts((previous) => [...previous, record].slice(-30));
  }, [diagnosticsEnabled]);
  const updateAttempt = useCallback((id: string, update: Partial<AttemptDiagnostic>) => {
    if (diagnosticsEnabled) setAttempts((previous) => previous.map((item) =>
      item.attempt_id === id ? { ...item, ...update } : item));
  }, [diagnosticsEnabled]);
  const cancelPendingAttempt = useCallback(() => {
    if (pendingAttemptRef.current) updateAttempt(pendingAttemptRef.current, { request_status: 'aborted', reason: 'attempt_reset_or_camera_stopped' });
    pendingAttemptRef.current = null;
  }, [updateAttempt]);

  const transition = useCallback((nextState: RecognitionFlowState) => {
    flowStateRef.current = nextState;
    setFlowState(nextState);
  }, []);

  const clearTimers = useCallback(() => {
    timerRefs.current.forEach((timer) => window.clearTimeout(timer));
    timerRefs.current.clear();
  }, []);

  const schedule = useCallback((callback: () => void, delayMs: number) => {
    const timer = window.setTimeout(() => {
      timerRefs.current.delete(timer);
      callback();
    }, delayMs);
    timerRefs.current.add(timer);
    return timer;
  }, []);

  const {
    status: permissionStatus,
    errorMessage: permissionErrorMessage,
    setStatus: setPermissionStatus,
    markRequesting,
    markGranted,
    markError,
  } = useCameraPermission();
  const {
    stream: cameraStream,
    start: startCameraStream,
    stop: stopCameraStream,
  } = useCameraStream(markError);

  const enterCooldown = useCallback(() => {
    if (!cameraStream) return;
    segmenterRef.current.beginCooldown(performance.now());
    transition('COOLDOWN');
  }, [cameraStream, transition]);

  const recognizeSegment = useCallback(
    async (segment: SegmentedSign) => {
      const session = sessionRef.current;
      recordAttempt({ attempt_id: segment.id, segment_start_ms: segment.startedAtMs, segment_end_ms: segment.endedAtMs,
        captured_frames: segment.sourceFrames.length, processed_frames: segment.usableFrameCount, sequence_length: null,
        hand_coverage: null, pose_coverage: null, completion_reason: 'stable', input_feature_schema: null,
        model_feature_schema: null, model_version: null, request_status: 'not_sent', reason: null,
        output_shape: null, top_three_raw_scores: null });
      if (segmenterRef.current.shouldSuppressDuplicate(segment, performance.now())) {
        updateAttempt(segment.id, { reason: 'duplicate_suppressed' });
        setDetailMessage('Signe déjà traité. Revenez en position de repos.');
        enterCooldown();
        return;
      }
      const controller = new AbortController();
      recognitionRequestRef.current?.abort();
      recognitionRequestRef.current = controller;
      try {
        const sequence = createLandmarkSequence(segment.sourceFrames, new Date().toISOString());
        const payload = toWordLandmarkPayload(sequence, {
          kind: segment.kind,
          reliable: segment.reliable,
          usableFrameCount: segment.usableFrameCount,
        });
        const validation = validateWordRecognitionPayloadV1(payload, {
          rawFrameCount: sequence.rawFrameCount,
          validFrameCount: sequence.validFrameCount,
        });
        updateAttempt(segment.id, { processed_frames: sequence.validFrameCount, sequence_length: payload.frames.length, hand_coverage: payload.quality.detected_hand_ratio,
          pose_coverage: payload.quality.detected_pose_ratio, input_feature_schema: payload.feature_schema_version });
        if (!validation.valid) {
          updateAttempt(segment.id, { request_status: 'not_sent', reason: validation.errors[0]?.code ?? 'invalid_input' });
          setCandidate(null);
          setDetailMessage(wordValidationErrorMessage(validation.errors[0]));
          enterCooldown();
          return;
        }

        if (!localHost || colorsToken.length < 16) {
          throw new Error('MODEL_NOT_READY — Modèle couleurs expérimental indisponible.');
        }
        pendingAttemptRef.current = segment.id;
        updateAttempt(segment.id, { request_status: 'pending' });
        const diagnostic = await landmarkRecognitionApi.submitColorExperiment(payload, colorsToken, controller.signal, diagnosticsEnabled);
        if (session !== sessionRef.current || !cameraStream) return;
        pendingAttemptRef.current = null;
        updateAttempt(segment.id, { request_status: 'response_received', reason: diagnostic.diagnostics?.failure_stage ?? diagnostic.recognition_state,
          model_id: diagnostic.model_id ?? null, experiment_id: diagnostic.experiment_id ?? null,
          model_version: diagnostic.model_version ?? null, model_feature_schema: diagnostic.diagnostics?.feature_schema_version ?? null,
          output_shape: diagnostic.diagnostics?.output_shape ?? null, top_three_raw_scores: diagnostic.diagnostics?.top_three ?? null });
        const label = diagnostic.candidate && COLOR_LABELS[diagnostic.candidate];
        setCandidate(label || null);
        setDetailMessage(label ? 'Aucune décision fiable : candidat non calibré et non validé.' :
          diagnostic.recognition_state === 'MODEL_NOT_READY' ? 'MODEL_NOT_READY — Modèle couleurs indisponible.' :
          diagnostic.recognition_state === 'UNKNOWN_SIGN' ? 'Signe inconnu — aucune décision fiable.' :
          diagnostic.recognition_state === 'NO_HAND_DETECTED' ? 'Aucune main détectée. Gardez votre main visible.' :
          diagnostic.recognition_state === 'INSUFFICIENT_FRAMES' ? 'Capture insuffisante. Réessayez avec une main visible.' :
          diagnostic.recognition_state === 'PREPROCESSING_ERROR' ? 'Les points capturés ne sont pas utilisables.' :
          'Erreur pendant le calcul du modèle expérimental.');
        transition('DISPLAYING');
        schedule(enterCooldown, 1_500);
      } catch (error) {
        if (session !== sessionRef.current || !cameraStream) return;
        pendingAttemptRef.current = null;
        const reason = error instanceof ApiError ? `http_${error.status ?? 'unknown'}` :
          error instanceof DOMException && error.name === 'AbortError' ? 'timeout_or_abort' :
          error instanceof TypeError ? 'network_error' : 'local_error';
        updateAttempt(segment.id, { request_status: 'failed', reason });
        setCandidate(null);
        setDetailMessage(error instanceof ApiError ? recognitionErrorMessage(error) :
          error instanceof DOMException && error.name === 'AbortError' ? 'La requête a expiré.' :
          error instanceof TypeError ? 'Connexion au service impossible.' :
          error instanceof Error ? error.message : 'Analyse impossible.');
        transition('ERROR');
        schedule(enterCooldown, 1_800);
      } finally {
        if (recognitionRequestRef.current === controller) recognitionRequestRef.current = null;
      }
    },
    [cameraStream, colorsToken, diagnosticsEnabled, localHost, enterCooldown, recordAttempt, updateAttempt, schedule, transition],
  );

  useEffect(() => {
    recognizeSegmentRef.current = (segment) => {
      void recognizeSegment(segment);
    };
  }, [recognizeSegment]);

  const handleFrame = useCallback(
    (frame: HolisticFrame) => {
      const event = segmenterRef.current.ingest(frame, flowStateRef.current);
      if (event.type === 'started') {
        setDetailMessage(event.kind === 'static' ? 'Signe statique détecté.' : 'Mouvement détecté.');
        transition('CAPTURING');
      } else if (event.type === 'completed') {
        setDetailMessage('');
        transition('RECOGNIZING');
        recognizeSegmentRef.current(event.segment);
      } else if (event.type === 'rejected') {
        recordAttempt({ attempt_id: event.attempt.id, segment_start_ms: event.attempt.startedAtMs, segment_end_ms: event.attempt.endedAtMs,
          captured_frames: event.attempt.capturedFrames, processed_frames: event.attempt.usableFrames, sequence_length: null,
          hand_coverage: event.attempt.handCoverage, pose_coverage: event.attempt.poseCoverage, completion_reason: event.attempt.completionReason,
          input_feature_schema: null, model_feature_schema: null, model_version: null, request_status: 'not_sent',
          reason: event.reason, output_shape: null, top_three_raw_scores: null });
        setDetailMessage(REJECTION_MESSAGES[event.reason]);
        segmenterRef.current.beginCooldown(frame.timestampMs);
        transition('COOLDOWN');
      } else if (event.type === 'reset') {
        setCandidate(null);
        setDetailMessage('');
        transition('WAITING_FOR_SIGN');
      }
    },
    [recordAttempt, transition],
  );

  const {
    status: landmarkerStatus,
    error: landmarkerError,
    start: startLandmarker,
    stop: stopLandmarker,
  } = useHolisticLandmarker(videoRef, Boolean(cameraStream), handleFrame);

  const startCamera = useCallback(async () => {
    cancelPendingAttempt();
    recognitionRequestRef.current?.abort();
    recognitionRequestRef.current = null;
    clearTimers();
    sessionRef.current += 1;
    segmenterRef.current.reset();
    setCandidate(null);
    setDetailMessage('');
    markRequesting();
    transition('INITIALIZING');
    const stream = await startCameraStream();
    if (stream) {
      markGranted();
      setPermissionStatus('READY');
    } else {
      transition('ERROR');
    }
  }, [cancelPendingAttempt, clearTimers, markGranted, markRequesting, setPermissionStatus, startCameraStream, transition]);

  const stopCamera = useCallback(() => {
    sessionRef.current += 1;
    cancelPendingAttempt();
    recognitionRequestRef.current?.abort();
    recognitionRequestRef.current = null;
    clearTimers();
    stopLandmarker();
    stopCameraStream();
    segmenterRef.current.reset();
    setCandidate(null);
    setDetailMessage('');
    setPermissionStatus('STOPPED');
    transition('CAMERA_OFF');
  }, [cancelPendingAttempt, clearTimers, setPermissionStatus, stopCameraStream, stopLandmarker, transition]);

  useEffect(() => {
    if (!cameraStream) return;
    void startLandmarker();
  }, [cameraStream, startLandmarker]);

  useEffect(() => {
    if (cameraStream) {
      hadCameraStreamRef.current = true;
      return;
    }
    if (!hadCameraStreamRef.current) return;
    hadCameraStreamRef.current = false;
    sessionRef.current += 1;
    cancelPendingAttempt();
    recognitionRequestRef.current?.abort();
    recognitionRequestRef.current = null;
    clearTimers();
    stopLandmarker();
    segmenterRef.current.reset();
    setCandidate(null);
    setDetailMessage('');
    setPermissionStatus('STOPPED');
    transition('CAMERA_OFF');
  }, [cameraStream, cancelPendingAttempt, clearTimers, setPermissionStatus, stopLandmarker, transition]);

  useEffect(() => {
    if (!cameraStream) return;
    if (landmarkerStatus === 'ready' && flowStateRef.current === 'INITIALIZING') {
      setDetailMessage('La détection démarre automatiquement.');
      transition('WAITING_FOR_SIGN');
    } else if (landmarkerStatus === 'error') {
      setDetailMessage(landmarkerError ?? 'Le moteur de détection est indisponible.');
      transition('ERROR');
    }
  }, [cameraStream, landmarkerError, landmarkerStatus, transition]);

  useEffect(
    () => () => {
      sessionRef.current += 1;
      recognitionRequestRef.current?.abort();
      recognitionRequestRef.current = null;
      clearTimers();
    },
    [clearTimers],
  );

  const signAgain = useCallback(() => {
    // Invalidate both network and speech callbacks before clearing the attempt state.
    sessionRef.current += 1;
    cancelPendingAttempt();
    recognitionRequestRef.current?.abort();
    recognitionRequestRef.current = null;
    clearTimers();
    segmenterRef.current.reset();
    setCandidate(null);
    setDetailMessage('');
    transition('WAITING_FOR_SIGN');
  }, [cancelPendingAttempt, clearTimers, transition]);

  const cameraActive = Boolean(cameraStream);
  const canSignAgain = cameraActive && landmarkerStatus === 'ready' &&
    ['RECOGNIZING', 'DISPLAYING', 'SPEAKING', 'COOLDOWN', 'ERROR'].includes(flowState);

  return (
    <div className="min-h-screen bg-mist text-ink dark:bg-slate-950 dark:text-slate-50">
      <SkipLink />
      <header className="border-b border-slate-200 bg-white/95 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-4xl px-4 py-4 text-lg font-bold">OpenSigne Darija</div>
      </header>
      <main id="main" className="mx-auto max-w-4xl px-4 py-8 pb-[calc(env(safe-area-inset-bottom)+2rem)]">
        <div className="mb-6 max-w-2xl">
          <h1 className="text-3xl font-bold">Reconnaissance de signes</h1>
          <p className="mt-2 text-slate-700 dark:text-slate-300">
            Activez la caméra, puis signez naturellement. La détection, la reconnaissance et l’analyse
            sont automatiques. Les candidats de couleur sont expérimentaux et non validés.
          </p>
          <a
            href="/contribute"
            className="mt-4 inline-flex min-h-11 items-center rounded-md border border-cedar px-4 py-2 font-semibold text-cedar hover:bg-teal-50"
          >
            Aidez-nous à améliorer OpenSigne Darija
          </a>
        </div>

        {!cameraActive && (
          <div className="space-y-3">
            <CameraPermissionPanel
              onEnable={startCamera}
              errorMessage={permissionErrorMessage}
              isRequesting={permissionStatus === 'REQUESTING_PERMISSION'}
            />
            {flowState === 'INITIALIZING' && (
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300" role="status" aria-live="polite">
                {FLOW_LABELS.INITIALIZING}
              </p>
            )}
          </div>
        )}

        {cameraActive && (
          <div className="space-y-5">
            <CameraPreview stream={cameraStream} videoRef={videoRef} isMirrored>
              {null}
            </CameraPreview>

            <section
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
              aria-labelledby="recognition-status"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`h-3 w-3 rounded-full ${
                    flowState === 'ERROR'
                      ? 'bg-coral'
                      : flowState === 'WAITING_FOR_SIGN'
                        ? 'bg-emerald-500'
                        : 'bg-amber-400'
                  }`}
                  aria-hidden="true"
                />
                <p id="recognition-status" className="font-semibold" role="status" aria-live="polite">
                  {FLOW_LABELS[flowState]}
                </p>
              </div>
              {detailMessage && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{detailMessage}</p>}

              {candidate && (
                <div className="mt-5 border-t border-slate-200 pt-5 text-center dark:border-slate-700" aria-live="polite">
                  <p className="text-sm font-medium text-slate-500">Couleur détectée — Expérimental</p>
                  <p className="mt-2 text-3xl font-bold text-cedar dark:text-teal-300">{candidate} — Prédiction expérimentale</p>
                </div>
              )}
            </section>

            {diagnosticsEnabled && (
              <details className="rounded-xl border border-slate-200 bg-white p-4 dark:bg-slate-900">
                <summary className="cursor-pointer font-semibold">Diagnostics locaux ({attempts.length})</summary>
                <p className="mt-2 text-sm">En mémoire uniquement. Scores bruts non calibrés, pas des probabilités.</p>
                <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap text-xs" data-testid="attempt-diagnostics">{JSON.stringify(attempts, null, 2)}</pre>
              </details>
            )}
            <div className="flex flex-wrap gap-3">
              {canSignAgain && (
                <Button variant="secondary" onClick={signAgain} aria-label="Refaire un signe">
                  <RotateCcw className="mr-2 inline h-5 w-5" aria-hidden="true" />
                  Refaire un signe
                </Button>
              )}
              <Button variant="ghost" onClick={stopCamera}>
                <CameraOff className="mr-2 inline h-5 w-5" aria-hidden="true" />
                Éteindre la caméra
              </Button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
