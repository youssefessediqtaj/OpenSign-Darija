import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError } from '../../../shared/api/client';
import { SkipLink } from '../../../shared/ui/SkipLink';
import { DISABLED_PREVIEW_SIGNS } from '../domain/contribution-words';
import type { ContributionStage } from '../domain/contribution-state';
import { useContributionCamera } from '../hooks/useContributionCamera';
import { useContributionRecording } from '../hooks/useContributionRecording';
import {
  loadContributionConfiguration,
  submitContribution,
} from '../services/contribution-api.service';
import type {
  ContributionFormValues,
  ContributionNotice,
  ContributionReceipt,
  ContributionSign,
  ContributionStatus,
} from '../types';
import { ContributionForm } from './ContributionForm';
import { ContributionSuccess } from './ContributionSuccess';
import { ContributorCamera } from './ContributorCamera';
import { RecordedVideoPreview } from './RecordedVideoPreview';
import { RecordingControls } from './RecordingControls';
import { RecordingReadiness } from './RecordingReadiness';
import { ReferenceSignVideo } from './ReferenceSignVideo';

const DISABLED_STATUS: ContributionStatus = {
  collection_enabled: false,
  compliance_configured: false,
  public_submission_allowed: false,
  collection_available: false,
  storage_status: 'not_checked',
  message: 'La collecte des contributions n’est pas encore ouverte.',
  missing_configuration: [],
  invalid_configuration: [],
  readiness_dwell_ms: 1000,
};

const INITIAL_FORM: ContributionFormValues = {
  fullName: '',
  age: '',
  city: '',
  signKey: 'salam',
  consentAccepted: false,
};

function contributionErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return 'La contribution n’a pas pu être envoyée. Réessayez plus tard.';
}

export function ContributionPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [status, setStatus] = useState<ContributionStatus>(DISABLED_STATUS);
  const [signs, setSigns] = useState<ContributionSign[]>(DISABLED_PREVIEW_SIGNS);
  const [notice, setNotice] = useState<ContributionNotice | null>(null);
  const [values, setValues] = useState<ContributionFormValues>(INITIAL_FORM);
  const [receipt, setReceipt] = useState<ContributionReceipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void loadContributionConfiguration(controller.signal)
      .then((configuration) => {
        setStatus(configuration.status);
        setSigns(configuration.signs);
        setNotice(configuration.notice);
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setPageError(
          error instanceof Error
            ? error.message
            : 'La configuration des contributions est indisponible.',
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  const selectedSign =
    signs.find((sign) => sign.key === values.signKey) ?? DISABLED_PREVIEW_SIGNS[0];
  const age = Number(values.age);
  const adult = values.age !== '' && Number.isFinite(age) && age >= 18;
  const formComplete =
    values.fullName.trim().length >= 2 &&
    adult &&
    values.city.trim().length >= 2 &&
    values.consentAccepted &&
    Boolean(notice?.notice_version) &&
    selectedSign.active;
  const collectionOpen =
    status.collection_available &&
    status.public_submission_allowed &&
    selectedSign.reference_video_approved;
  const canActivateCamera = collectionOpen && formComplete && !uploading;

  const camera = useContributionCamera(
    videoRef,
    canActivateCamera,
    status.readiness_dwell_ms,
  );
  const recording = useContributionRecording(selectedSign.expected_max_duration_seconds);

  useEffect(() => {
    if (canActivateCamera) return;
    if (camera.cameraActive) camera.stop();
    if (recording.preview || recording.isRecording) {
      recording.stop();
      recording.discard();
    }
  }, [canActivateCamera]); // eslint-disable-line react-hooks/exhaustive-deps

  const stage: ContributionStage = useMemo(() => {
    if (receipt) return 'SUCCESS';
    if (uploading) return 'UPLOADING';
    if (recording.preview) return 'PREVIEW';
    if (recording.isRecording) return 'RECORDING';
    if (camera.readiness.dwellReady) return 'RECORDING_ENABLED';
    if (camera.readiness.rawReady) return 'READINESS_DWELL';
    if (camera.detectorStatus === 'ready') return 'DETECTOR_READY';
    if (camera.cameraActive) return 'CAMERA_ACTIVATION';
    return 'FORM';
  }, [
    camera.cameraActive,
    camera.detectorStatus,
    camera.readiness.dwellReady,
    camera.readiness.rawReady,
    receipt,
    recording.isRecording,
    recording.preview,
    uploading,
  ]);

  const changeSign = useCallback(
    (signKey: ContributionFormValues['signKey']) => {
      if (recording.isRecording) recording.stop();
      recording.discard();
      setValues((current) => ({ ...current, signKey }));
    },
    [recording],
  );

  const startRecording = () => {
    if (!camera.stream || !camera.readiness.dwellReady || !formComplete) return;
    setPageError(null);
    recording.start(camera.stream);
  };

  const retake = () => {
    recording.discard();
    setPageError(null);
  };

  const save = async () => {
    if (
      !recording.preview ||
      !notice ||
      !collectionOpen ||
      !formComplete ||
      uploading
    ) {
      return;
    }
    if (recording.preview.durationSeconds < selectedSign.expected_min_duration_seconds) {
      setPageError(
        `La vidéo doit durer au moins ${selectedSign.expected_min_duration_seconds} secondes.`,
      );
      return;
    }
    setUploading(true);
    setPageError(null);
    try {
      const nextReceipt = await submitContribution(
        values,
        notice.notice_version,
        recording.preview.blob,
      );
      camera.stop();
      recording.discard();
      setReceipt(nextReceipt);
    } catch (error) {
      setPageError(contributionErrorMessage(error));
    } finally {
      setUploading(false);
    }
  };

  const recordingError = camera.error ?? recording.error ?? pageError;
  const canSubmit =
    Boolean(recording.preview) &&
    (recording.preview?.durationSeconds ?? 0) >= selectedSign.expected_min_duration_seconds &&
    formComplete &&
    collectionOpen;

  return (
    <div
      className="min-h-screen bg-mist text-ink dark:bg-slate-950 dark:text-slate-50"
      data-contribution-stage={stage}
    >
      <SkipLink />
      <header className="border-b border-slate-200 bg-white/95">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
          <span className="text-lg font-bold">OpenSigne Darija</span>
          <Link to="/app/recognition" className="font-semibold text-cedar hover:underline">
            <ArrowLeft className="mr-1 inline h-4 w-4" aria-hidden="true" />
            Reconnaissance
          </Link>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-7xl px-4 py-8 pb-16">
        <div className="mb-6 max-w-3xl">
          <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-cedar">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            Contribution volontaire et privée
          </p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Aidez-nous à améliorer OpenSigne Darija
          </h1>
          <p className="mt-3 leading-7 text-slate-700">
            Enregistrez un seul signe à partir d’une référence officielle. Chaque envoi reste en
            quarantaine privée jusqu’à une vérification humaine.
          </p>
        </div>

        <div
          className={`mb-6 rounded-xl border p-4 ${
            collectionOpen
              ? 'border-emerald-200 bg-emerald-50 text-emerald-950'
              : 'border-amber-200 bg-amber-50 text-amber-950'
          }`}
          role="status"
        >
          <p className="font-semibold">
            {loading ? 'Vérification de l’ouverture de la collecte…' : status.message}
          </p>
          {!collectionOpen && !loading && (
            <p className="mt-1 text-sm">
              Le formulaire est affiché en aperçu. La caméra, l’enregistrement et l’envoi sont
              bloqués ; aucune information personnelle n’est transmise.
            </p>
          )}
        </div>

        {receipt ? (
          <ContributionSuccess receipt={receipt} />
        ) : (
          <div className="grid items-start gap-6 md:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
            <div className="order-2 space-y-5 md:order-1">
              <ContributionForm
                values={values}
                notice={notice}
                collectionOpen={collectionOpen}
                onChange={setValues}
              />
              <ContributorCamera stream={camera.stream} videoRef={videoRef} />
              {camera.cameraActive && <RecordingReadiness readiness={camera.readiness} />}
              {recording.preview && (
                <RecordedVideoPreview
                  url={recording.preview.url}
                  durationSeconds={recording.preview.durationSeconds}
                />
              )}
              <RecordingControls
                cameraActive={camera.cameraActive}
                canActivateCamera={canActivateCamera}
                canRecord={camera.readiness.dwellReady && !uploading}
                isRecording={recording.isRecording}
                hasPreview={Boolean(recording.preview)}
                canSubmit={canSubmit}
                uploading={uploading}
                elapsedSeconds={recording.elapsedSeconds}
                onActivateCamera={() => void camera.activate()}
                onStopCamera={camera.stop}
                onRecord={startRecording}
                onStopRecording={recording.stop}
                onRetake={retake}
                onSubmit={() => void save()}
              />
              {recordingError && (
                <p className="rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-900" role="alert">
                  {recordingError}
                </p>
              )}
            </div>
            <div className="order-1 md:order-2 md:sticky md:top-4">
              <ReferenceSignVideo
                signs={signs}
                selected={selectedSign}
                disabled={!collectionOpen || recording.isRecording || uploading}
                onSelect={changeSign}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
