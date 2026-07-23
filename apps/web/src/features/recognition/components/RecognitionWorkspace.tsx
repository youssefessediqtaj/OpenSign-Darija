import { CameraOff, Volume2 } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Button } from '../../../components/Button';
import { SkipLink } from '../../../components/SkipLink';
import { speakWithBrowser } from '../../speech/services/browser-speech.service';
import { speechApi } from '../../speech/services/speech-api.service';
import { CameraPermissionPanel } from './CameraPermissionPanel';
import { CameraPreview } from './CameraPreview';
import { useCameraPermission } from '../hooks/useCameraPermission';
import { useCameraStream } from '../hooks/useCameraStream';
import { useHolisticLandmarker } from '../hooks/useHolisticLandmarker';
import { AutomaticSignSegmenter } from '../services/automatic-segmentation.service';
import { landmarkRecognitionApi, recognitionErrorMessage } from '../services/recognition-api.service';
import {
  createLandmarkSequence,
  toWordLandmarkPayload,
  validateWordRecognitionPayloadV1,
  wordValidationErrorMessage,
} from '../services/sequence-validator.service';
import type { HolisticFrame } from '../types/landmark.types';
import type {
  PublicRecognitionResult,
  RecognitionFlowState,
  SegmentedSign,
} from '../types/recognition-flow.types';

const FLOW_LABELS: Record<RecognitionFlowState, string> = {
  CAMERA_OFF: 'Caméra éteinte',
  INITIALIZING: 'Initialisation de la caméra…',
  WAITING_FOR_SIGN: 'Prêt — Faites un signe',
  CAPTURING: 'Signe détecté…',
  RECOGNIZING: 'Reconnaissance en cours…',
  DISPLAYING: 'Résultat disponible',
  SPEAKING: 'Lecture audio…',
  COOLDOWN: 'Revenez en position de repos',
  ERROR: 'Service momentanément indisponible',
};

const REJECTION_MESSAGES = {
  too_short: 'Signe trop court. Réessayez naturellement.',
  insufficient_usable_frames: 'Gardez au moins une main et le haut du corps visibles.',
  unreliable_boundary: 'Le début ou la fin du signe n’est pas assez net.',
} as const;

type VisibleResult = {
  segmentId: string;
  labelKey: string | null;
  labelAr: string;
  unknown: boolean;
};

function isKnownResult(
  result: PublicRecognitionResult,
): result is PublicRecognitionResult & { label_key: string; label_ar: string } {
  return (
    result.status === 'recognized' &&
    result.unknown === false &&
    typeof result.label_key === 'string' &&
    result.label_key.length > 0 &&
    typeof result.label_ar === 'string' &&
    result.label_ar.length > 0
  );
}

export function RecognitionWorkspace() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const segmenterRef = useRef(new AutomaticSignSegmenter());
  const flowStateRef = useRef<RecognitionFlowState>('CAMERA_OFF');
  const recognizeSegmentRef = useRef<(segment: SegmentedSign) => void>(() => undefined);
  const sessionRef = useRef(0);
  const speechRunRef = useRef(0);
  const hadCameraStreamRef = useRef(false);
  const timerRefs = useRef(new Set<number>());
  const autoSpokenSegmentsRef = useRef(new Set<string>());
  const [flowState, setFlowState] = useState<RecognitionFlowState>('CAMERA_OFF');
  const [visibleResult, setVisibleResult] = useState<VisibleResult | null>(null);
  const [detailMessage, setDetailMessage] = useState('');
  const [audioMessage, setAudioMessage] = useState('');

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
    async (result: VisibleResult, automatic: boolean) => {
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
        if (speechRun === speechRunRef.current) playWithBrowserSpeech(result.labelAr, speechRun);
      }
    },
    [cancelSpeech, finishSpeech, playWithBrowserSpeech, schedule, transition],
  );

  const recognizeSegment = useCallback(
    async (segment: SegmentedSign) => {
      const session = sessionRef.current;
      if (segmenterRef.current.shouldSuppressDuplicate(segment, performance.now())) {
        setDetailMessage('Signe déjà traité. Revenez en position de repos.');
        enterCooldown();
        return;
      }

      try {
        const sequence = createLandmarkSequence(segment.sourceFrames, new Date().toISOString());
        const payload = toWordLandmarkPayload(sequence, undefined, {
          kind: segment.kind,
          reliable: segment.reliable,
          usableFrameCount: segment.usableFrameCount,
        });
        const validation = validateWordRecognitionPayloadV1(payload, {
          rawFrameCount: sequence.rawFrameCount,
          validFrameCount: sequence.validFrameCount,
        });
        if (!validation.valid) {
          throw new Error(wordValidationErrorMessage(validation.errors[0]));
        }

        const response = await landmarkRecognitionApi.submitWordSequence(payload);
        if (session !== sessionRef.current || !cameraStream) return;

        segmenterRef.current.rememberRecognized(segment, performance.now());
        if (!isKnownResult(response)) {
          const unknownResult: VisibleResult = {
            segmentId: segment.id,
            labelKey: null,
            labelAr: 'الإشارة غير معروفة',
            unknown: true,
          };
          setVisibleResult(unknownResult);
          setDetailMessage('Signe non reconnu. Réessayez avec un mouvement bien délimité.');
          setAudioMessage('');
          transition('DISPLAYING');
          schedule(enterCooldown, 1_500);
          return;
        }

        const knownResult: VisibleResult = {
          segmentId: segment.id,
          labelKey: response.label_key,
          labelAr: response.label_ar,
          unknown: false,
        };
        setVisibleResult(knownResult);
        setDetailMessage('');
        transition('DISPLAYING');
        void speakResult(knownResult, true);
      } catch (error) {
        if (session !== sessionRef.current || !cameraStream) return;
        setVisibleResult(null);
        setDetailMessage(
          error instanceof Error && !(error.name === 'ApiError')
            ? error.message
            : recognitionErrorMessage(error),
        );
        transition('ERROR');
        schedule(enterCooldown, 1_800);
      }
    },
    [cameraStream, enterCooldown, schedule, speakResult, transition],
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
        setDetailMessage(REJECTION_MESSAGES[event.reason]);
        segmenterRef.current.beginCooldown(frame.timestampMs);
        transition('COOLDOWN');
      } else if (event.type === 'reset') {
        setVisibleResult(null);
        setDetailMessage('');
        setAudioMessage('');
        transition('WAITING_FOR_SIGN');
      }
    },
    [transition],
  );

  const {
    status: landmarkerStatus,
    error: landmarkerError,
    start: startLandmarker,
    stop: stopLandmarker,
  } = useHolisticLandmarker(videoRef, Boolean(cameraStream), handleFrame);

  const startCamera = useCallback(async () => {
    clearTimers();
    cancelSpeech();
    sessionRef.current += 1;
    autoSpokenSegmentsRef.current.clear();
    segmenterRef.current.reset();
    setVisibleResult(null);
    setDetailMessage('');
    setAudioMessage('');
    markRequesting();
    transition('INITIALIZING');
    const stream = await startCameraStream();
    if (stream) {
      markGranted();
      setPermissionStatus('READY');
    } else {
      transition('ERROR');
    }
  }, [cancelSpeech, clearTimers, markGranted, markRequesting, setPermissionStatus, startCameraStream, transition]);

  const stopCamera = useCallback(() => {
    sessionRef.current += 1;
    clearTimers();
    cancelSpeech();
    stopLandmarker();
    stopCameraStream();
    segmenterRef.current.reset();
    autoSpokenSegmentsRef.current.clear();
    setVisibleResult(null);
    setDetailMessage('');
    setAudioMessage('');
    setPermissionStatus('STOPPED');
    transition('CAMERA_OFF');
  }, [cancelSpeech, clearTimers, setPermissionStatus, stopCameraStream, stopLandmarker, transition]);

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
    clearTimers();
    cancelSpeech();
    stopLandmarker();
    segmenterRef.current.reset();
    autoSpokenSegmentsRef.current.clear();
    setVisibleResult(null);
    setDetailMessage('');
    setAudioMessage('');
    setPermissionStatus('STOPPED');
    transition('CAMERA_OFF');
  }, [cameraStream, cancelSpeech, clearTimers, setPermissionStatus, stopLandmarker, transition]);

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
      clearTimers();
      cancelSpeech();
    },
    [cancelSpeech, clearTimers],
  );

  const cameraActive = Boolean(cameraStream);
  const repeatDisabled = !visibleResult || visibleResult.unknown || flowState === 'SPEAKING';

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
            Activez la caméra, puis signez naturellement. La détection, la reconnaissance et la
            lecture du résultat sont automatiques.
          </p>
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
                  {flowState === 'DISPLAYING' && visibleResult?.unknown
                    ? 'Signe non reconnu'
                    : FLOW_LABELS[flowState]}
                </p>
              </div>
              {detailMessage && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{detailMessage}</p>}

              {visibleResult && (
                <div className="mt-5 border-t border-slate-200 pt-5 text-center dark:border-slate-700">
                  <p className="text-sm font-medium text-slate-500">
                    {visibleResult.unknown ? 'Signe non reconnu' : 'Signe reconnu'}
                  </p>
                  <p
                    className="mt-2 text-5xl font-bold leading-tight text-cedar dark:text-teal-300 sm:text-6xl"
                    lang="ar"
                    dir="rtl"
                    aria-live="assertive"
                    data-testid="arabic-result"
                  >
                    {visibleResult.labelAr}
                  </p>
                  {audioMessage && <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">{audioMessage}</p>}
                </div>
              )}
            </section>

            <div className="flex flex-wrap gap-3">
              {visibleResult && !visibleResult.unknown && (
                <Button
                  variant="secondary"
                  disabled={repeatDisabled}
                  onClick={() => void speakResult(visibleResult, false)}
                >
                  <Volume2 className="mr-2 inline h-5 w-5" aria-hidden="true" />
                  Répéter l’audio
                </Button>
              )}
              <Button variant="ghost" onClick={stopCamera}>
                <CameraOff className="mr-2 inline h-5 w-5" aria-hidden="true" />
                Éteindre la caméra
              </Button>
            </div>
          </div>
        )}

        <audio ref={audioRef} className="hidden" preload="none" aria-hidden="true" />
      </main>
    </div>
  );
}
