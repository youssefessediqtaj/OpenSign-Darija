import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { CameraPermissionPanel } from './CameraPermissionPanel';
import { CameraControls } from './CameraControls';
import { CameraPreview } from './CameraPreview';
import { CameraSelector } from './CameraSelector';
import { CameraStatus } from './CameraStatus';
import { CaptureCountdown } from './CaptureCountdown';
import { CaptureProgress } from './CaptureProgress';
import { FramingGuide } from './FramingGuide';
import { LandmarkCanvas } from './LandmarkCanvas';
import { LightingIndicator } from './LightingIndicator';
import { PredictionPanel } from './PredictionPanel';
import { RecognitionInstructions } from './RecognitionInstructions';
import { FingerspellingPanel } from '../../fingerspelling/components/FingerspellingPanel';
import { useCameraDevices } from '../hooks/useCameraDevices';
import { useCameraPermission } from '../hooks/useCameraPermission';
import { useCameraStream } from '../hooks/useCameraStream';
import { useHolisticLandmarker } from '../hooks/useHolisticLandmarker';
import { useLandmarkRecorder } from '../hooks/useLandmarkRecorder';
import { useRecognitionCapture } from '../hooks/useRecognitionCapture';
import { useRecognitionSubmission } from '../hooks/useRecognitionSubmission';
import { setPreferredCameraDeviceId } from '../services/camera.service';
import { FEATURE_SCHEMA_VERSION, compactFrame } from '../services/landmark-normalizer.service';
import { landmarkRecognitionApi } from '../services/recognition-api.service';
import { useRecognitionStore } from '../stores/recognition.store';
import type { FramingEvaluation } from '../types/framing.types';
import type { HolisticFrame } from '../types/landmark.types';
import { evaluateFraming } from '../utils/framing-evaluator';
import { movementScore } from '../utils/sequence-statistics';

const emptyEvaluation: FramingEvaluation = {
  isReady: false,
  faceVisible: false,
  torsoVisible: false,
  leftHandVisible: false,
  rightHandVisible: false,
  shouldersVisible: false,
  centered: false,
  distance: 'too_far',
  lighting: 'too_dark',
  stability: 'unstable',
  warnings: ['FACE_MISSING', 'TORSO_MISSING', 'HANDS_MISSING'],
};

export function RecognitionWorkspace() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const recentFramesRef = useRef<HolisticFrame[]>([]);
  const lastUiUpdateRef = useRef(0);
  const [latestFrame, setLatestFrame] = useState<HolisticFrame | null>(null);
  const [evaluation, setEvaluation] = useState<FramingEvaluation>(emptyEvaluation);
  const [mode, setMode] = useState<'word' | 'alphabet'>('word');
  const [alphabetResult, setAlphabetResult] = useState<Awaited<ReturnType<typeof landmarkRecognitionApi.submitAlphabet>> | null>(null);
  const [alphabetPending, setAlphabetPending] = useState(false);
  const [alphabetError, setAlphabetError] = useState('');
  const [alphabetModelActive, setAlphabetModelActive] = useState(false);
  const { preferences, anonymousSessionId, updatePreferences } = useRecognitionStore();
  const permission = useCameraPermission();
  const { devices } = useCameraDevices(Boolean(videoRef.current) || permission.status === 'READY');
  const submission = useRecognitionSubmission();
  const recorder = useLandmarkRecorder(anonymousSessionId);
  const startRecorder = recorder.start;
  const startRecording = useCallback(() => startRecorder(), [startRecorder]);

  const camera = useCameraStream(
    preferences.preferredDeviceId,
    preferences.cameraQuality,
    preferences.performanceMode,
    permission.markError,
  );

  const handleFrame = useCallback(
    (frame: HolisticFrame) => {
      recentFramesRef.current = [...recentFramesRef.current.slice(-8), frame];
      recorder.addFrame(frame);
      if (performance.now() - lastUiUpdateRef.current > 150) {
        lastUiUpdateRef.current = performance.now();
        setLatestFrame(frame);
        setEvaluation(evaluateFraming(frame, movementScore(recentFramesRef.current)));
      }
    },
    [recorder],
  );

  const landmarker = useHolisticLandmarker(
    videoRef,
    Boolean(camera.stream),
    handleFrame,
    preferences.performanceMode,
  );
  const startLandmarker = landmarker.start;

  const isCameraActive = Boolean(camera.stream);
  const canCapture = evaluation.isReady && isCameraActive && recorder.phase !== 'capturing';
  const isSubmitting = submission.isPending || recorder.phase === 'submitting';
  const countdown = useRecognitionCapture(startRecording);

  const startCamera = useCallback(async () => {
    permission.markRequesting();
    const stream = await camera.start();
    if (stream) {
      permission.markGranted();
      permission.setStatus('READY');
    }
  }, [camera, permission]);

  useEffect(() => {
    if (!camera.stream) return;
    void startLandmarker();
  }, [camera.stream, startLandmarker]);

  const stopCamera = useCallback(() => {
    landmarker.stop();
    camera.stop();
    recorder.cancel();
    permission.setStatus('STOPPED');
  }, [camera, landmarker, permission, recorder]);

  const finishCapture = useCallback(async () => {
    const payload = recorder.finish();
    if (!payload) return;
    try {
      await submission.mutateAsync(payload);
      recorder.markComplete();
    } catch {
      recorder.markError('Le backend est indisponible. Reessayez sans fermer la camera.');
    }
  }, [recorder, submission]);

  const engineStatus = useMemo(() => {
    if (landmarker.status === 'loading') return 'Chargement du moteur de detection...';
    if (landmarker.status === 'fallback') return 'Mode test sans MediaPipe';
    if (landmarker.status === 'ready') return 'MediaPipe pret';
    if (landmarker.status === 'error') return 'Erreur MediaPipe';
    return 'En attente';
  }, [landmarker.status]);

  useEffect(() => {
    void landmarkRecognitionApi
      .activeModel(mode === 'alphabet' ? 'ALPHABET_STATIC' : 'WORD_ISOLATED')
      .then((model) => {
        if (mode === 'alphabet') setAlphabetModelActive(model.is_active);
      })
      .catch(() => {
        if (mode === 'alphabet') setAlphabetModelActive(false);
      });
  }, [mode]);

  const recognizeAlphabet = useCallback(async () => {
    if (!latestFrame) {
      setAlphabetError('Activez la caméra et gardez une main visible.');
      return;
    }
    const compact = compactFrame(latestFrame, 0);
    if (!compact) {
      setAlphabetError('Landmarks insuffisants pour analyser la lettre.');
      return;
    }
    setAlphabetPending(true);
    setAlphabetError('');
    try {
      const result = await landmarkRecognitionApi.submitAlphabet({
        sequence_id: crypto.randomUUID(),
        captured_at: new Date().toISOString(),
        feature_schema_version: FEATURE_SCHEMA_VERSION,
        hand: latestFrame.metadata.rightHandDetected ? 'right' : latestFrame.metadata.leftHandDetected ? 'left' : 'unknown',
        features: compact.features,
        presence_mask: compact.presence_mask,
        stability_frames: recentFramesRef.current.length,
        anonymous_session_id: anonymousSessionId,
      });
      setAlphabetResult(result);
    } catch {
      setAlphabetError('Le modèle alphabet est indisponible.');
    } finally {
      setAlphabetPending(false);
    }
  }, [anonymousSessionId, latestFrame]);

  return (
    <section className="mx-auto max-w-6xl px-4 py-6 pb-[calc(env(safe-area-inset-bottom)+2rem)]">
      <div className="mb-5">
        <h1 className="text-3xl font-bold">Reconnaissance camera</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Reconnaissance expérimentale d’un vocabulaire limité. OpenSign Darija peut se tromper. Vérifiez toujours le résultat avant de l’utiliser.
        </p>
      </div>
      <div className="mb-5 rounded-md border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900" role="tablist" aria-label="Mode de reconnaissance">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'word'}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${mode === 'word' ? 'bg-cedar text-white' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}`}
          onClick={() => setMode('word')}
        >
          Reconnaître un signe
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'alphabet'}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${mode === 'alphabet' ? 'bg-cedar text-white' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}`}
          onClick={() => setMode('alphabet')}
        >
          Épeler un mot
        </button>
        <p className="px-2 pb-1 pt-2 text-sm text-slate-600 dark:text-slate-300">
          {mode === 'word'
            ? 'Reconnaître un signe utilise les mouvements des mains, du visage et du corps.'
            : 'Épeler un mot reconnaît les lettres une par une et ne remplace pas la reconnaissance de signes.'}
        </p>
      </div>
      <RecognitionInstructions />
      <div className="mt-5 grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-4">
          {!isCameraActive && (
            <CameraPermissionPanel
              onEnable={startCamera}
              errorMessage={permission.errorMessage}
              isRequesting={permission.status === 'REQUESTING_PERMISSION'}
            />
          )}
          <CameraPreview
            stream={camera.stream}
            videoRef={videoRef}
            isMirrored={preferences.preferredDeviceId === null}
          >
            <LandmarkCanvas frame={latestFrame} enabled={preferences.showLandmarks} />
            <CaptureCountdown value={countdown.countdown} />
          </CameraPreview>
          <div className="grid gap-3 md:grid-cols-2">
            <CameraSelector
              devices={devices}
              value={preferences.preferredDeviceId}
              disabled={recorder.phase === 'capturing' || isSubmitting}
              onChange={(deviceId) => {
                setPreferredCameraDeviceId(deviceId);
                updatePreferences({ preferredDeviceId: deviceId });
              }}
            />
            <CameraStatus status={permission.status} engineStatus={engineStatus} />
          </div>
          <CameraControls
            canCapture={mode === 'word' && canCapture}
            isCameraActive={isCameraActive}
            isCapturing={recorder.phase === 'capturing'}
            isSubmitting={isSubmitting}
            onStartCamera={startCamera}
            onStopCamera={stopCamera}
            onStartCapture={countdown.beginCountdown}
            onFinishCapture={finishCapture}
            onCancelCapture={() => {
              countdown.cancelCountdown();
              recorder.cancel();
            }}
            showLandmarks={preferences.showLandmarks}
            onToggleLandmarks={() => updatePreferences({ showLandmarks: !preferences.showLandmarks })}
          />
          {recorder.validationErrors.length > 0 && (
            <div className="rounded-md border border-coral bg-red-50 p-3 text-sm text-coral" role="alert">
              {recorder.validationErrors.join(' ')}
            </div>
          )}
        </div>
        <div className="space-y-4">
          <FramingGuide evaluation={evaluation} />
          <LightingIndicator lighting={evaluation.lighting} />
          {mode === 'word' ? (
            <>
              <CaptureProgress phase={recorder.phase} frameCount={recorder.frameCount} />
              <PredictionPanel result={submission.data ?? null} />
            </>
          ) : (
            <FingerspellingPanel
              result={alphabetResult}
              isModelAvailable={alphabetModelActive}
              isPending={alphabetPending}
              onRecognize={recognizeAlphabet}
            />
          )}
          {alphabetError && mode === 'alphabet' && (
            <p className="rounded-md border border-coral bg-red-50 p-3 text-sm text-coral" role="alert">
              {alphabetError}
            </p>
          )}
          {submission.isError && mode === 'word' && (
            <p className="rounded-md border border-coral bg-red-50 p-3 text-sm text-coral" role="alert">
              Le moteur de reconnaissance est temporairement indisponible. Vous pouvez réessayer ou consulter les signes supportés.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
