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
import { useCameraDevices } from '../hooks/useCameraDevices';
import { useCameraPermission } from '../hooks/useCameraPermission';
import { useCameraStream } from '../hooks/useCameraStream';
import { useHolisticLandmarker } from '../hooks/useHolisticLandmarker';
import { useLandmarkRecorder } from '../hooks/useLandmarkRecorder';
import { useRecognitionCapture } from '../hooks/useRecognitionCapture';
import { useRecognitionSubmission } from '../hooks/useRecognitionSubmission';
import { setPreferredCameraDeviceId } from '../services/camera.service';
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

  return (
    <section className="mx-auto max-w-6xl px-4 py-6 pb-[calc(env(safe-area-inset-bottom)+2rem)]">
      <div className="mb-5">
        <h1 className="text-3xl font-bold">Reconnaissance camera</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Capture manuelle de landmarks. Le modele de reconnaissance reste simule.
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
            canCapture={canCapture}
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
          <CaptureProgress phase={recorder.phase} frameCount={recorder.frameCount} />
          <PredictionPanel result={submission.data ?? null} />
          {submission.isError && (
            <p className="rounded-md border border-coral bg-red-50 p-3 text-sm text-coral" role="alert">
              Le service n’a pas repondu. Vous pouvez reessayer.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
